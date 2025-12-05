from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.integration_schemas import ProjectListResponse
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

