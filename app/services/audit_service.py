from typing import Optional
import uuid
import json
from app.db.connection import get_db_pool
from app.db.queries import create_audit_log


class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    async def log_action(
        workspace_id: str,
        action: str,
        actor_id: str,
        details: Optional[dict] = None
    ):
        """Log an action to the audit log."""
        pool = await get_db_pool()
        log_id = str(uuid.uuid4())
        details_json = json.dumps(details) if details else None
        
        await create_audit_log(
            pool,
            log_id,
            workspace_id,
            action,
            actor_id,
            details_json
        )

