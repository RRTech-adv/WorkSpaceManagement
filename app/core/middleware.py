from typing import Optional, Dict
from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.azure_jwt_validator import AzureJWTValidator
from app.core.security import decode_pma_token, get_role_for_workspace


class CurrentUserContext:
    """Context object attached to request.state."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        roles: Dict[str, str],
        role_for_workspace: Optional[str] = None
    ):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.role_for_workspace = role_for_workspace


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Azure and PMA tokens."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.azure_validator = AzureJWTValidator()
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc", "/health", "/auth/validate", "/db"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get tokens from headers
        azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        pma_token = request.headers.get("X-PMA-Token", "")
        
        if not azure_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "MISSING_AZURE_TOKEN", "message": "Azure token is required"}
            )
        
        if not pma_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "MISSING_PMA_TOKEN", "message": "PMA token is required"}
            )
        
        # Validate Azure token
        azure_payload = self.azure_validator.validate_token(azure_token)
        if not azure_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "INVALID_AZURE_TOKEN", "message": "Azure token is invalid or expired"}
            )
        
        # Validate PMA token
        pma_payload = decode_pma_token(pma_token)
        if not pma_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "INVALID_PMA_TOKEN", "message": "PMA token is invalid or expired"}
            )
        
        # Verify user_id matches
        if azure_payload["user_id"] != pma_payload["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "TOKEN_MISMATCH", "message": "Token user mismatch"}
            )
        
        # Extract workspace_id from path if present
        workspace_id = None
        role_for_workspace = None
        
        # Try to extract workspace_id from path
        # Handles patterns like: /workspaces/{id}, /workspaces/{id}/members, etc.
        path_parts = [p for p in request.url.path.split("/") if p]
        if "workspaces" in path_parts:
            try:
                idx = path_parts.index("workspaces")
                if idx + 1 < len(path_parts):
                    workspace_id = path_parts[idx + 1]
                    # Validate it's a GUID format (basic check)
                    if len(workspace_id) == 36:  # GUID length
                        role_for_workspace = get_role_for_workspace(
                            workspace_id,
                            pma_payload.get("roles", {})
                        )
            except (ValueError, IndexError):
                pass
        
        # Attach context to request
        request.state.user = CurrentUserContext(
            user_id=pma_payload["user_id"],
            email=pma_payload["email"],
            roles=pma_payload.get("roles", {}),
            role_for_workspace=role_for_workspace
        )
        
        return await call_next(request)


def require_role(min_role: str = "VIEWER"):
    """
    FastAPI dependency to check if user has required role for workspace.
    Role hierarchy: VIEWER < MEMBER < ADMIN < OWNER
    Usage: Depends(require_role("ADMIN"))
    """
    role_hierarchy = {"VIEWER": 0, "MEMBER": 1, "ADMIN": 2, "OWNER": 3}
    
    async def role_checker(request: Request) -> CurrentUserContext:
        if not hasattr(request.state, "user"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "UNAUTHORIZED", "message": "User context not found"}
            )
        
        user: CurrentUserContext = request.state.user
        
        if not user.role_for_workspace:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "USER_NOT_AUTHORIZED",
                    "message": "You do not have access to this workspace"
                }
            )
        
        user_role_level = role_hierarchy.get(user.role_for_workspace, -1)
        required_level = role_hierarchy.get(min_role, 0)
        
        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Requires {min_role} role or higher"
                }
            )
        
        return user
    
    return role_checker

