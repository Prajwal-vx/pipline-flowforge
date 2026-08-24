from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import WorkflowExecution, Workflow
from app.core.security import get_current_user
from app.services.broker import redis
from app.core.config import settings
from jose import JWTError, jwt
import json

router = APIRouter(prefix="/api/executions", tags=["executions"])

@router.get("/{execution_id}")
async def get_execution(execution_id: str, user=Depends(get_current_user)):
    async with SessionLocal() as db:
        result = await db.execute(select(WorkflowExecution, Workflow).join(Workflow, Workflow.id == WorkflowExecution.workflow_id).where(WorkflowExecution.id == execution_id, Workflow.owner_id == user.id))
        pair = result.first()
        if not pair: raise HTTPException(404, "Execution not found")
        execution, _ = pair
        return {"id": execution.id, "workflow_id": execution.workflow_id, "status": execution.status, "input_json": execution.input_json, "output_json": execution.output_json, "error": execution.error, "duration_ms": execution.duration_ms}

@router.websocket("/ws/{execution_id}")
async def execution_socket(websocket: WebSocket, execution_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError
    except JWTError:
        await websocket.close(code=1008)
        return
    async with SessionLocal() as db:
        result = await db.execute(select(WorkflowExecution.id).join(Workflow, Workflow.id == WorkflowExecution.workflow_id).where(WorkflowExecution.id == execution_id, Workflow.owner_id == user_id))
        if result.scalar_one_or_none() is None:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"execution:{execution_id}")
    try:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
                if data.get("type") in {"workflow_completed", "workflow_failed"}:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"execution:{execution_id}")
        await pubsub.close()
