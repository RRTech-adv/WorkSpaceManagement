from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt
from app.core.config import settings


def generate_pma_token(user_id: str, email: str, roles: Dict[str, str]) -> str:
    """Generate PM Assist token with user info and workspace roles."""
    payload = {
        "user_id": user_id,
        "email": email,
        "roles": roles,
        "exp": datetime.utcnow() + timedelta(hours=settings.pma_token_expiry_hours),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.pma_token_secret, algorithm="HS256")


def decode_pma_token(token: str) -> Optional[Dict]:
    """Decode and validate PM Assist token."""
    try:
        payload = jwt.decode(
            token,
            settings.pma_token_secret,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_role_for_workspace(workspace_id: str, roles: Dict[str, str]) -> Optional[str]:
    """Get role for a specific workspace from roles dict."""
    return roles.get(workspace_id)

