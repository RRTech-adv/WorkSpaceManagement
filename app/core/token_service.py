from typing import Dict, Optional, Any
from app.core.azure_jwt_validator import AzureJWTValidator
from app.core.security import generate_pma_token, decode_pma_token
from app.db.connection import get_db_pool
from app.db.queries import get_user_workspace_roles
import uuid
import logging

logger = logging.getLogger(__name__)


class TokenService:
    """Service for token validation and PMA token generation."""
    
    def __init__(self):
        self.azure_validator = AzureJWTValidator()
    
    async def validate_azure_token_and_generate_pma(
        self, azure_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate Azure token and generate PMA token with workspace roles.
        
        Flow:
        1. Validate Azure Entra ID JWT token
        2. Extract user information (user_id, email, display_name)
        3. Fetch user's workspace roles from database
        4. Generate PMA token with roles embedded
        
        Returns user info with PMA token.
        """
        # Step 1: Validate Azure token
        azure_payload = self.azure_validator.validate_token(azure_token)
        if not azure_payload:
            logger.warning("Azure token validation failed")
            return None
        
        # Step 2: Extract user information from validated Azure token
        user_id = azure_payload["user_id"]
        email = azure_payload["email"]
        display_name = azure_payload.get("display_name", email)
        logger.info(f"Azure token validated for user: {user_id} ({email})")
        
        # Step 3: Fetch workspace roles from database (after token validation, before PMA token creation)
        try:
            pool = await get_db_pool()
            roles = await get_user_workspace_roles(pool, user_id)
            logger.info(f"Fetched roles from database for user {user_id}: {len(roles)} workspace(s)")
        except Exception as e:
            # If database query fails, log but continue with empty roles
            # This allows authentication to proceed even if database is unavailable
            logger.warning(f"Failed to fetch workspace roles from database: {e}. Continuing with empty roles.")
            roles = {}
        
        # Step 4: Generate PMA token with roles embedded
        pma_token = generate_pma_token(user_id, email, roles)
        logger.info(f"Generated PMA token for user {user_id} with {len(roles)} workspace role(s)")
        
        return {
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "pma_token": pma_token,
            "roles": roles
        }
    
    async def refresh_pma_token(
        self, azure_token: str, current_pma_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh PMA token with updated roles from database.
        Validates both Azure token and current PMA token, then generates new PMA token with fresh roles.
        """
        # Validate Azure token
        azure_payload = self.azure_validator.validate_token(azure_token)
        if not azure_payload:
            return None
        
        # Validate current PMA token
        pma_payload = decode_pma_token(current_pma_token)
        if not pma_payload:
            return None
        
        # Verify user_id matches between tokens
        if azure_payload["user_id"] != pma_payload["user_id"]:
            logger.warning(f"Token user mismatch: Azure user_id={azure_payload['user_id']}, PMA user_id={pma_payload['user_id']}")
            return None
        
        user_id = azure_payload["user_id"]
        email = azure_payload["email"]
        display_name = azure_payload.get("display_name", email)
        
        # Fetch fresh workspace roles from database
        try:
            pool = await get_db_pool()
            roles = await get_user_workspace_roles(pool, user_id)
            logger.info(f"Refreshed roles for user {user_id}: {len(roles)} workspace(s)")
        except Exception as e:
            logger.error(f"Failed to fetch workspace roles from database: {e}")
            # If database query fails, use existing roles from current token as fallback
            roles = pma_payload.get("roles", {})
            logger.warning(f"Using existing roles from token as fallback: {len(roles)} workspace(s)")
        
        # Generate new PMA token with fresh roles
        pma_token = generate_pma_token(user_id, email, roles)
        
        return {
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "pma_token": pma_token,
            "roles": roles
        }

