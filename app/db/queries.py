"""
Query functions for SQL Server.
"""
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from app.db.db_adapter import DBAdapter


async def _execute_query(pool, query: str, params: tuple = None, fetch_one: bool = False, commit: bool = False):
    """Execute a query and return results for SQL Server."""
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
            "SELECT workspace_id, role FROM pmassist_master.WorkspaceMember WHERE user_id = ?",
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
    blob_path: str,
    db_schema_name: Optional[str] = None
) -> Dict:
    """Create a new workspace with schema name."""
    from app.db.workspace_schema import get_workspace_schema_name
    
    current_time = DBAdapter.get_current_time_sql()
    
    # Generate schema name if not provided
    if not db_schema_name:
        db_schema_name = get_workspace_schema_name(workspace_id)
    
    await _execute_query(
        pool,
        f"""
        INSERT INTO pmassist_master.Workspace 
        (id, name, description, created_by, created_at, updated_at, blob_path, is_active, db_schema_name, status)
        VALUES (?, ?, ?, ?, {current_time}, {current_time}, ?, 1, ?, 'Active')
        """,
        (workspace_id, name, description, created_by, blob_path, db_schema_name),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        """
        SELECT id, name, description, created_by, created_at, updated_at, blob_path, is_active, db_schema_name, last_seen_utc, status
        FROM pmassist_master.Workspace WHERE id = ?
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
        "is_active": DBAdapter.parse_boolean(row[7]),
        "db_schema_name": row[8] if row[8] else None,
        "last_seen_utc": row[9] if len(row) > 9 and row[9] else None,
        "status": row[10] if len(row) > 10 and row[10] else "Active"
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
        INSERT INTO pmassist_master.WorkspaceMember
        (id, workspace_id, user_id, display_name, role, added_at)
        VALUES (?, ?, ?, ?, ?, {current_time})
        """,
        (member_id, workspace_id, user_id, display_name, role),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        "SELECT id, workspace_id, user_id, display_name, role, added_at FROM pmassist_master.WorkspaceMember WHERE id = ?",
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


async def update_workspace_member_role(
    pool,
    member_id: str,
    workspace_id: str,
    new_role: str
) -> Optional[Dict]:
    """Update a member's role in a workspace."""
    current_time = DBAdapter.get_current_time_sql()
    await _execute_query(
        pool,
        f"""
        UPDATE WorkspaceMember
        SET role = ?, added_at = {current_time}
        WHERE id = ? AND workspace_id = ?
        """,
        (new_role, member_id, workspace_id),
        commit=True
    )
    
    row = await _execute_query(
        pool,
        "SELECT id, workspace_id, user_id, display_name, role, added_at FROM pmassist_master.WorkspaceMember WHERE id = ?",
        (member_id,),
        fetch_one=True
    )
    
    if not row:
        return None
    
    return {
        "id": str(row[0]),
        "workspace_id": str(row[1]),
        "user_id": row[2],
        "display_name": row[3],
        "role": row[4],
        "added_at": row[5]
    }


async def get_workspace_member_by_user_id(pool, workspace_id: str, user_id: str) -> Optional[Dict]:
    """Get a workspace member by user_id and workspace_id."""
    row = await _execute_query(
        pool,
        "SELECT id, workspace_id, user_id, display_name, role, added_at FROM pmassist_master.WorkspaceMember WHERE workspace_id = ? AND user_id = ?",
        (workspace_id, user_id),
        fetch_one=True
    )
    
    if not row:
        return None
    
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
        SELECT id, name, description, created_by, created_at, updated_at, blob_path, is_active, db_schema_name, last_seen_utc, status
        FROM pmassist_master.Workspace WHERE id = ? AND is_active = 1
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
        "is_active": DBAdapter.parse_boolean(row[7]),
        "db_schema_name": row[8] if len(row) > 8 and row[8] else None,
        "last_seen_utc": row[9] if len(row) > 9 and row[9] else None,
        "status": row[10] if len(row) > 10 and row[10] else "Active"
    }


async def get_workspaces_by_user(pool, user_id: str) -> List[Dict]:
    """Get all workspaces for a user."""
    rows = await _execute_query(
        pool,
        """
        SELECT w.id, w.name, w.description, w.created_by, w.created_at, w.updated_at, w.blob_path, w.is_active, w.db_schema_name, w.last_seen_utc, w.status
        FROM pmassist_master.Workspace w
        INNER JOIN pmassist_master.WorkspaceMember m ON w.id = m.workspace_id
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
            "is_active": DBAdapter.parse_boolean(row[7]),
            "db_schema_name": row[8] if len(row) > 8 and row[8] else None,
            "last_seen_utc": row[9] if len(row) > 9 and row[9] else None,
            "status": row[10] if len(row) > 10 and row[10] else "Active"
        }
        for row in rows
    ]


async def get_workspace_members(pool, workspace_id: str) -> List[Dict]:
    """Get all members of a workspace."""
    rows = await _execute_query(
        pool,
        """
        SELECT id, workspace_id, user_id, display_name, role, added_at
        FROM pmassist_master.WorkspaceMember WHERE workspace_id = ? ORDER BY added_at ASC
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
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                    f"UPDATE pmassist_master.Workspace SET is_active = 0, updated_at = {current_time} WHERE id = ?",
                (workspace_id,)
            )
            await conn.commit()
            return cursor.rowcount > 0


async def get_workspace_integrations(pool, workspace_id: str) -> List[Dict]:
    """Get all workspace integrations from the per-workspace schema."""
    from app.db.workspace_schema import get_workspace_schema_name_from_db
    
    try:
        schema_name = await get_workspace_schema_name_from_db(workspace_id)
        
        # Query per-workspace schema
        query = f"""
            SELECT workspace_integration_id, workspace_id, user_id, integration_display_name, provider, url, extra_config_json, connection_status, added_by_user_id, added_utc
            FROM {schema_name}.workspace_integrations 
            WHERE workspace_id = ? 
            ORDER BY added_utc DESC
        """
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (workspace_id,))
                rows = await cursor.fetchall()
        
        if not rows:
            return []
        
        return [
            {
                "id": str(row[0]),
                "workspace_id": str(row[1]),
                "provider": row[4],
                "external_id": row[3] if row[3] else "",  # integration_display_name as external_id for compatibility
                "display_name": row[3],  # integration_display_name
                "config": row[6],  # extra_config_json
                "linked_at": row[9],  # added_utc
                # Additional fields for new schema
                "user_id": row[2],
                "url": row[5],
                "connection_status": row[7],
                "added_by_user_id": row[8]
            }
            for row in rows
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching workspace integrations for {workspace_id}: {e}", exc_info=True)
        # Return empty list if schema doesn't exist yet or error occurs
        return []


async def create_workspace_integration(
    pool,
    workspace_id: str,
    integration_id: str,
    provider: str,
    integration_display_name: str,
    user_id: Optional[str] = None,
    url: Optional[str] = None,
    extra_config_json: Optional[str] = None,
    added_by_user_id: Optional[str] = None
) -> Dict:
    """Create a workspace integration entry in the per-workspace schema."""
    from app.db.workspace_schema import get_workspace_schema_name_from_db
    
    schema_name = await get_workspace_schema_name_from_db(workspace_id)
    current_time = DBAdapter.get_current_time_sql()
    
    # Build dynamic query for per-workspace schema
    query = f"""
        INSERT INTO {schema_name}.workspace_integrations
        (workspace_integration_id, workspace_id, user_id, integration_display_name, provider, url, extra_config_json, connection_status, added_by_user_id, added_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Connected', ?, {current_time})
    """
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                query,
                (integration_id, workspace_id, user_id, integration_display_name, provider, url, extra_config_json, added_by_user_id)
            )
            await conn.commit()
    
    # Fetch the created record
    fetch_query = f"""
        SELECT workspace_integration_id, workspace_id, user_id, integration_display_name, provider, url, extra_config_json, connection_status, added_by_user_id, added_utc
        FROM {schema_name}.workspace_integrations WHERE workspace_integration_id = ?
    """
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(fetch_query, (integration_id,))
            row = await cursor.fetchone()
    
    if not row:
        return None
    
    return {
        "id": str(row[0]),
        "workspace_id": str(row[1]),
        "user_id": row[2],
        "integration_display_name": row[3],
        "provider": row[4],
        "url": row[5],
        "extra_config_json": row[6],
        "connection_status": row[7],
        "added_by_user_id": row[8],
        "added_utc": row[9]
    }


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
        INSERT INTO pmassist_master.AuditLog
        (id, workspace_id, action, actor_id, details, timestamp)
        VALUES (?, ?, ?, ?, ?, {current_time})
        """,
        (log_id, workspace_id, action, actor_id, details),
        commit=True
    )

