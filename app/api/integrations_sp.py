from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from app.core.middleware import require_role, CurrentUserContext
from app.schemas.integration_schemas import ProjectListResponse, ProjectDetailResponse, ExternalLinkCreate, ExternalLinkResponse
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations/sharepoint", tags=["integrations-sharepoint"])
integration_service = IntegrationService()


@router.get("/sites", response_model=ProjectListResponse)
async def list_sharepoint_sites(request: Request):
    """List SharePoint sites."""
    user: CurrentUserContext = request.state.user
    
    try:
        sites = await integration_service.list_sharepoint_sites(user.user_id)
        return ProjectListResponse(projects=sites)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch SharePoint sites: {str(e)}"
            }
        )


@router.get("/sites/{site_id}", response_model=ProjectDetailResponse)
async def get_sharepoint_site(
    site_id: str = Path(..., description="SharePoint site ID"),
    request: Request = None
):
    """Get SharePoint site details."""
    user: CurrentUserContext = request.state.user
    
    try:
        site = await integration_service.get_sharepoint_site(site_id, user.user_id)
        return ProjectDetailResponse(data=site)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch SharePoint site: {str(e)}"
            }
        )


@router.post("/workspaces/{workspace_id}/links/sharepoint", response_model=ExternalLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_sharepoint_site(
    workspace_id: str = Path(..., description="Workspace ID"),
    link_data: ExternalLinkCreate = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Link a SharePoint site to a workspace."""
    
    try:
        link = await integration_service.link_external_entity(
            workspace_id=workspace_id,
            provider="SHAREPOINT",
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
                "message": f"Failed to link SharePoint site: {str(e)}"
            }
        )

