from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from app.core.middleware import require_role, CurrentUserContext
from app.schemas.member_schemas import MemberAdd, MemberResponse
from app.services.member_service import MemberService

router = APIRouter(prefix="/workspaces", tags=["members"])
member_service = MemberService()


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: str = Path(..., description="Workspace ID"),
    member_data: MemberAdd = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Add a member to a workspace (ADMIN or OWNER)."""
    
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


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Remove a member from a workspace (ADMIN or OWNER)."""
    
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
    
    return None

