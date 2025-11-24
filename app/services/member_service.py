from typing import Optional
import uuid
from app.db.connection import get_db_pool
from app.db.queries import add_workspace_member, delete_workspace_member, get_workspace_members
from app.services.audit_service import AuditService


class MemberService:
    """Service for workspace member operations."""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    async def add_member(
        self,
        workspace_id: str,
        user_id: str,
        display_name: str,
        role: str,
        actor_id: str
    ) -> dict:
        """Add a member to a workspace."""
        pool = await get_db_pool()
        member_id = str(uuid.uuid4())
        
        member = await add_workspace_member(
            pool,
            member_id,
            workspace_id,
            user_id,
            display_name,
            role
        )
        
        await self.audit_service.log_action(
            workspace_id,
            "MEMBER_ADDED",
            actor_id,
            {"member_id": user_id, "role": role}
        )
        
        return member
    
    async def remove_member(
        self,
        workspace_id: str,
        member_id: str,
        actor_id: str
    ) -> bool:
        """Remove a member from a workspace."""
        pool = await get_db_pool()
        result = await delete_workspace_member(pool, member_id, workspace_id)
        
        if result:
            await self.audit_service.log_action(
                workspace_id,
                "MEMBER_REMOVED",
                actor_id,
                {"member_id": member_id}
            )
        
        return result
    
    async def list_members(self, workspace_id: str) -> list:
        """List all members of a workspace."""
        pool = await get_db_pool()
        return await get_workspace_members(pool, workspace_id)

