# WSMS FastAPI Backend

Production-grade FastAPI backend for workspace management with Azure Entra ID authentication, SQL Server, and external integrations.

## Features

- **Raw SQL Queries**: All database operations use raw SQL (no ORM)
- **SQL Server**: Async connection pooling with aioodbc
- **Two-Level Database Architecture**: Global schema for metadata, per-workspace schemas for tenant data
- **Azure Entra ID JWT Authentication**: Validates Azure tokens
- **Custom PM Assist Token**: Per-workspace role-based authorization
- **Azure Blob Storage**: Automatic folder creation for workspaces
- **External Integrations**: Jira, Azure DevOps, ServiceNow PPM, SharePoint
- **Audit Logging**: Complete audit trail for all actions
- **Role-Based Access Control**: OWNER, ADMIN, MEMBER, VIEWER roles
- **Enhanced Error Handling**: Categorized error codes for better frontend integration
- **Comprehensive Logging**: Detailed logging with configurable log levels

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── api/                    # API route handlers
│   ├── auth.py
│   ├── workspaces.py
│   ├── members.py
│   ├── integrations_jira.py
│   ├── integrations_ado.py
│   ├── integrations_snow.py
│   ├── integrations_sp.py
│   └── db_init.py
├── core/                   # Core configuration and security
│   ├── config.py
│   ├── security.py
│   ├── token_service.py
│   ├── azure_jwt_validator.py
│   └── middleware.py
├── db/                     # Database layer
│   ├── connection.py
│   ├── queries.py
│   └── workspace_schema.py  # Per-workspace schema management
├── services/               # Business logic services
│   ├── workspace_service.py
│   ├── member_service.py
│   ├── integration_service.py
│   ├── blob_service.py
│   └── audit_service.py
└── schemas/                # Pydantic schemas
    ├── auth_schemas.py
    ├── workspace_schemas.py
    ├── member_schemas.py
    └── integration_schemas.py
```

## Database Architecture

The application uses a **two-level database architecture**:

### 1. Global Schema (`pmassist_master`)
Contains shared metadata:
- **Workspace**: Workspace definitions with schema names
- **WorkspaceMember**: User memberships and roles
- **AuditLog**: Global audit trail

### 2. Per-Workspace Schemas (`ws_<guid>`)
Each workspace gets its own schema with tenant-specific data:
- **workspace_integrations**: External system integrations (Jira, ADO, ServiceNow, SharePoint)
- **workspace_agents**: Workspace-specific agents
- **automation_jobs**: Scheduled automation jobs
- **automation_job_runs**: Job execution history
- **file_artifacts**: Generated files and artifacts

## Setup

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure Environment Variables**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:
- Database: `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- Azure Entra ID: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_AUDIENCE`
- PMA Token: `PMA_TOKEN_SECRET`
- Blob Storage: `AZURE_STORAGE_CONNECTION_STRING` (optional)
- Integration tokens (optional): `JIRA_API_TOKEN`, `JIRA_BASE_URL`, etc.

3. **Database Setup**

Run the SQL Server schema script to create the global schema:

```bash
# Run database_schema.sql in your SQL Server instance
# This creates the pmassist_master schema and tables
```

The script creates:
- `pmassist_master` schema
- `pmassist_master.Workspace` table (with `db_schema_name`, `status`, `last_seen_utc` fields)
- `pmassist_master.WorkspaceMember` table
- `pmassist_master.AuditLog` table

**Per-workspace schemas are automatically created** when workspaces are created through the API.

4. **Run the Application**

```bash
python -m app.main
```

Or with uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Authentication

- `POST /auth/validate` - Validate Azure token and get PMA token
- `POST /auth/refresh` - Refresh PMA token with updated roles

### Workspaces

- `POST /workspaces` - Create workspace (with optional provider/provider_project for initial integration)
  - Request body includes: `name`, `description`, `provider` (optional), `provider_project` (optional)
- `GET /workspaces` - List workspaces for user (includes integrations)
- `GET /workspaces/{id}` - Get workspace details (includes members and integrations)
- `DELETE /workspaces/{id}` - Soft delete workspace

### Members

- `POST /workspaces/{id}/members` - Add member
- `GET /workspaces/{id}/members` - List members
- `PATCH /workspaces/{id}/members/{member_id}` - Update member role
- `DELETE /workspaces/{id}/members/{member_id}` - Remove member

### Integrations

#### Jira
- `GET /integrations/jira/projects` - List Jira projects

#### Azure DevOps
- `GET /integrations/ado/projects` - List Azure DevOps projects

#### ServiceNow
- `GET /integrations/snow/spaces` - List ServiceNow PPM spaces

#### SharePoint
- `GET /integrations/sharepoint/sites` - List SharePoint sites

**Note**: Integration details are stored in per-workspace schemas and are automatically included in workspace responses.

### Database

- `POST /db/init` - Get database initialization instructions
- `GET /db/status` - Check database connection and table status

## Authentication Flow

1. Frontend sends Azure Entra ID JWT token in `Authorization: Bearer <token>` header
2. Backend validates Azure token
3. Backend generates PM Assist token with workspace roles
4. Frontend stores PM Assist token and sends it in `X-PMA-Token` header for subsequent requests
5. Middleware validates both tokens and extracts workspace role from path

## Authorization

Roles are hierarchical:
- **OWNER**: Full access, can delete workspace
- **ADMIN**: Manage members and integrations
- **MEMBER**: Partial access
- **VIEWER**: Read-only access

## Workspace Creation

When creating a workspace, you can optionally provide:
- `provider`: Integration provider (Jira, ADO, SNOW, SP)
- `provider_project`: Project name/ID for the integration

If provided, an initial integration entry is automatically created in the workspace's schema.

**Example Request:**
```json
{
    "name": "My Workspace",
    "description": "Workspace description",
    "provider": "Jira",
    "provider_project": "PROJ-123"
}
```

## Error Handling

All errors return consistent JSON format:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable message"
}
```

### Error Codes

**Authentication & Authorization:**
- `MISSING_AZURE_TOKEN` - Azure token not provided
- `MISSING_PMA_TOKEN` - PMA token not provided
- `INVALID_AZURE_TOKEN` - Azure token invalid or expired
- `INVALID_PMA_TOKEN` - PMA token invalid or expired
- `TOKEN_MISMATCH` - Token user mismatch
- `USER_NOT_AUTHORIZED` - User lacks required permission
- `PERMISSION_DENIED` - Permission denied

**Validation:**
- `VALIDATION_ERROR` - Request validation failed (includes field-level details)
- `INVALID_REQUEST` - Invalid request format
- `MISSING_REQUIRED_FIELD` - Required field missing

**Resources:**
- `WORKSPACE_NOT_FOUND` - Workspace not found
- `RESOURCE_NOT_FOUND` - Resource not found
- `MEMBER_NOT_FOUND` - Member not found

**Database:**
- `DATABASE_ERROR` - Database operation error
- `DATABASE_CONNECTION_ERROR` - Database connection failed
- `DB_QUERY_FAILED` - Database query failed

**Network & External Services:**
- `NETWORK_ERROR` - Network connection failed
- `REQUEST_TIMEOUT` - Request timed out
- `EXTERNAL_SERVICE_ERROR` - External API error
- `INTEGRATION_FAILURE` - Integration operation failed

**Storage:**
- `STORAGE_ERROR` - Blob storage error

**General:**
- `INTERNAL_SERVER_ERROR` - Unexpected server error
- `HTTP_ERROR` - Generic HTTP error

## Integration Configuration

Integration tokens are configured via environment variables in `.env` file:

- `JIRA_API_TOKEN` - Jira API token
- `JIRA_BASE_URL` - Jira base URL (e.g., `https://yourcompany.atlassian.net`)
- `ADO_PAT_TOKEN` - Azure DevOps Personal Access Token
- `ADO_ORG_URL` - Azure DevOps organization URL (e.g., `https://dev.azure.com/yourorg`)
- `SNOW_API_TOKEN` - ServiceNow API token
- `SNOW_BASE_URL` - ServiceNow instance URL (e.g., `https://yourinstance.service-now.com`)
- `SHAREPOINT_ACCESS_TOKEN` - SharePoint access token

See `.env.example` for the complete configuration template.

## Logging

The application uses Python's built-in logging module. Logs are output to the console by default.

**Configuration:**
- Set `LOG_LEVEL` in `.env` file (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Default: `INFO`

**View Logs:**
- Logs appear in the console/terminal where the application is running
- Full exception details are logged for debugging
- Log format: `YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - message`

See `LOGGING_GUIDE.md` for detailed logging documentation.

## Database Schema Details

### Global Schema: `pmassist_master`

**Workspace Table:**
- Standard fields: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`, `blob_path`, `is_active`
- New fields: `db_schema_name` (per-workspace schema name), `last_seen_utc`, `status` (Active/Archived)

**Per-Workspace Schema Structure:**
Each workspace schema (`ws_<guid_no_hyphens>`) contains:
- `workspace_integrations` - External system integrations
- `workspace_agents` - Workspace-specific agents
- `automation_jobs` - Scheduled jobs
- `automation_job_runs` - Job execution history
- `file_artifacts` - Generated files

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Database Status Check

```bash
curl http://localhost:8000/db/status
```

### Health Check

```bash
curl http://localhost:8000/health
```

## License

Proprietary
