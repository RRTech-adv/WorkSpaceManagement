from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MemberAdd(BaseModel):
    user_email: str
    role: str  # ADMIN, MEMBER, VIEWER


class MemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    display_name: Optional[str]
    role: str
    added_at: datetime


class MemberListResponse(BaseModel):
    members: List[MemberResponse]

