from typing import Optional, Dict
import jwt
from jwt import PyJWKClient
from app.core.config import settings


class AzureJWTValidator:
    """Validates Azure Entra ID JWT tokens."""
    
    def __init__(self):
        self.jwks_url = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(self.jwks_url)
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate Azure Entra ID JWT token.
        Returns decoded payload if valid, None otherwise.
        """
        try:
            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.azure_audience,
                issuer=f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0"
            )
            
            return {
                "user_id": payload.get("oid") or payload.get("sub"),
                "email": payload.get("email") or payload.get("preferred_username"),
                "display_name": payload.get("name"),
                "roles": payload.get("roles", [])
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

