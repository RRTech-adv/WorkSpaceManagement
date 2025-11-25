from typing import Optional
import uuid
from app.db.connection import get_db_pool
from app.db.queries import (
    add_workspace_member,
    delete_workspace_member,
    get_workspace_members,
    update_workspace_member_role,
    get_workspace_member_by_user_id
)
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
    
    async def update_member_role(
        self,
        workspace_id: str,
        member_id: str,
        new_role: str,
        actor_id: str
    ) -> Optional[dict]:
        """Update a member's role in a workspace."""
        pool = await get_db_pool()
        member = await update_workspace_member_role(
            pool,
            member_id,
            workspace_id,
            new_role
        )
        
        if member:
            await self.audit_service.log_action(
                workspace_id,
                "MEMBER_ROLE_UPDATED",
                actor_id,
                {"member_id": member_id, "new_role": new_role}
            )
        
        return member
    
    async def remove_member(
        self,
        workspace_id: str,
        member_id: str,
        actor_id: str
    ) -> Optional[dict]:
        """Remove a member from a workspace. Returns member info if found."""
        pool = await get_db_pool()
        # Get member info before deletion - need to query by member_id first
        from app.db.queries import _execute_query
        row = await _execute_query(
            pool,
            "SELECT id, workspace_id, user_id, display_name, role, added_at FROM WorkspaceMember WHERE id = ? AND workspace_id = ?",
            (member_id, workspace_id),
            fetch_one=True
        )
        
        if not row:
            return None
        
        member = {
            "id": str(row[0]),
            "workspace_id": str(row[1]),
            "user_id": row[2],
            "display_name": row[3],
            "role": row[4],
            "added_at": row[5]
        }
        
        result = await delete_workspace_member(pool, member_id, workspace_id)
        
        if result:
            await self.audit_service.log_action(
                workspace_id,
                "MEMBER_REMOVED",
                actor_id,
                {"member_id": member_id}
            )
            return member
        
        return None
    
    async def list_members(self, workspace_id: str) -> list:
        """List all members of a workspace."""
        pool = await get_db_pool()
        return await get_workspace_members(pool, workspace_id)

