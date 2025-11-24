# Setup Guide

## Prerequisites

- Python 3.11+
- SQL Server database
- Azure subscription with:
  - Azure Entra ID (Azure AD) app registration
  - Azure Key Vault
  - Azure Blob Storage account

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure Entra ID

1. Register an application in Azure Portal → Azure Active Directory → App registrations
2. Note the:
   - Tenant ID
   - Application (client) ID
   - API audience (usually `api://<client-id>`)

### 3. Configure Azure Blob Storage

1. Create a storage account in Azure Portal
2. Create a container (default: `workspaces`)
3. Get connection string or use Managed Identity

### 4. Configure Database

1. Create SQL Server database
2. Run `database_schema.sql` to create tables
3. Ensure SQL Server authentication is configured

### 5. Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DB_SERVER=your-server.database.windows.net
DB_NAME=your-database
DB_USER=your-username
DB_PASSWORD=your-password
DB_DRIVER=ODBC Driver 18 for SQL Server

# Azure Entra ID
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_AUDIENCE=api://your-client-id

# PMA Token
PMA_TOKEN_SECRET=your-secret-key-min-32-chars
PMA_TOKEN_EXPIRY_HOURS=24

# Azure Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_CONTAINER_NAME=workspaces
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net

# Integration Tokens - Jira
JIRA_API_TOKEN=your-jira-api-token
JIRA_BASE_URL=https://yourcompany.atlassian.net

# Integration Tokens - Azure DevOps
ADO_PAT_TOKEN=your-azure-devops-personal-access-token
ADO_ORG_URL=https://dev.azure.com/yourorg

# Integration Tokens - ServiceNow
SNOW_API_TOKEN=your-servicenow-api-token
SNOW_BASE_URL=https://yourinstance.service-now.com

# Integration Tokens - SharePoint
SHAREPOINT_ACCESS_TOKEN=your-sharepoint-access-token

# Application
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 6. Run the Application

```bash
# Development
python -m app.main

# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Test the API

1. Get Azure Entra ID token (use Azure CLI or MSAL)
2. Call `/auth/validate` with Azure token to get PMA token
3. Use PMA token in `X-PMA-Token` header for subsequent requests

Example:

```bash
# Validate token
curl -X POST http://localhost:8000/auth/validate \
  -H "Authorization: Bearer <azure-token>"

# Create workspace
curl -X POST http://localhost:8000/workspaces \
  -H "Authorization: Bearer <azure-token>" \
  -H "X-PMA-Token: <pma-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workspace", "description": "Test workspace"}'
```

## Troubleshooting

### Database Connection Issues

- Ensure SQL Server allows TCP/IP connections
- Check firewall rules allow your IP
- Verify credentials and database name
- Test connection with `sqlcmd` or Azure Data Studio

### Azure Authentication Issues

- Verify tenant ID and client ID
- Check token audience matches `AZURE_AUDIENCE`
- Ensure token hasn't expired
- Verify app registration has correct API permissions

### Integration Token Issues

- Verify all integration tokens are set in `.env` file
- Check token formats (ADO PAT tokens should be plain text, not base64 encoded)
- Ensure URLs are correct and include protocol (https://)
- Verify tokens haven't expired

### Blob Storage Issues

- Verify storage account name and container exist
- Check connection string format
- Ensure container has proper permissions

## Production Deployment

1. Use environment variables or Azure App Configuration
2. Enable HTTPS/TLS
3. Configure CORS appropriately
4. Set up logging and monitoring
5. Use managed identity for Azure resources
6. Enable database connection pooling
7. Configure rate limiting
8. Set up health checks and readiness probes

