from typing import Optional, List, Dict
import uuid
from app.db.connection import get_db_pool
from app.db.queries import (
    create_workspace,
    get_workspace_by_id,
    get_workspaces_by_user,
    soft_delete_workspace,
    add_workspace_member,
    get_workspace_members,
    get_workspace_external_links
)
from app.services.blob_service import BlobService
from app.services.audit_service import AuditService


class WorkspaceService:
    """Service for workspace operations."""
    
    def __init__(self):
        self.blob_service = BlobService()
        self.audit_service = AuditService()
    
    async def create_workspace(
        self,
        name: str,
        description: Optional[str],
        created_by: str,
        creator_display_name: str
    ) -> Dict:
        """Create a new workspace."""
        pool = await get_db_pool()
        workspace_id = str(uuid.uuid4())
        
        # Create blob folders
        blob_path = await self.blob_service.create_workspace_folders(workspace_id)
        
        # Create workspace
        workspace = await create_workspace(
            pool,
            workspace_id,
            name,
            description,
            created_by,
            blob_path
        )
        
        # Add creator as OWNER
        member_id = str(uuid.uuid4())
        await add_workspace_member(
            pool,
            member_id,
            workspace_id,
            created_by,
            creator_display_name,
            "OWNER"
        )
        
        # Audit log
        await self.audit_service.log_action(
            workspace_id,
            "WORKSPACE_CREATED",
            created_by,
            {"name": name, "description": description}
        )
        
        return workspace
    
    async def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace by ID."""
        pool = await get_db_pool()
        workspace = await get_workspace_by_id(pool, workspace_id)
        
        if workspace:
            # Get members
            members = await get_workspace_members(pool, workspace_id)
            workspace["members"] = members
            
            # Get external links
            links = await get_workspace_external_links(pool, workspace_id)
            workspace["external_links"] = links
        
        return workspace
    
    async def list_workspaces(self, user_id: str) -> List[Dict]:
        """List workspaces for a user."""
        pool = await get_db_pool()
        return await get_workspaces_by_user(pool, user_id)
    
    async def delete_workspace(self, workspace_id: str, actor_id: str) -> bool:
        """Soft delete a workspace."""
        pool = await get_db_pool()
        result = await soft_delete_workspace(pool, workspace_id)
        
        if result:
            await self.audit_service.log_action(
                workspace_id,
                "WORKSPACE_DELETED",
                actor_id,
                {}
            )
        
        return result

