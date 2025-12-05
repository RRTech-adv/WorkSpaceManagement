from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/db", tags=["database"])


@router.post("/init")
async def initialize_database():
    """
    Initialize database schema.
    For SQL Server: Run database_schema.sql manually on your SQL Server instance.
    """
    return {
        "status": "info",
        "message": "For SQL Server, please run database_schema.sql manually on your SQL Server instance.",
        "database_type": "sqlserver",
        "instructions": "Please run the SQL script from database_schema.sql in your SQL Server database",
        "script_location": "database_schema.sql"
    }


@router.get("/status")
async def database_status():
    """Check database connection and table status."""
    try:
        from app.db.connection import get_db_pool
        
        pool = await get_db_pool()
        
        # Check SQL Server tables
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'pmassist_master'
                    AND TABLE_NAME IN ('Workspace', 'WorkspaceMember', 'AuditLog')
                """)
                tables = await cursor.fetchall()
        
        existing_tables = [table[0] for table in tables] if tables else []
        
        return {
            "status": "connected",
            "database_type": "sqlserver",
            "database_name": settings.db_name,
            "server": settings.db_server,
            "tables": {
                "Workspace": "Workspace" in existing_tables,
                "WorkspaceMember": "WorkspaceMember" in existing_tables,
                "AuditLog": "AuditLog" in existing_tables,
            }
        }
    except Exception as e:
        logger.error(f"Error checking database status: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "database_type": "sqlserver"
        }

