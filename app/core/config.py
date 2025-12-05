from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (SQL Server only)
    db_server: Optional[str] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_driver: str = "ODBC Driver 18 for SQL Server"
    
    # Azure Entra ID
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_audience: Optional[str] = None
    
    # PMA Token
    pma_token_secret: Optional[str] = None
    pma_token_expiry_hours: int = 24
    
    # Azure Blob Storage
    azure_storage_account_name: Optional[str] = None
    azure_storage_container_name: str = "workspaces"
    azure_storage_connection_string: Optional[str] = None
    
    # Integration Tokens (Jira)
    jira_api_token: Optional[str] = None
    jira_base_url: Optional[str] = None
    
    # Integration Tokens (Azure DevOps)
    ado_pat_token: Optional[str] = None
    ado_org_url: Optional[str] = None
    
    # Integration Tokens (ServiceNow)
    snow_api_token: Optional[str] = None
    snow_base_url: Optional[str] = None
    
    # Integration Tokens (SharePoint)
    sharepoint_access_token: Optional[str] = None
    
    # Application
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

