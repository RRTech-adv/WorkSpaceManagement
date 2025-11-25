from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from app.core.middleware import require_role, CurrentUserContext
from app.core.token_service import TokenService
from app.schemas.member_schemas import MemberAdd, MemberResponse, MemberRoleUpdate
from app.services.member_service import MemberService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["members"])
member_service = MemberService()
token_service = TokenService()


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: str = Path(..., description="Workspace ID"),
    member_data: MemberAdd = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Add a member to a workspace (ADMIN or OWNER). Returns refreshed PMA token if added user == current user."""
    
    # In production, resolve user_email to user_id via Azure AD Graph API
    # For now, using email as user_id
    user_id = member_data.user_email
    
    if member_data.role not in ["ADMIN", "MEMBER", "VIEWER"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ROLE",
                "message": "Role must be ADMIN, MEMBER, or VIEWER"
            }
        )
    
    try:
        member = await member_service.add_member(
            workspace_id=workspace_id,
            user_id=user_id,
            display_name=member_data.user_email,
            role=member_data.role,
            actor_id=user.user_id
        )
        
        # If added user is the current user, refresh PMA token
        if user_id == user.user_id:
            azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
            current_pma_token = request.headers.get("X-PMA-Token", "")
            
            if azure_token and current_pma_token:
                try:
                    refreshed = await token_service.refresh_pma_token(azure_token, current_pma_token)
                    if refreshed:
                        member["pma_token"] = refreshed["pma_token"]
                        logger.info(f"Refreshed PMA token for user {user.user_id} after being added to workspace")
                except Exception as e:
                    logger.warning(f"Failed to refresh PMA token after adding member: {e}")
        
        return MemberResponse(**member)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to add member: {str(e)}"
            }
        )


@router.get("/{workspace_id}/members", response_model=list)
async def list_members(
    workspace_id: str = Path(..., description="Workspace ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("VIEWER"))
):
    """List all members of a workspace."""
    try:
        members = await member_service.list_members(workspace_id)
        return [MemberResponse(**m) for m in members]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to list members: {str(e)}"
            }
        )


@router.patch("/{workspace_id}/members/{member_id}/role", response_model=MemberResponse)
async def change_member_role(
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    role_data: MemberRoleUpdate = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Change a member's role in a workspace (ADMIN or OWNER). Returns refreshed PMA token if changed user == current user."""
    
    if role_data.role not in ["OWNER", "ADMIN", "MEMBER", "VIEWER"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ROLE",
                "message": "Role must be OWNER, ADMIN, MEMBER, or VIEWER"
            }
        )
    
    try:
        member = await member_service.update_member_role(
            workspace_id=workspace_id,
            member_id=member_id,
            new_role=role_data.role,
            actor_id=user.user_id
        )
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "MEMBER_NOT_FOUND",
                    "message": "Member not found"
                }
            )
        
        # If the user whose role changed is the current user, refresh PMA token
        if member["user_id"] == user.user_id:
            azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
            current_pma_token = request.headers.get("X-PMA-Token", "")
            
            if azure_token and current_pma_token:
                try:
                    refreshed = await token_service.refresh_pma_token(azure_token, current_pma_token)
                    if refreshed:
                        member["pma_token"] = refreshed["pma_token"]
                        logger.info(f"Refreshed PMA token for user {member['user_id']} after role change")
                except Exception as e:
                    logger.warning(f"Failed to refresh PMA token after role change: {e}")
        
        return MemberResponse(**member)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to update member role: {str(e)}"
            }
        )


@router.delete("/{workspace_id}/members/{member_id}", response_model=MemberResponse)
async def remove_member(
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Remove a member from a workspace (ADMIN or OWNER). Returns refreshed PMA token if removed user == current user."""
    
    result = await member_service.remove_member(
        workspace_id=workspace_id,
        member_id=member_id,
        actor_id=user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "MEMBER_NOT_FOUND",
                "message": "Member not found"
            }
        )
    
    # If removed user is the current user, refresh PMA token
    if result["user_id"] == user.user_id:
        azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        current_pma_token = request.headers.get("X-PMA-Token", "")
        
        if azure_token and current_pma_token:
            try:
                refreshed = await token_service.refresh_pma_token(azure_token, current_pma_token)
                if refreshed:
                    result["pma_token"] = refreshed["pma_token"]
                    logger.info(f"Refreshed PMA token for user {user.user_id} after being removed from workspace")
            except Exception as e:
                logger.warning(f"Failed to refresh PMA token after removing member: {e}")
    
    return MemberResponse(**result)

