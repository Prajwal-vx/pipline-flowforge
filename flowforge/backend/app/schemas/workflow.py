from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class WorkflowPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    enabled: bool = False
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)

class WorkflowResponse(WorkflowPayload):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    nodes: list[dict] = Field(default_factory=list, validation_alias="nodes_json", serialization_alias="nodes")
    edges: list[dict] = Field(default_factory=list, validation_alias="edges_json", serialization_alias="edges")
    created_at: datetime
    updated_at: datetime

class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    input_json: dict
    output_json: dict
    error: str
    duration_ms: int
    started_at: datetime | None
    finished_at: datetime | None
