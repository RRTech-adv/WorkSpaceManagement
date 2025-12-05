from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from typing import Optional
from app.core.middleware import require_role, CurrentUserContext
from app.core.token_service import TokenService
from app.schemas.workspace_schemas import WorkspaceCreate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService
from app.db.queries import get_workspace_by_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
workspace_service = WorkspaceService()
token_service = TokenService()


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request
):
    """
    Create a new workspace. Returns refreshed PMA token with OWNER role.
    
    Note: The user's current PMA token may not have this workspace yet (since it was just created).
    This endpoint always returns a refreshed PMA token that includes the new workspace with OWNER role.
    The client should update their stored token with the returned pma_token.
    """
    user: CurrentUserContext = request.state.user
    
    try:
        # Create workspace (this also adds user as OWNER in database)
        workspace = await workspace_service.create_workspace(
            name=workspace_data.name,
            description=workspace_data.description,
            created_by=user.user_id,
            creator_display_name=user.email,
            provider=workspace_data.provider,
            provider_project=workspace_data.provider_project
        )
        
        workspace_id = workspace["id"]
        logger.info(f"Workspace {workspace_id} created by user {user.user_id}. User added as OWNER in database.")
        
        # Get full workspace with members and links
        full_workspace = await workspace_service.get_workspace(workspace_id)
        
        # IMPORTANT: Refresh PMA token to include the newly created workspace
        # The user's current token doesn't have this workspace yet, so we MUST refresh it
        azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        current_pma_token = request.headers.get("X-PMA-Token", "")
        
        if azure_token and current_pma_token:
            try:
                # Refresh token - this fetches fresh roles from database (now includes new workspace)
                refreshed = await token_service.refresh_pma_token(azure_token, current_pma_token)
                if refreshed:
                    full_workspace["pma_token"] = refreshed["pma_token"]
                    # Verify the new workspace is in the refreshed roles
                    new_roles = refreshed.get("roles", {})
                    if workspace_id in new_roles:
                        logger.info(f"Refreshed PMA token for user {user.user_id} after workspace creation. New workspace {workspace_id} included with role: {new_roles[workspace_id]}")
                    else:
                        logger.warning(f"Workspace {workspace_id} not found in refreshed roles. This should not happen.")
            except Exception as e:
                logger.error(f"Failed to refresh PMA token after workspace creation: {e}. User should manually refresh token.")
                # Don't fail the request, but log the error
                # The middleware will handle role lookup from database if needed
        else:
            logger.warning(f"Missing tokens for token refresh. Azure: {bool(azure_token)}, PMA: {bool(current_pma_token)}")
        
        return WorkspaceResponse(**full_workspace)
    except Exception as e:
        logger.error(f"Error creating workspace: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to create workspace: {str(e)}"
            }
        )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str = Path(..., description="Workspace ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("VIEWER"))
):
    """Get workspace details."""
    workspace = await workspace_service.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "WORKSPACE_NOT_FOUND",
                "message": "Workspace not found"
            }
        )
    
    return WorkspaceResponse(**workspace)


@router.get("", response_model=list)
async def list_workspaces(
    request: Request,
    user_id: Optional[str] = None
):
    """List workspaces for the current user."""
    user: CurrentUserContext = request.state.user
    
    # Use user_id from token if not provided
    target_user_id = user_id or user.user_id
    
    try:
        workspaces = await workspace_service.list_workspaces(target_user_id)
        return [WorkspaceResponse(**w) for w in workspaces]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to list workspaces: {str(e)}"
            }
        )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str = Path(..., description="Workspace ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("OWNER"))
):
    """Soft delete a workspace (OWNER only)."""
    
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "WORKSPACE_NOT_FOUND",
                "message": "Workspace not found"
            }
        )
    
    result = await workspace_service.delete_workspace(workspace_id, user.user_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": "Failed to delete workspace"
            }
        )
    
    return None

