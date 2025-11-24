from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ExternalLinkCreate(BaseModel):
    external_id: str
    display_name: str


class ExternalLinkResponse(BaseModel):
    id: str
    workspace_id: str
    provider: str
    external_id: str
    display_name: Optional[str]
    config: Optional[str]
    linked_at: str


class ProjectListItem(BaseModel):
    id: str
    name: str
    key: Optional[str] = None
    description: Optional[str] = None


class ProjectListResponse(BaseModel):
    projects: List[ProjectListItem]


class ProjectDetailResponse(BaseModel):
    data: Dict[str, Any]

