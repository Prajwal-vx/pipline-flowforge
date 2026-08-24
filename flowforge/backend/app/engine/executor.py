import asyncio
import time
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Workflow, WorkflowExecution, NodeExecution
from app.nodes.base import NODE_REGISTRY, NodeContext
from app.services.broker import publish


def now():
    return datetime.now(timezone.utc)

class WorkflowExecutor:
    def __init__(self, workflow: Workflow, execution: WorkflowExecution):
        self.workflow = workflow
        self.execution = execution
        self.nodes = workflow.nodes_json or []
        self.edges = workflow.edges_json or []
        self.outputs = {}

    def build_graph(self):
        outgoing = defaultdict(list)
        incoming = {node["id"]: 0 for node in self.nodes}
        for edge in self.edges:
            if edge.get("source") not in incoming or edge.get("target") not in incoming:
                raise ValueError("Workflow edge references an unknown node")
            outgoing[edge["source"]].append(edge["target"])
            incoming[edge["target"]] += 1
        return outgoing, incoming

    async def _record(self, execution: WorkflowExecution, node: dict, status: str, input_data: dict, output: dict, error: str, duration: int):
        async with SessionLocal() as db:
            result = await db.execute(select(NodeExecution).where(NodeExecution.execution_id == execution.id, NodeExecution.node_id == node["id"]))
            rec = result.scalar_one_or_none()
            if not rec:
                rec = NodeExecution(execution_id=execution.id, node_id=node["id"], node_type=node["data"].get("type", "unknown"))
                db.add(rec)
            rec.status = status
            rec.input_json = input_data or {}
            rec.output_json = output or {}
            rec.error = error
            rec.duration_ms = duration
            if status == "running": rec.started_at = now()
            if status in {"success", "failed"}: rec.finished_at = now()
            await db.commit()
        await publish(execution.id, {"type": "node_status", "node_id": node["id"], "status": status, "error": error})

    async def run_node(self, node: dict, current_data: dict):
        node_cfg = node.get("data", {})
        node_type = node_cfg.get("type", "transform")
        cls = NODE_REGISTRY.get(node_type)
        if not cls:
            raise ValueError(f"Unsupported node type: {node_type}")
        retries = max(0, min(int(node_cfg.get("retries", 2)), 5))
        for attempt in range(retries + 1):
            started = time.perf_counter()
            try:
                await self._record(self.execution, node, "running", current_data, {}, "", 0)
                ctx = NodeContext(self.execution.id, node["id"], {**current_data, "input": self.execution.input_json})
                output = await cls().run(node_cfg.get("config", {}), ctx)
                elapsed = int((time.perf_counter() - started) * 1000)
                await self._record(self.execution, node, "success", current_data, output, "", elapsed)
                return output
            except Exception as exc:
                elapsed = int((time.perf_counter() - started) * 1000)
                if attempt < retries:
                    await publish(self.execution.id, {"type": "retry", "node_id": node["id"], "attempt": attempt + 1, "error": str(exc)})
                    await asyncio.sleep(min(2 ** attempt, 8))
                    continue
                await self._record(self.execution, node, "failed", current_data, {}, str(exc), elapsed)
                raise

    async def run(self):
        outgoing, incoming = self.build_graph()
        node_map = {node["id"]: node for node in self.nodes}
        ready = [node_id for node_id, count in incoming.items() if count == 0]
        completed = set()
        data_by_node = {node_id: dict(self.execution.input_json or {}) for node_id in node_map}
        await publish(self.execution.id, {"type": "execution_started", "execution_id": self.execution.id})
        while ready:
            batch = ready[:]
            ready.clear()
            results = await asyncio.gather(*(self.run_node(node_map[node_id], data_by_node[node_id]) for node_id in batch), return_exceptions=True)
            for node_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    raise result
                completed.add(node_id)
                data_by_node[node_id] = {**data_by_node[node_id], **(result or {})}
                for target in outgoing.get(node_id, []):
                    data_by_node[target] = {**data_by_node[node_id], **(result or {})}
                    incoming[target] -= 1
                    if incoming[target] == 0:
                        ready.append(target)
        if len(completed) != len(node_map):
            # Detect cycles or disconnected nodes without dependencies.
            raise ValueError("Workflow graph could not be fully executed; check node connections")
        return data_by_node

async def execute_workflow(execution_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(WorkflowExecution).where(WorkflowExecution.id == execution_id))
        execution = result.scalar_one()
        wf_result = await db.execute(select(Workflow).where(Workflow.id == execution.workflow_id))
        workflow = wf_result.scalar_one()
        execution.status = "running"
        execution.started_at = now()
        await db.commit()
    try:
        result = await WorkflowExecutor(workflow, execution).run()
        async with SessionLocal() as db:
            rec = await db.get(WorkflowExecution, execution_id)
            rec.status = "completed"
            rec.output_json = result
            rec.finished_at = now()
            rec.duration_ms = int((rec.finished_at - rec.started_at).total_seconds() * 1000)
            await db.commit()
        await publish(execution_id, {"type": "workflow_completed", "execution_id": execution_id})
    except Exception as exc:
        async with SessionLocal() as db:
            rec = await db.get(WorkflowExecution, execution_id)
            rec.status = "failed"
            rec.error = str(exc)
            rec.finished_at = now()
            rec.duration_ms = int((rec.finished_at - rec.started_at).total_seconds() * 1000)
            await db.commit()
        await publish(execution_id, {"type": "workflow_failed", "execution_id": execution_id, "error": str(exc)})
