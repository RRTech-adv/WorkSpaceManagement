from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.integration_schemas import ProjectListResponse
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations/jira", tags=["integrations-jira"])
integration_service = IntegrationService()


@router.get("/projects", response_model=ProjectListResponse)
async def list_jira_projects(request: Request):
    """List Jira projects."""
    user: CurrentUserContext = request.state.user
    
    try:
        projects = await integration_service.list_jira_projects(user.user_id)
        return ProjectListResponse(projects=projects)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch Jira projects: {str(e)}"
            }
        )

