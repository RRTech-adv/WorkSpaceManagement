"""
Unified query functions that work with both SQL Server and SQLite.
This is a complete rewrite of queries.py with proper database abstraction.
"""
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from app.db.db_adapter import DBAdapter
from app.core.config import settings


async def _execute_query(pool, query: str, params: tuple = None, fetch_one: bool = False, commit: bool = False):
    """Execute a query and return results, handling both SQL Server and SQLite."""
    db_type = (settings.db_type or "sqlserver").lower()
    
    if db_type == "sqlite":
        print("SQLite")
        # For SQLite, pool is the connection itself
        cursor = await pool.cursor()
        try:
            if params:
                await cursor.execute(query, params)
            else:
                await cursor.execute(query)
            if commit:
                await pool.commit()
            if fetch_one:
                result = await cursor.fetchone()
            else:
                result = await cursor.fetchall()
            return result if result is not None else ([] if not fetch_one else None)
        finally:
            await cursor.close()
    else:
        # For SQL Server, pool is a connection pool
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                if commit:
                    await conn.commit()
                if fetch_one:
                    result = await cursor.fetchone()
                    return result if result is not None else None
                else:
                    result = await cursor.fetchall()
                    return result if result is not None else []


async def get_user_workspace_roles(pool, user_id: str) -> Dict[str, str]:
    """Get all workspace roles for a user."""
    try:
        rows = await _execute_query(
            pool,
            "SELECT workspace_id, role FROM WorkspaceMember WHERE user_id = ?",
            (user_id,)
        )
        # Handle case where rows might be None or empty
        if not rows:
            return {}
        return {str(row[0]): row[1] for row in rows}
    except Exception as e:
        # Log error but return empty dict to allow auth to proceed
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching workspace roles for user {user_id}: {e}")
        # Return empty dict so user can still authenticate (they just won't have workspace roles yet)
        return {}


async def create_workspace(
    pool,
    workspace_id: str,
    name: str,
    description: Optional[str],
    created_by: str,
    blob_path: str
) -> Dict:
    """Create a new workspace."""
    current_time = DBAdapter.get_current_time_sql()
    await _execute_query(
        pool,
        f"""
        INSERT INTO Workspace 
        (id, name, description, created_by, created_at, updated_at, blob_path, is_active)
        VALUES (?, ?, ?, ?, {current_time}, {current_time}, ?, 1)
        """,
        (workspace_id, name, description, created_by, blob_path),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        """
        SELECT id, name, description, created_by, created_at, updated_at, blob_path, is_active
        FROM Workspace WHERE id = ?
        """,
        (workspace_id,),
        fetch_one=True
    )
    
    return {
        "id": str(row[0]),
        "name": row[1],
        "description": row[2],
        "created_by": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "blob_path": row[6],
        "is_active": DBAdapter.parse_boolean(row[7])
    }


async def add_workspace_member(
    pool,
    member_id: str,
    workspace_id: str,
    user_id: str,
    display_name: str,
    role: str
) -> Dict:
    """Add a member to a workspace."""
    current_time = DBAdapter.get_current_time_sql()
    await _execute_query(
        pool,
        f"""
        INSERT INTO WorkspaceMember
        (id, workspace_id, user_id, display_name, role, added_at)
        VALUES (?, ?, ?, ?, ?, {current_time})
        """,
        (member_id, workspace_id, user_id, display_name, role),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        "SELECT id, workspace_id, user_id, display_name, role, added_at FROM WorkspaceMember WHERE id = ?",
        (member_id,),
        fetch_one=True
    )
    
    return {
        "id": str(row[0]),
        "workspace_id": str(row[1]),
        "user_id": row[2],
        "display_name": row[3],
        "role": row[4],
        "added_at": row[5]
    }


async def get_workspace_by_id(pool, workspace_id: str) -> Optional[Dict]:
    """Get workspace by ID."""
    row = await _execute_query(
        pool,
        """
        SELECT id, name, description, created_by, created_at, updated_at, blob_path, is_active
        FROM Workspace WHERE id = ? AND is_active = 1
        """,
        (workspace_id,),
        fetch_one=True
    )
    
    if not row:
        return None
    
    return {
        "id": str(row[0]),
        "name": row[1],
        "description": row[2],
        "created_by": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "blob_path": row[6],
        "is_active": DBAdapter.parse_boolean(row[7])
    }


async def get_workspaces_by_user(pool, user_id: str) -> List[Dict]:
    """Get all workspaces for a user."""
    rows = await _execute_query(
        pool,
        """
        SELECT w.id, w.name, w.description, w.created_by, w.created_at, w.updated_at, w.blob_path, w.is_active
        FROM Workspace w
        INNER JOIN WorkspaceMember m ON w.id = m.workspace_id
        WHERE m.user_id = ? AND w.is_active = 1
        ORDER BY w.created_at DESC
        """,
        (user_id,)
    )
    
    return [
        {
            "id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "created_by": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "blob_path": row[6],
            "is_active": DBAdapter.parse_boolean(row[7])
        }
        for row in rows
    ]


async def get_workspace_members(pool, workspace_id: str) -> List[Dict]:
    """Get all members of a workspace."""
    rows = await _execute_query(
        pool,
        """
        SELECT id, workspace_id, user_id, display_name, role, added_at
        FROM WorkspaceMember WHERE workspace_id = ? ORDER BY added_at ASC
        """,
        (workspace_id,)
    )
    
    return [
        {
            "id": str(row[0]),
            "workspace_id": str(row[1]),
            "user_id": row[2],
            "display_name": row[3],
            "role": row[4],
            "added_at": row[5]
        }
        for row in rows
    ]


async def delete_workspace_member(pool, member_id: str, workspace_id: str) -> bool:
    """Delete a member from a workspace."""
    db_type = (settings.db_type or "sqlserver").lower()
    
    if db_type == "sqlite":
        cursor = await pool.cursor()
        await cursor.execute(
            "DELETE FROM WorkspaceMember WHERE id = ? AND workspace_id = ?",
            (member_id, workspace_id)
        )
        rowcount = cursor.rowcount
        await pool.commit()
        await cursor.close()
        return rowcount > 0
    else:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM WorkspaceMember WHERE id = ? AND workspace_id = ?",
                    (member_id, workspace_id)
                )
                await conn.commit()
                return cursor.rowcount > 0


async def soft_delete_workspace(pool, workspace_id: str) -> bool:
    """Soft delete a workspace."""
    current_time = DBAdapter.get_current_time_sql()
    db_type = (settings.db_type or "sqlserver").lower()
    
    if db_type == "sqlite":
        cursor = await pool.cursor()
        await cursor.execute(
            f"UPDATE Workspace SET is_active = 0, updated_at = {current_time} WHERE id = ?",
            (workspace_id,)
        )
        rowcount = cursor.rowcount
        await pool.commit()
        await cursor.close()
        return rowcount > 0
    else:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE Workspace SET is_active = 0, updated_at = {current_time} WHERE id = ?",
                    (workspace_id,)
                )
                await conn.commit()
                return cursor.rowcount > 0


async def create_external_link(
    pool,
    link_id: str,
    workspace_id: str,
    provider: str,
    external_id: str,
    display_name: str,
    config: Optional[str]
) -> Dict:
    """Create an external link for a workspace."""
    current_time = DBAdapter.get_current_time_sql()
    await _execute_query(
        pool,
        f"""
        INSERT INTO WorkspaceExternalLink
        (id, workspace_id, provider, external_id, display_name, config, linked_at)
        VALUES (?, ?, ?, ?, ?, ?, {current_time})
        """,
        (link_id, workspace_id, provider, external_id, display_name, config),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        "SELECT id, workspace_id, provider, external_id, display_name, config, linked_at FROM WorkspaceExternalLink WHERE id = ?",
        (link_id,),
        fetch_one=True
    )
    
    return {
        "id": str(row[0]),
        "workspace_id": str(row[1]),
        "provider": row[2],
        "external_id": row[3],
        "display_name": row[4],
        "config": row[5],
        "linked_at": row[6]
    }


async def get_workspace_external_links(pool, workspace_id: str) -> List[Dict]:
    """Get all external links for a workspace."""
    rows = await _execute_query(
        pool,
        """
        SELECT id, workspace_id, provider, external_id, display_name, config, linked_at
        FROM WorkspaceExternalLink WHERE workspace_id = ? ORDER BY linked_at DESC
        """,
        (workspace_id,)
    )
    
    return [
        {
            "id": str(row[0]),
            "workspace_id": str(row[1]),
            "provider": row[2],
            "external_id": row[3],
            "display_name": row[4],
            "config": row[5],
            "linked_at": row[6]
        }
        for row in rows
    ]


async def create_audit_log(
    pool,
    log_id: str,
    workspace_id: str,
    action: str,
    actor_id: str,
    details: Optional[str]
):
    """Create an audit log entry."""
    current_time = DBAdapter.get_current_time_sql()
    await _execute_query(
        pool,
        f"""
        INSERT INTO AuditLog
        (id, workspace_id, action, actor_id, details, timestamp)
        VALUES (?, ?, ?, ?, ?, {current_time})
        """,
        (log_id, workspace_id, action, actor_id, details),
        commit=True
    )

