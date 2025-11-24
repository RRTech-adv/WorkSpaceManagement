from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.db.connection import get_db_pool
from app.db.init_schema import init_sqlite_schema
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/db", tags=["database"])


@router.post("/init")
async def initialize_database():
    """
    Initialize database with all tables.
    For SQLite: Creates all tables automatically.
    For SQL Server: Returns instructions (tables must be created manually).
    """
    try:
        db_type = (settings.db_type or "sqlserver").lower()
        
        if db_type == "sqlite":
            # Initialize SQLite schema
            pool = await get_db_pool()
            await init_sqlite_schema(pool)
            
            return {
                "status": "success",
                "message": "Database initialized successfully",
                "database_type": "sqlite",
                "tables_created": [
                    "Workspace",
                    "WorkspaceMember",
                    "WorkspaceExternalLink",
                    "AuditLog"
                ]
            }
        else:
            # For SQL Server, provide instructions
            return {
                "status": "info",
                "message": "SQL Server requires manual table creation",
                "database_type": "sqlserver",
                "instructions": "Please run the SQL script from database_schema.sql in your SQL Server database",
                "script_location": "database_schema.sql"
            }
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_INIT_FAILED",
                "message": f"Failed to initialize database: {str(e)}"
            }
        )


@router.get("/status")
async def database_status():
    """Check database connection and table status."""
    try:
        db_type = (settings.db_type or "sqlserver").lower()
        pool = await get_db_pool()
        
        if db_type == "sqlite":
            # Check if tables exist
            cursor = await pool.cursor()
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Workspace', 'WorkspaceMember', 'WorkspaceExternalLink', 'AuditLog')"
            )
            tables = await cursor.fetchall()
            await cursor.close()
            
            existing_tables = [table[0] for table in tables]
            expected_tables = ["Workspace", "WorkspaceMember", "WorkspaceExternalLink", "AuditLog"]
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            
            return {
                "status": "connected",
                "database_type": "sqlite",
                "database_name": settings.db_name,
                "tables": {
                    "existing": existing_tables,
                    "missing": missing_tables,
                    "all_present": len(missing_tables) == 0
                }
            }
        else:
            # For SQL Server, just check connection
            return {
                "status": "connected",
                "database_type": "sqlserver",
                "database_name": settings.db_name,
                "server": settings.db_server,
                "message": "Connection successful. Use /db/init for initialization instructions."
            }
    except Exception as e:
        logger.error(f"Error checking database status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DB_STATUS_CHECK_FAILED",
                "message": f"Failed to check database status: {str(e)}"
            }
        )

