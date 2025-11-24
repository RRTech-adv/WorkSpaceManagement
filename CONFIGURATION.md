# Configuration Guide

## How Configuration Values Are Loaded

The application uses **Pydantic Settings** (`pydantic_settings.BaseSettings`) to automatically load configuration from environment variables and `.env` files.

### Configuration Flow

1. **Settings Class** (`app/core/config.py`)
   - Defines all configuration fields as class attributes
   - Uses `BaseSettings` which automatically reads from:
     - Environment variables
     - `.env` file (specified in `Config.env_file = ".env"`)
     - Default values (if provided)

2. **Singleton Instance** (`settings = Settings()`)
   - Created once when the module is imported
   - Available throughout the application via `from app.core.config import settings`

3. **Automatic Mapping**
   - Environment variable names are automatically mapped to class attributes
   - Case-insensitive matching (due to `case_sensitive = False`)
   - Example: `DB_SERVER` → `settings.db_server`

### Example: How `db_server` is Loaded

```python
# In .env file:
DB_SERVER=your-server.database.windows.net

# In config.py:
class Settings(BaseSettings):
    db_server: Optional[str] = None  # Maps to DB_SERVER env var

# Usage in code:
from app.core.config import settings
server = settings.db_server  # Gets value from .env or environment
```

### Configuration Priority

Values are loaded in this order (first match wins):
1. **Environment variables** (highest priority)
2. **`.env` file**
3. **Default values** (if specified in class)

### All Configuration Fields

#### Database Configuration
- `DB_TYPE` → `settings.db_type` (default: "sqlite")
- `DB_SERVER` → `settings.db_server` (SQL Server only)
- `DB_NAME` → `settings.db_name` (database name or SQLite file path)
- `DB_USER` → `settings.db_user` (SQL Server only)
- `DB_PASSWORD` → `settings.db_password` (SQL Server only)
- `DB_DRIVER` → `settings.db_driver` (default: "ODBC Driver 18 for SQL Server")

#### Azure Entra ID
- `AZURE_TENANT_ID` → `settings.azure_tenant_id`
- `AZURE_CLIENT_ID` → `settings.azure_client_id`
- `AZURE_AUDIENCE` → `settings.azure_audience`

#### PMA Token
- `PMA_TOKEN_SECRET` → `settings.pma_token_secret`
- `PMA_TOKEN_EXPIRY_HOURS` → `settings.pma_token_expiry_hours` (default: 24)

#### Azure Blob Storage
- `AZURE_STORAGE_ACCOUNT_NAME` → `settings.azure_storage_account_name`
- `AZURE_STORAGE_CONTAINER_NAME` → `settings.azure_storage_container_name` (default: "workspaces")
- `AZURE_STORAGE_CONNECTION_STRING` → `settings.azure_storage_connection_string`

#### Integration Tokens
- `JIRA_API_TOKEN` → `settings.jira_api_token`
- `JIRA_BASE_URL` → `settings.jira_base_url`
- `ADO_PAT_TOKEN` → `settings.ado_pat_token`
- `ADO_ORG_URL` → `settings.ado_org_url`
- `SNOW_API_TOKEN` → `settings.snow_api_token`
- `SNOW_BASE_URL` → `settings.snow_base_url`
- `SHAREPOINT_ACCESS_TOKEN` → `settings.sharepoint_access_token`

#### Application Settings
- `API_HOST` → `settings.api_host` (default: "0.0.0.0")
- `API_PORT` → `settings.api_port` (default: 8000)
- `LOG_LEVEL` → `settings.log_level` (default: "INFO")

### Usage Examples

#### In Database Connection
```python
from app.core.config import settings

# Access database configuration
db_type = settings.db_type
db_name = settings.db_name
db_server = settings.db_server
```

#### In Security/Token Generation
```python
from app.core.config import settings

# Access PMA token secret
secret = settings.pma_token_secret
expiry_hours = settings.pma_token_expiry_hours
```

#### In Integration Service
```python
from app.core.config import settings

# Access integration tokens
jira_token = settings.jira_api_token
jira_url = settings.jira_base_url
```

### How to Set Values

#### Option 1: `.env` File (Recommended for Development)
```env
DB_TYPE=sqlite
DB_NAME=app.db
PMA_TOKEN_SECRET=your-secret-key-here
AZURE_TENANT_ID=your-tenant-id
```

#### Option 2: Environment Variables (Recommended for Production)
```bash
# Windows PowerShell
$env:DB_TYPE="sqlite"
$env:DB_NAME="app.db"

# Linux/Mac
export DB_TYPE=sqlite
export DB_NAME=app.db
```

#### Option 3: Default Values (In Code)
```python
class Settings(BaseSettings):
    api_host: str = "0.0.0.0"  # Default value
    api_port: int = 8000        # Default value
```

### Important Notes

1. **Case Insensitive**: Environment variable names are case-insensitive
   - `DB_SERVER`, `db_server`, `Db_Server` all work

2. **Optional Fields**: Most fields are `Optional[str]` to allow the app to start without full configuration

3. **Required Fields**: Some fields are required for specific features:
   - Database: `DB_NAME` (for SQLite) or `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (for SQL Server)
   - Authentication: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_AUDIENCE`, `PMA_TOKEN_SECRET`

4. **Type Conversion**: Pydantic automatically converts types:
   - `API_PORT=8000` (string) → `settings.api_port` (int)
   - `PMA_TOKEN_EXPIRY_HOURS=24` (string) → `settings.pma_token_expiry_hours` (int)

### Debugging Configuration

To check what values are loaded:
```python
from app.core.config import settings

print(f"DB Type: {settings.db_type}")
print(f"DB Name: {settings.db_name}")
print(f"API Host: {settings.api_host}")
print(f"API Port: {settings.api_port}")
```

### Security Best Practices

1. **Never commit `.env` files** with real secrets to version control
2. **Use `.env.example`** as a template
3. **In production**, use environment variables or secure secret management (Azure Key Vault, etc.)
4. **Rotate secrets regularly**, especially `PMA_TOKEN_SECRET`

