"""
Database schema initialization for SQLite.
"""
from app.core.config import settings
from app.db.connection import get_db_pool
import logging

logger = logging.getLogger(__name__)

SQLITE_SCHEMA = """
-- Workspace Table
CREATE TABLE IF NOT EXISTS Workspace (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    blob_path TEXT,
    is_active INTEGER DEFAULT 1
);

-- WorkspaceMember Table
CREATE TABLE IF NOT EXISTS WorkspaceMember (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL,
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- WorkspaceExternalLink Table
CREATE TABLE IF NOT EXISTS WorkspaceExternalLink (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    display_name TEXT,
    config TEXT,
    linked_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- AuditLog Table
CREATE TABLE IF NOT EXISTS AuditLog (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    details TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS IX_WorkspaceMember_WorkspaceId ON WorkspaceMember(workspace_id);
CREATE INDEX IF NOT EXISTS IX_WorkspaceMember_UserId ON WorkspaceMember(user_id);
CREATE INDEX IF NOT EXISTS IX_WorkspaceExternalLink_WorkspaceId ON WorkspaceExternalLink(workspace_id);
CREATE INDEX IF NOT EXISTS IX_AuditLog_WorkspaceId ON AuditLog(workspace_id);
CREATE INDEX IF NOT EXISTS IX_AuditLog_Timestamp ON AuditLog(timestamp);
"""


async def init_sqlite_schema(pool):
    """Initialize SQLite database schema if tables don't exist."""
    try:
        cursor = await pool.cursor()
        # Execute all schema statements
        await cursor.executescript(SQLITE_SCHEMA)
        await pool.commit()
        await cursor.close()
        logger.info("SQLite schema initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing SQLite schema: {e}")
        raise


async def check_and_init_schema():
    """Check if schema exists and initialize if needed (SQLite only)."""
    db_type = (settings.db_type or "sqlserver").lower()
    
    if db_type == "sqlite":
        try:
            pool = await get_db_pool()
            # Check if Workspace table exists
            cursor = await pool.cursor()
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Workspace'"
            )
            table_exists = await cursor.fetchone()
            await cursor.close()
            
            if not table_exists:
                logger.info("SQLite database schema not found. Initializing...")
                await init_sqlite_schema(pool)
            else:
                logger.debug("SQLite schema already exists")
        except Exception as e:
            logger.error(f"Error checking/initializing SQLite schema: {e}")
            raise

