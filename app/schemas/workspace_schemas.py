from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    blob_path: str
    is_active: bool
    members: Optional[List[dict]] = None
    external_links: Optional[List[dict]] = None


class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]

