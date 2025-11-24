# PM Assist FastAPI Backend

Production-grade FastAPI backend for workspace management with Azure Entra ID authentication, SQL Server, and external integrations.

## Features

- **Raw SQL Queries**: All database operations use raw SQL (no ORM)
- **Multi-Database Support**: Switch between SQL Server and SQLite3 via configuration
- **Azure Entra ID JWT Authentication**: Validates Azure tokens
- **Custom PM Assist Token**: Per-workspace role-based authorization
- **SQL Server**: Async connection pooling with aioodbc
- **SQLite3**: Local development database support
- **Azure Blob Storage**: Automatic folder creation for workspaces
- **External Integrations**: Jira, Azure DevOps, ServiceNow PPM, SharePoint
- **Audit Logging**: Complete audit trail for all actions
- **Role-Based Access Control**: OWNER, ADMIN, MEMBER, VIEWER roles

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
│   └── integrations_sp.py
├── core/                   # Core configuration and security
│   ├── config.py
│   ├── security.py
│   ├── token_service.py
│   ├── azure_jwt_validator.py
│   └── middleware.py
├── db/                     # Database layer
│   ├── connection.py
│   └── queries.py
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

3. **Database Setup**

Choose your database type:

**Option A: SQL Server**
Run the SQL scripts to create tables in SQL Server:

```sql
CREATE TABLE Workspace (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    created_by NVARCHAR(200) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    blob_path NVARCHAR(500),
    is_active BIT DEFAULT 1
);

CREATE TABLE WorkspaceMember (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    user_id NVARCHAR(200) NOT NULL,
    display_name NVARCHAR(200),
    role NVARCHAR(50) NOT NULL,
    added_at DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_WorkspaceMember_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

CREATE TABLE WorkspaceExternalLink (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    provider NVARCHAR(50) NOT NULL,
    external_id NVARCHAR(255) NOT NULL,
    display_name NVARCHAR(255),
    config NVARCHAR(MAX),
    linked_at DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_WorkspaceExternalLink_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

CREATE TABLE AuditLog (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    action NVARCHAR(255) NOT NULL,
    actor_id NVARCHAR(200) NOT NULL,
    details NVARCHAR(MAX) NULL,
    timestamp DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_AuditLog_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);
```

**Option B: SQLite (for local development)**
Run the SQLite schema script:
```bash
sqlite3 app.db < database_schema_sqlite.sql
```

Or set `DB_TYPE=sqlite` and `DB_NAME=app.db` in your `.env` file. The database will be created automatically if it doesn't exist.

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

### Workspaces

- `POST /workspaces` - Create workspace
- `GET /workspaces` - List workspaces for user
- `GET /workspaces/{id}` - Get workspace details
- `DELETE /workspaces/{id}` - Soft delete workspace

### Members

- `POST /workspaces/{id}/members` - Add member
- `GET /workspaces/{id}/members` - List members
- `DELETE /workspaces/{id}/members/{member_id}` - Remove member

### Integrations

#### Jira
- `GET /integrations/jira/projects` - List projects
- `GET /integrations/jira/projects/{project_id}` - Get project details
- `POST /workspaces/{id}/links/jira` - Link Jira project

#### Azure DevOps
- `GET /integrations/ado/projects` - List projects
- `GET /integrations/ado/projects/{project_id}` - Get project details
- `POST /workspaces/{id}/links/ado` - Link ADO project

#### ServiceNow
- `GET /integrations/snow/spaces` - List spaces
- `GET /integrations/snow/spaces/{space_id}` - Get space details
- `POST /workspaces/{id}/links/snow` - Link ServiceNow space

#### SharePoint
- `GET /integrations/sharepoint/sites` - List sites
- `GET /integrations/sharepoint/sites/{site_id}` - Get site details
- `POST /workspaces/{id}/links/sharepoint` - Link SharePoint site

## Authentication Flow

1. Frontend sends Azure Entra ID JWT token in `Authorization: Bearer <token>` header
2. Backend validates Azure token
3. Backend generates PM Assist token with workspace roles
4. Frontend stores PM Assist token and sends it in `X-PMA-Token` header for subsequent requests
5. Middleware validates both tokens and extracts workspace role from path

## Authorization

Roles are hierarchical:
- **OWNER**: Full access
- **ADMIN**: Manage members and integrations
- **MEMBER**: Partial access
- **VIEWER**: Read-only

## Error Handling

All errors return consistent JSON format:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable message"
}
```

Common error codes:
- `MISSING_AZURE_TOKEN`
- `MISSING_PMA_TOKEN`
- `INVALID_AZURE_TOKEN`
- `INVALID_PMA_TOKEN`
- `USER_NOT_AUTHORIZED`
- `WORKSPACE_NOT_FOUND`
- `DB_QUERY_FAILED`
- `INTEGRATION_FAILURE`

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

## License

Proprietary

