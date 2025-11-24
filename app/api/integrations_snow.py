from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from app.core.middleware import require_role, CurrentUserContext
from app.schemas.integration_schemas import ProjectListResponse, ProjectDetailResponse, ExternalLinkCreate, ExternalLinkResponse
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations/snow", tags=["integrations-snow"])
integration_service = IntegrationService()


@router.get("/spaces", response_model=ProjectListResponse)
async def list_snow_spaces(request: Request):
    """List ServiceNow PPM spaces."""
    user: CurrentUserContext = request.state.user
    
    try:
        spaces = await integration_service.list_snow_spaces(user.user_id)
        return ProjectListResponse(projects=spaces)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch ServiceNow spaces: {str(e)}"
            }
        )


@router.get("/spaces/{space_id}", response_model=ProjectDetailResponse)
async def get_snow_space(
    space_id: str = Path(..., description="ServiceNow space ID"),
    request: Request = None
):
    """Get ServiceNow PPM space details."""
    user: CurrentUserContext = request.state.user
    
    try:
        space = await integration_service.get_snow_space(space_id, user.user_id)
        return ProjectDetailResponse(data=space)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch ServiceNow space: {str(e)}"
            }
        )


@router.post("/workspaces/{workspace_id}/links/snow", response_model=ExternalLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_snow_space(
    workspace_id: str = Path(..., description="Workspace ID"),
    link_data: ExternalLinkCreate = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Link a ServiceNow PPM space to a workspace."""
    
    try:
        link = await integration_service.link_external_entity(
            workspace_id=workspace_id,
            provider="SNOW",
            external_id=link_data.external_id,
            display_name=link_data.display_name,
            actor_id=user.user_id
        )
        return ExternalLinkResponse(**link)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_QUERY_FAILED",
                "message": f"Failed to link ServiceNow space: {str(e)}"
            }
        )

