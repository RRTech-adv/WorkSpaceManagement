from fastapi import APIRouter, HTTPException, status, Request, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.token_service import TokenService
from app.schemas.auth_schemas import ValidateTokenResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
token_service = TokenService()

# HTTPBearer for Swagger UI compatibility
security = HTTPBearer(auto_error=False)


@router.post("/validate", response_model=ValidateTokenResponse)
async def validate_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Validate Azure Entra ID JWT token and generate PMA token.
    
    **Usage in Swagger UI:**
    1. Click the "Authorize" button at the top
    2. Enter: `Bearer <your-azure-token>` in the Value field
    3. Click "Authorize"
    4. Then try this endpoint
    
    **Usage with curl:**
    ```bash
    curl -X POST http://localhost:8000/auth/validate \\
      -H "Authorization: Bearer <your-azure-token>"
    ```
    """
    # Try to get token from HTTPBearer (works with Swagger)
    authorization = None
    if credentials:
        authorization = credentials.credentials
        logger.info("Token received via HTTPBearer (Swagger)")
    else:
        # Fallback: get from request headers directly
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            authorization = auth_header.replace("Bearer ", "").strip()
            logger.info("Token received via Authorization header")
    
    # If still no token, check the raw header
    if not authorization:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            authorization = auth_header.replace("Bearer ", "").strip()
            logger.info("Token extracted from Authorization header")
    
    if not authorization:
        logger.warning(f"No authorization token found. Headers: {list(request.headers.keys())}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "MISSING_AUTHORIZATION_HEADER",
                "message": "Authorization header is required. Format: 'Bearer <token>' or use Swagger's Authorize button"
            }
        )
    
    # Log token info (without exposing the actual token)
    logger.info(f"Token received. Length: {len(authorization)} characters")
    
    # Validate token and generate PMA token
    result = await token_service.validate_azure_token_and_generate_pma(authorization)
    
    if not result:
        logger.warning("Token validation failed - invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_VALIDATION_FAILED",
                "message": "Azure token validation failed. Token may be invalid, expired, or misconfigured."
            }
        )
    
    logger.info(f"Token validated successfully for user: {result.get('user_id')}")
    return ValidateTokenResponse(**result)


@router.post("/refresh", response_model=ValidateTokenResponse)
async def refresh_token(
    request: Request,
    azure_credentials: HTTPAuthorizationCredentials = Security(security),
    x_pma_token: str = Header(None, alias="X-PMA-Token", description="Current PMA token to refresh")
):
    """
    Refresh PMA token with updated roles from database.
    
    This endpoint is useful when:
    - User creates a workspace and needs updated roles in their token
    - User is added to a workspace and needs updated roles
    - User's roles have changed and they need a fresh token
    
    **Usage in Swagger UI:**
    1. Click "Authorize" and enter: `Bearer <your-azure-token>`
    2. In the request, add header: `X-PMA-Token: <your-current-pma-token>`
    3. Call this endpoint to get a new PMA token with updated roles
    
    **Usage with curl:**
    ```bash
    curl -X POST http://localhost:8000/auth/refresh \\
      -H "Authorization: Bearer <azure-token>" \\
      -H "X-PMA-Token: <current-pma-token>"
    ```
    """
    # Get Azure token
    azure_token = None
    if azure_credentials:
        azure_token = azure_credentials.credentials
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            azure_token = auth_header.replace("Bearer ", "").strip()
    
    if not azure_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "MISSING_AZURE_TOKEN",
                "message": "Azure token is required in Authorization header"
            }
        )
    
    # Get PMA token
    if not x_pma_token:
        # Try to get from headers directly
        x_pma_token = request.headers.get("X-PMA-Token", "")
    
    if not x_pma_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "MISSING_PMA_TOKEN",
                "message": "Current PMA token is required in X-PMA-Token header"
            }
        )
    
    logger.info("Refreshing PMA token with updated roles from database")
    
    # Refresh token
    result = await token_service.refresh_pma_token(azure_token, x_pma_token)
    
    if not result:
        logger.warning("Token refresh failed - invalid tokens or mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_REFRESH_FAILED",
                "message": "Token refresh failed. Azure token or PMA token may be invalid, expired, or mismatched."
            }
        )
    
    logger.info(f"Token refreshed successfully for user: {result.get('user_id')} with {len(result.get('roles', {}))} workspace(s)")
    return ValidateTokenResponse(**result)

