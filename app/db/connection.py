from app.core.config import settings
import asyncio
from typing import Optional
import os

_db_pool: Optional[object] = None


async def get_db_pool():
    """Get or create database connection pool."""
    global _db_pool
    
    if _db_pool is None:
        db_type = (settings.db_type or "sqlserver").lower()
        
        if db_type == "sqlite":
            # SQLite configuration
            print("SQLite")
            from aiosqlite import connect
            
            if not settings.db_name:
                raise ValueError(
                    "Database configuration is missing. Please set DB_NAME (path to SQLite database file) in .env file"
                )
            
            # Ensure directory exists for SQLite file
            db_path = settings.db_name
            db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            # aiosqlite doesn't have create_pool, so we create a simple connection wrapper
            # For simplicity, we'll use a single connection (can be enhanced later)
            _db_pool = await connect(db_path)
            # Enable row factory for easier access
            _db_pool.row_factory = None  # Use tuple rows for consistency
            
            # Initialize schema if tables don't exist
            try:
                from db.init_schema import init_sqlite_schema
                await init_sqlite_schema(_db_pool)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Schema initialization warning (may already exist): {e}")
        else:
            # SQL Server configuration
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
    """Close database connection pool."""
    global _db_pool
    if _db_pool:
        db_type = (settings.db_type or "sqlserver").lower()
        if db_type == "sqlite":
            await _db_pool.close()
        else:
            _db_pool.close()
            await _db_pool.wait_closed()
        _db_pool = None

