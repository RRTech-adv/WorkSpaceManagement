"""
Functions to create and manage per-workspace database schemas.
Each workspace gets its own schema: ws_<guid_no_hyphens>
"""
import uuid
import logging
from app.db.connection import get_db_pool

logger = logging.getLogger(__name__)


def get_workspace_schema_name(workspace_id: str) -> str:
    """
    Generate schema name from workspace GUID.
    Format: ws_<guid_without_hyphens>
    Example: ws_123e4567e89b12d3a456426614174000
    """
    # Remove hyphens from GUID
    guid_no_hyphens = workspace_id.replace("-", "")
    return f"ws_{guid_no_hyphens}"


async def create_workspace_schema(workspace_id: str) -> str:
    """
    Create a new schema for a workspace with all required tables.
    
    Returns the schema name created.
    """
    pool = await get_db_pool()
    schema_name = get_workspace_schema_name(workspace_id)
    
    try:
        # Create schema
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Create schema
                await cursor.execute(f"CREATE SCHEMA {schema_name}")
                await conn.commit()
                logger.info(f"Created schema {schema_name} for workspace {workspace_id}")
                
                # Create workspace_integrations table
                await cursor.execute(f"""
                    CREATE TABLE {schema_name}.workspace_integrations (
                        workspace_integration_id UNIQUEIDENTIFIER PRIMARY KEY,
                        workspace_id UNIQUEIDENTIFIER NOT NULL,
                        user_id NVARCHAR(200),
                        integration_display_name NVARCHAR(255),
                        provider NVARCHAR(50) NOT NULL,
                        url NVARCHAR(500),
                        extra_config_json NVARCHAR(MAX),
                        connection_status NVARCHAR(50),
                        added_by_user_id NVARCHAR(200),
                        added_utc DATETIME2 DEFAULT SYSDATETIME()
                    )
                """)
                
                # Create workspace_agents table
                await cursor.execute(f"""
                    CREATE TABLE {schema_name}.workspace_agents (
                        workspace_agent_id UNIQUEIDENTIFIER PRIMARY KEY,
                        workspace_id UNIQUEIDENTIFIER NOT NULL,
                        agent_type NVARCHAR(100) NOT NULL,
                        is_enabled BIT DEFAULT 1,
                        config_json NVARCHAR(MAX),
                        created_utc DATETIME2 DEFAULT SYSDATETIME(),
                        created_by_user_id NVARCHAR(200)
                    )
                """)
                
                # Create automation_jobs table
                await cursor.execute(f"""
                    CREATE TABLE {schema_name}.automation_jobs (
                        job_id UNIQUEIDENTIFIER PRIMARY KEY,
                        workspace_id UNIQUEIDENTIFIER NOT NULL,
                        workspace_agent_id UNIQUEIDENTIFIER,
                        name NVARCHAR(255) NOT NULL,
                        schedule_cron NVARCHAR(255),
                        is_active BIT DEFAULT 1,
                        created_utc DATETIME2 DEFAULT SYSDATETIME()
                    )
                """)
                
                # Create automation_job_runs table
                await cursor.execute(f"""
                    CREATE TABLE {schema_name}.automation_job_runs (
                        job_run_id UNIQUEIDENTIFIER PRIMARY KEY,
                        job_id UNIQUEIDENTIFIER NOT NULL,
                        started_utc DATETIME2 DEFAULT SYSDATETIME(),
                        completed_utc DATETIME2 NULL,
                        status NVARCHAR(50),
                        error_message NVARCHAR(MAX)
                    )
                """)
                
                # Create file_artifacts table
                await cursor.execute(f"""
                    CREATE TABLE {schema_name}.file_artifacts (
                        file_artifact_id UNIQUEIDENTIFIER PRIMARY KEY,
                        workspace_id UNIQUEIDENTIFIER NOT NULL,
                        workspace_agent_id UNIQUEIDENTIFIER,
                        job_run_id UNIQUEIDENTIFIER,
                        type NVARCHAR(50),
                        blob_url NVARCHAR(500),
                        file_name NVARCHAR(255),
                        created_utc DATETIME2 DEFAULT SYSDATETIME(),
                        created_by_user_id NVARCHAR(200)
                    )
                """)
                
                # Create indexes
                await cursor.execute(f"CREATE INDEX IX_workspace_integrations_workspace_id ON {schema_name}.workspace_integrations(workspace_id)")
                await cursor.execute(f"CREATE INDEX IX_workspace_integrations_provider ON {schema_name}.workspace_integrations(provider)")
                await cursor.execute(f"CREATE INDEX IX_workspace_agents_workspace_id ON {schema_name}.workspace_agents(workspace_id)")
                await cursor.execute(f"CREATE INDEX IX_automation_jobs_workspace_id ON {schema_name}.automation_jobs(workspace_id)")
                await cursor.execute(f"CREATE INDEX IX_automation_job_runs_job_id ON {schema_name}.automation_job_runs(job_id)")
                await cursor.execute(f"CREATE INDEX IX_file_artifacts_workspace_id ON {schema_name}.file_artifacts(workspace_id)")
                
                await conn.commit()
                logger.info(f"Created all tables in schema {schema_name} for workspace {workspace_id}")
                
        return schema_name
        
    except Exception as e:
        logger.error(f"Error creating workspace schema {schema_name}: {e}", exc_info=True)
        raise


async def get_workspace_schema_name_from_db(workspace_id: str) -> str:
    """
    Get the schema name for a workspace from the database.
    Falls back to generating it if not found in database.
    """
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT db_schema_name 
                    FROM pmassist_master.Workspace 
                    WHERE id = ?
                """, (workspace_id,))
                
                row = await cursor.fetchone()
                if row and row[0]:
                    return row[0]
                
                # If not found, generate it
                return get_workspace_schema_name(workspace_id)
                
    except Exception as e:
        logger.error(f"Error getting workspace schema name: {e}", exc_info=True)
        # Fallback to generated name
        return get_workspace_schema_name(workspace_id)

