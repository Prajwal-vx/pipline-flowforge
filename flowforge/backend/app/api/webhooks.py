import asyncio
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Workflow, WorkflowExecution
from app.engine.executor import execute_workflow

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/{workflow_id}")
async def trigger_workflow(workflow_id: str, request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode(errors="ignore")}
    async with SessionLocal() as db:
        wf = await db.get(Workflow, workflow_id)
        if not wf or not wf.enabled:
            raise HTTPException(404, "Workflow not found or disabled")
        execution = WorkflowExecution(workflow_id=wf.id, status="queued", input_json=payload if isinstance(payload, dict) else {"payload": payload})
        db.add(execution); await db.commit(); await db.refresh(execution)
    asyncio.create_task(execute_workflow(execution.id))
    return {"accepted": True, "execution_id": execution.id}
