from app.core.config import settings
from typing import Optional

_db_pool: Optional[object] = None


async def get_db_pool():
    """Get or create SQL Server database connection pool."""
    global _db_pool
    
    if _db_pool is None:
        from aioodbc import create_pool
        
        if not all([settings.db_server, settings.db_name, settings.db_user, settings.db_password]):
            raise ValueError(
                "Database configuration is missing. Please set DB_SERVER, DB_NAME, DB_USER, and DB_PASSWORD in .env file"
            )
        
        connection_string = (
            f"DRIVER={{{settings.db_driver}}};"
            f"SERVER={settings.db_server};"
            f"DATABASE={settings.db_name};"
            f"UID={settings.db_user};"
            f"PWD={settings.db_password};"
            f"TrustServerCertificate=yes;"
        )
        
        _db_pool = await create_pool(
            dsn=connection_string,
            minsize=1,
            maxsize=10,
            echo=False
        )
    
    return _db_pool


async def close_db_pool():
    """Close SQL Server database connection pool."""
    global _db_pool
    if _db_pool:
        _db_pool.close()
        await _db_pool.wait_closed()
        _db_pool = None

