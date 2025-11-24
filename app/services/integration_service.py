from typing import List, Dict, Optional
import uuid
import json
import requests
import base64
from app.core.config import settings
from app.db.connection import get_db_pool
from app.db.queries import create_external_link
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for external system integrations."""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    async def list_jira_projects(self, user_id: str) -> List[Dict]:
        """List Jira projects."""
        if not settings.jira_api_token or not settings.jira_base_url:
            raise ValueError("Jira API token and base URL must be configured in .env")
        
        token = settings.jira_api_token
        jira_url = settings.jira_base_url
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{jira_url}/rest/api/3/project",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            projects = response.json()
            
            return [
                {
                    "id": p.get("id"),
                    "key": p.get("key"),
                    "name": p.get("name"),
                    "projectTypeKey": p.get("projectTypeKey")
                }
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Error fetching Jira projects: {e}")
            raise
    
    async def get_jira_project(self, project_id: str, user_id: str) -> Dict:
        """Get Jira project details."""
        if not settings.jira_api_token or not settings.jira_base_url:
            raise ValueError("Jira API token and base URL must be configured in .env")
        
        token = settings.jira_api_token
        jira_url = settings.jira_base_url
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{jira_url}/rest/api/3/project/{project_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching Jira project: {e}")
            raise
    
    async def list_ado_projects(self, user_id: str) -> List[Dict]:
        """List Azure DevOps projects."""
        if not settings.ado_pat_token or not settings.ado_org_url:
            raise ValueError("ADO PAT token and org URL must be configured in .env")
        
        # ADO PAT tokens need to be base64 encoded for Basic auth
        # Format: username:token (use empty string or PAT as username)
        pat_token = settings.ado_pat_token
        encoded_token = base64.b64encode(f":{pat_token}".encode()).decode()
        org_url = settings.ado_org_url
        
        headers = {
            "Authorization": f"Basic {encoded_token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{org_url}/_apis/projects?api-version=7.0",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "state": p.get("state")
                }
                for p in data.get("value", [])
            ]
        except Exception as e:
            logger.error(f"Error fetching ADO projects: {e}")
            raise
    
    async def get_ado_project(self, project_id: str, user_id: str) -> Dict:
        """Get Azure DevOps project details."""
        if not settings.ado_pat_token or not settings.ado_org_url:
            raise ValueError("ADO PAT token and org URL must be configured in .env")
        
        # ADO PAT tokens need to be base64 encoded for Basic auth
        pat_token = settings.ado_pat_token
        encoded_token = base64.b64encode(f":{pat_token}".encode()).decode()
        org_url = settings.ado_org_url
        
        headers = {
            "Authorization": f"Basic {encoded_token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{org_url}/_apis/projects/{project_id}?api-version=7.0",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ADO project: {e}")
            raise
    
    async def list_snow_spaces(self, user_id: str) -> List[Dict]:
        """List ServiceNow PPM spaces."""
        if not settings.snow_api_token or not settings.snow_base_url:
            raise ValueError("ServiceNow API token and base URL must be configured in .env")
        
        token = settings.snow_api_token
        snow_url = settings.snow_base_url
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{snow_url}/api/sn_ppm/workspace/space",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": s.get("sys_id"),
                    "name": s.get("name"),
                    "description": s.get("description")
                }
                for s in data.get("result", [])
            ]
        except Exception as e:
            logger.error(f"Error fetching ServiceNow spaces: {e}")
            raise
    
    async def get_snow_space(self, space_id: str, user_id: str) -> Dict:
        """Get ServiceNow PPM space details."""
        if not settings.snow_api_token or not settings.snow_base_url:
            raise ValueError("ServiceNow API token and base URL must be configured in .env")
        
        token = settings.snow_api_token
        snow_url = settings.snow_base_url
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"{snow_url}/api/sn_ppm/workspace/space/{space_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ServiceNow space: {e}")
            raise
    
    async def list_sharepoint_sites(self, user_id: str) -> List[Dict]:
        """List SharePoint sites."""
        if not settings.sharepoint_access_token:
            raise ValueError("SharePoint access token must be configured in .env")
        
        token = settings.sharepoint_access_token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/sites?search=*",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": s.get("id"),
                    "name": s.get("displayName"),
                    "webUrl": s.get("webUrl"),
                    "description": s.get("description")
                }
                for s in data.get("value", [])
            ]
        except Exception as e:
            logger.error(f"Error fetching SharePoint sites: {e}")
            raise
    
    async def get_sharepoint_site(self, site_id: str, user_id: str) -> Dict:
        """Get SharePoint site details."""
        if not settings.sharepoint_access_token:
            raise ValueError("SharePoint access token must be configured in .env")
        
        token = settings.sharepoint_access_token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/sites/{site_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SharePoint site: {e}")
            raise
    
    async def link_external_entity(
        self,
        workspace_id: str,
        provider: str,
        external_id: str,
        display_name: str,
        actor_id: str
    ) -> Dict:
        """Link an external entity to a workspace."""
        pool = await get_db_pool()
        link_id = str(uuid.uuid4())
        
        # Store config with metadata
        config = json.dumps({
            "linked_by": actor_id,
            "provider": provider
        })
        
        link = await create_external_link(
            pool,
            link_id,
            workspace_id,
            provider.upper(),
            external_id,
            display_name,
            config
        )
        
        await self.audit_service.log_action(
            workspace_id,
            "EXTERNAL_LINK_CREATED",
            actor_id,
            {"provider": provider, "external_id": external_id}
        )
        
        return link

