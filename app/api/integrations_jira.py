from fastapi import APIRouter, Request, HTTPException, status, Path, Depends
from app.core.middleware import require_role, CurrentUserContext
from app.schemas.integration_schemas import ProjectListResponse, ProjectDetailResponse, ExternalLinkCreate, ExternalLinkResponse
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


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_jira_project(
    project_id: str = Path(..., description="Jira project ID or key"),
    request: Request = None
):
    """Get Jira project details."""
    user: CurrentUserContext = request.state.user
    
    try:
        project = await integration_service.get_jira_project(project_id, user.user_id)
        return ProjectDetailResponse(data=project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTEGRATION_FAILURE",
                "message": f"Failed to fetch Jira project: {str(e)}"
            }
        )


@router.post("/workspaces/{workspace_id}/links/jira", response_model=ExternalLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_jira_project(
    workspace_id: str = Path(..., description="Workspace ID"),
    link_data: ExternalLinkCreate = None,
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("ADMIN"))
):
    """Link a Jira project to a workspace."""
    
    try:
        link = await integration_service.link_external_entity(
            workspace_id=workspace_id,
            provider="JIRA",
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
                "message": f"Failed to link Jira project: {str(e)}"
            }
        )

