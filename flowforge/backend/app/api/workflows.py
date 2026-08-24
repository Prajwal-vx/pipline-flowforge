import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import User, Workflow, WorkflowExecution
from app.schemas.workflow import WorkflowPayload, WorkflowResponse, ExecutionResponse
from app.core.security import get_current_user
from app.engine.executor import execute_workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.owner_id == user.id).order_by(Workflow.updated_at.desc()))
    return list(result.scalars())

@router.post("", response_model=WorkflowResponse)
async def create_workflow(payload: WorkflowPayload, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = Workflow(owner_id=user.id, name=payload.name, description=payload.description, enabled=payload.enabled, nodes_json=payload.nodes, edges_json=payload.edges)
    db.add(wf); await db.commit(); await db.refresh(wf)
    return wf

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf or wf.owner_id != user.id: raise HTTPException(404, "Workflow not found")
    return wf

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, payload: WorkflowPayload, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf or wf.owner_id != user.id: raise HTTPException(404, "Workflow not found")
    wf.name = payload.name; wf.description = payload.description; wf.enabled = payload.enabled; wf.nodes_json = payload.nodes; wf.edges_json = payload.edges
    await db.commit(); await db.refresh(wf)
    return wf

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf or wf.owner_id != user.id: raise HTTPException(404, "Workflow not found")
    await db.delete(wf); await db.commit(); return {"ok": True}

@router.post("/{workflow_id}/run", response_model=ExecutionResponse)
async def run_workflow(workflow_id: str, payload: dict | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf or wf.owner_id != user.id: raise HTTPException(404, "Workflow not found")
    execution = WorkflowExecution(workflow_id=wf.id, status="queued", input_json=payload or {})
    db.add(execution); await db.commit(); await db.refresh(execution)
    asyncio.create_task(execute_workflow(execution.id))
    return execution

@router.get("/{workflow_id}/executions", response_model=list[ExecutionResponse])
async def executions(workflow_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf or wf.owner_id != user.id: raise HTTPException(404, "Workflow not found")
    result = await db.execute(select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow_id).order_by(WorkflowExecution.id.desc()).limit(50))
    return list(result.scalars())
