from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.integration_schemas import ProjectListResponse
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

