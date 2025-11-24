from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from typing import Optional
from app.core.middleware import require_role, CurrentUserContext
from app.schemas.workspace_schemas import WorkspaceCreate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService
from app.db.queries import get_workspace_by_id

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
workspace_service = WorkspaceService()


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request
):
    """Create a new workspace."""
    user: CurrentUserContext = request.state.user
    
    try:
        workspace = await workspace_service.create_workspace(
            name=workspace_data.name,
            description=workspace_data.description,
            created_by=user.user_id,
            creator_display_name=user.email
        )
        
        # Get full workspace with members and links
        full_workspace = await workspace_service.get_workspace(workspace["id"])
        
        return WorkspaceResponse(**full_workspace)
    except Exception as e:
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

