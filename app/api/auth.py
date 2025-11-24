from fastapi import APIRouter, HTTPException, status, Header
from app.core.token_service import TokenService
from app.schemas.auth_schemas import ValidateTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
token_service = TokenService()


@router.post("/validate", response_model=ValidateTokenResponse)
async def validate_token(
    authorization: str = Header(..., description="Bearer <AzureEntraToken>")
):
    """
    Validate Azure Entra ID JWT token and generate PMA token.
    """
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_AUTHORIZATION_HEADER",
                "message": "Authorization header must start with 'Bearer '"
            }
        )
    
    azure_token = authorization.replace("Bearer ", "")
    
    result = await token_service.validate_azure_token_and_generate_pma(azure_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_VALIDATION_FAILED",
                "message": "Azure token validation failed"
            }
        )
    
    return ValidateTokenResponse(**result)

