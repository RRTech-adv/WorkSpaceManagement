from typing import Dict, Optional, Any
from app.core.azure_jwt_validator import AzureJWTValidator
from app.core.security import generate_pma_token
from app.db.connection import get_db_pool
from app.db.queries import get_user_workspace_roles
import uuid


class TokenService:
    """Service for token validation and PMA token generation."""
    
    def __init__(self):
        self.azure_validator = AzureJWTValidator()
    
    async def validate_azure_token_and_generate_pma(
        self, azure_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate Azure token and generate PMA token with workspace roles.
        Returns user info with PMA token.
        """
        # Validate Azure token
        azure_payload = self.azure_validator.validate_token(azure_token)
        if not azure_payload:
            return None
        
        user_id = azure_payload["user_id"]
        email = azure_payload["email"]
        display_name = azure_payload.get("display_name", email)
        
        # Fetch workspace roles from database
        try:
            pool = await get_db_pool()
            roles = await get_user_workspace_roles(pool, user_id)
        except Exception as e:
            # If database query fails, log but continue with empty roles
            # This allows authentication to proceed even if database is unavailable
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to fetch workspace roles from database: {e}. Continuing with empty roles.")
            roles = {}
        
        # Generate PMA token
        pma_token = generate_pma_token(user_id, email, roles)
        
        return {
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "pma_token": pma_token,
            "roles": roles
        }

