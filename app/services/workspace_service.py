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
    get_workspace_integrations,
    create_workspace_integration
)
from app.db.workspace_schema import create_workspace_schema
from app.services.blob_service import BlobService
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


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
        creator_display_name: str,
        provider: Optional[str] = None,
        provider_project: Optional[str] = None
    ) -> Dict:
        """Create a new workspace with optional initial integration."""
        pool = await get_db_pool()
        workspace_id = str(uuid.uuid4())
        
        # Create blob folders
        blob_path = await self.blob_service.create_workspace_folders(workspace_id)
        
        # Create per-workspace schema
        try:
            schema_name = await create_workspace_schema(workspace_id)
            logger.info(f"Created workspace schema {schema_name} for workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to create workspace schema: {e}", exc_info=True)
            raise
        
        # Create workspace (with schema name)
        workspace = await create_workspace(
            pool,
            workspace_id,
            name,
            description,
            created_by,
            blob_path,
            db_schema_name=schema_name
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
        
        # Create initial integration entry if provider and provider_project provided
        if provider and provider_project:
            try:
                integration_id = str(uuid.uuid4())
                await create_workspace_integration(
                    pool,
                    workspace_id,
                    integration_id,
                    provider=provider,
                    integration_display_name=provider_project,
                    added_by_user_id=created_by
                )
                logger.info(f"Created initial integration for workspace {workspace_id}: provider={provider}, project={provider_project}")
            except Exception as e:
                logger.error(f"Failed to create initial integration: {e}", exc_info=True)
                # Don't fail workspace creation if integration creation fails
        
        # Audit log
        await self.audit_service.log_action(
            workspace_id,
            "WORKSPACE_CREATED",
            created_by,
            {"name": name, "description": description, "provider": provider, "provider_project": provider_project}
        )
        
        return workspace
    
    async def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace by ID with members and integrations."""
        pool = await get_db_pool()
        workspace = await get_workspace_by_id(pool, workspace_id)
        
        if workspace:
            # Get members
            members = await get_workspace_members(pool, workspace_id)
            workspace["members"] = members
            
            # Get integrations from per-workspace schema
            integrations = await get_workspace_integrations(pool, workspace_id)
            workspace["external_links"] = integrations  # Keep field name for backward compatibility
        
        return workspace
    
    async def list_workspaces(self, user_id: str) -> List[Dict]:
        """List workspaces for a user with integrations."""
        pool = await get_db_pool()
        workspaces = await get_workspaces_by_user(pool, user_id)
        
        # Add integrations to each workspace
        for workspace in workspaces:
            workspace_id = workspace["id"]
            integrations = await get_workspace_integrations(pool, workspace_id)
            workspace["external_links"] = integrations  # Keep field name for backward compatibility
        
        return workspaces
    
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

