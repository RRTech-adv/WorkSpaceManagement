# Complete Flow: GET /workspaces/{id}

This document explains exactly what happens when you query `GET /workspaces/{workspace_id}`.

---

## Request

```http
GET /workspaces/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer <azure-token>
X-PMA-Token: <pma-token>
```

---

## Step-by-Step Flow

### Step 1: Request Arrives at FastAPI

```
Request → FastAPI Application
```

### Step 2: AuthMiddleware Intercepts (Before Endpoint)

**Location:** `app/core/middleware.py` → `AuthMiddleware.dispatch()`

#### 2.1: Check Excluded Paths
```python
# Path is NOT excluded, so continue with auth
exclude_paths = ["/docs", "/openapi.json", "/redoc", "/health", "/auth/validate", "/db"]
# /workspaces/{id} is NOT in exclude_paths → Continue
```

#### 2.2: Extract Tokens from Headers
```python
azure_token = request.headers.get("Authorization", "").replace("Bearer ", "")
pma_token = request.headers.get("X-PMA-Token", "")

# If either missing → 401 Unauthorized
```

#### 2.3: Validate Azure Token
```python
azure_payload = self.azure_validator.validate_token(azure_token)
# - Validates signature with Azure JWKS
# - Checks expiration
# - Verifies audience and issuer
# If invalid → 401 Unauthorized
```

#### 2.4: Validate PMA Token
```python
pma_payload = decode_pma_token(pma_token)
# - Decodes with PMA_TOKEN_SECRET
# - Checks expiration
# - Returns payload with ALL roles
# If invalid → 401 Unauthorized
```

**Decoded PMA Token:**
```python
pma_payload = {
    "user_id": "user-123",
    "email": "user@example.com",
    "roles": {
        "workspace-123": "OWNER",
        "workspace-456": "ADMIN",
        "workspace-789": "MEMBER"
    },
    "exp": 1234567890,
    "iat": 1234567800
}
```

#### 2.5: Verify User ID Match
```python
if azure_payload["user_id"] != pma_payload["user_id"]:
    # → 401 Unauthorized (TOKEN_MISMATCH)
```

#### 2.6: Extract Workspace ID from URL
```python
path = "/workspaces/123e4567-e89b-12d3-a456-426614174000"
path_parts = ["workspaces", "123e4567-e89b-12d3-a456-426614174000"]

idx = path_parts.index("workspaces")  # 0
workspace_id = path_parts[idx + 1]   # "123e4567-e89b-12d3-a456-426614174000"

# Validate GUID format (length check)
if len(workspace_id) == 36:
    # Valid GUID format
```

#### 2.7: Look Up Role in Token
```python
roles = pma_payload.get("roles", {})
# roles = {
#     "workspace-123": "OWNER",
#     "workspace-456": "ADMIN",
#     "workspace-789": "MEMBER"
# }

role_for_workspace = roles.get(workspace_id)
# If workspace_id = "123e4567-e89b-12d3-a456-426614174000"
# role_for_workspace = "OWNER" (if found) or None (if not found)
```

#### 2.8: Auto-Refresh Roles if Missing (Fallback)
```python
if not role_for_workspace:
    # Role not in token, query database
    pool = await get_db_pool()
    fresh_roles = await get_user_workspace_roles(pool, user_id)
    
    if fresh_roles:
        roles.update(fresh_roles)  # Update roles dict
        role_for_workspace = fresh_roles.get(workspace_id)
        # If found → Continue
        # If still not found → Will fail in require_role()
```

#### 2.9: Attach User Context to Request
```python
request.state.user = CurrentUserContext(
    user_id="user-123",
    email="user@example.com",
    roles={
        "workspace-123": "OWNER",
        "workspace-456": "ADMIN",
        "workspace-789": "MEMBER"
    },
    role_for_workspace="OWNER"  # Role for the requested workspace
)
```

### Step 3: require_role("VIEWER") Dependency Executes

**Location:** `app/core/middleware.py` → `require_role()`

**Endpoint:** `GET /workspaces/{id}` requires `require_role("VIEWER")`

```python
async def role_checker(request: Request) -> CurrentUserContext:
    user: CurrentUserContext = request.state.user
    
    # Check 1: User has role for workspace?
    if not user.role_for_workspace:
        # → 403 Forbidden (USER_NOT_AUTHORIZED)
        # "You do not have access to this workspace"
    
    # Check 2: Role level sufficient?
    role_hierarchy = {"VIEWER": 0, "MEMBER": 1, "ADMIN": 2, "OWNER": 3}
    user_role_level = role_hierarchy.get(user.role_for_workspace, -1)
    required_level = role_hierarchy.get("VIEWER", 0)  # 0
    
    if user_role_level < required_level:
        # → 403 Forbidden (INSUFFICIENT_PERMISSIONS)
        # "Requires VIEWER role or higher"
    
    # User has sufficient permissions → Continue
    return user
```

**Example Scenarios:**

| User Role | Required | Result |
|-----------|----------|--------|
| OWNER | VIEWER | ✅ Allowed (3 >= 0) |
| ADMIN | VIEWER | ✅ Allowed (2 >= 0) |
| MEMBER | VIEWER | ✅ Allowed (1 >= 0) |
| VIEWER | VIEWER | ✅ Allowed (0 >= 0) |
| None | VIEWER | ❌ 403 Forbidden |

### Step 4: Endpoint Handler Executes

**Location:** `app/api/workspaces.py` → `get_workspace()`

```python
@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str = Path(..., description="Workspace ID"),
    request: Request = None,
    user: CurrentUserContext = Depends(require_role("VIEWER"))
):
    """Get workspace details."""
    # user is guaranteed to have at least VIEWER role here
    
    workspace = await workspace_service.get_workspace(workspace_id)
    
    if not workspace:
        # → 404 Not Found (WORKSPACE_NOT_FOUND)
    
    return WorkspaceResponse(**workspace)
```

### Step 5: WorkspaceService.get_workspace() Executes

**Location:** `app/services/workspace_service.py` → `get_workspace()`

```python
async def get_workspace(self, workspace_id: str) -> Optional[Dict]:
    """Get workspace by ID."""
    pool = await get_db_pool()
    
    # Query 1: Get workspace details
    workspace = await get_workspace_by_id(pool, workspace_id)
    # SQL: SELECT id, name, description, created_by, created_at, 
    #           updated_at, blob_path, is_active
    #      FROM Workspace 
    #      WHERE id = ? AND is_active = 1
    
    if workspace:
        # Query 2: Get members
        members = await get_workspace_members(pool, workspace_id)
        workspace["members"] = members
        
        # Query 3: Get external links
        links = await get_workspace_external_links(pool, workspace_id)
        workspace["external_links"] = links
    
    return workspace
```

**Database Queries:**

1. **Get Workspace:**
   ```sql
   SELECT id, name, description, created_by, created_at, 
          updated_at, blob_path, is_active
   FROM Workspace 
   WHERE id = ? AND is_active = 1
   ```

2. **Get Members:**
   ```sql
   SELECT id, workspace_id, user_id, display_name, role, added_at
   FROM WorkspaceMember
   WHERE workspace_id = ?
   ```

3. **Get External Links:**
   ```sql
   SELECT id, workspace_id, link_type, link_url, created_at
   FROM WorkspaceExternalLink
   WHERE workspace_id = ?
   ```

### Step 6: Response Returned

**Response Structure:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Workspace",
  "description": "Workspace description",
  "created_by": "user-123",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "blob_path": "workspaces/123e4567-e89b-12d3-a456-426614174000",
  "is_active": true,
  "members": [
    {
      "id": "member-123",
      "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "user-123",
      "display_name": "User Name",
      "role": "OWNER",
      "added_at": "2024-01-01T00:00:00"
    }
  ],
  "external_links": []
}
```

---

## Possible Outcomes

### ✅ Success (200 OK)
- Both tokens valid
- User has role for workspace (at least VIEWER)
- Workspace exists and is active
- Returns workspace details with members and links

### ❌ 401 Unauthorized
- Missing Azure token
- Missing PMA token
- Invalid/expired Azure token
- Invalid/expired PMA token
- Token user mismatch

### ❌ 403 Forbidden
- User not a member of workspace (`role_for_workspace` is None)
- User role level insufficient (though VIEWER is minimum, so unlikely)

### ❌ 404 Not Found
- Workspace doesn't exist
- Workspace is soft-deleted (`is_active = 0`)

### ❌ 500 Internal Server Error
- Database connection failure
- Query execution error

---

## Key Points

1. **Authentication happens first** - Both tokens validated before endpoint
2. **Role lookup** - Middleware extracts workspace_id and looks up role
3. **Auto-refresh** - If role not in token, database is queried automatically
4. **Authorization check** - `require_role("VIEWER")` ensures user has access
5. **Database queries** - 3 queries: workspace, members, external links
6. **Response** - Complete workspace details with related data

---

## Flow Diagram

```
Request: GET /workspaces/{id}
    │
    ├─→ AuthMiddleware
    │   ├─→ Validate Azure Token
    │   ├─→ Validate PMA Token
    │   ├─→ Extract workspace_id from URL
    │   ├─→ Look up role in token
    │   ├─→ (If missing) Query database for roles
    │   └─→ Attach user context
    │
    ├─→ require_role("VIEWER")
    │   ├─→ Check user has role for workspace
    │   └─→ Check role level >= VIEWER
    │
    ├─→ get_workspace() endpoint
    │   └─→ WorkspaceService.get_workspace()
    │       ├─→ Query workspace
    │       ├─→ Query members
    │       └─→ Query external links
    │
    └─→ Response: WorkspaceResponse
```

---

## Example Scenarios

### Scenario 1: User has OWNER role in token
```
Token roles: {"workspace-123": "OWNER"}
Request: GET /workspaces/workspace-123
→ Role found in token: "OWNER"
→ require_role("VIEWER") passes (OWNER >= VIEWER)
→ Returns workspace details
```

### Scenario 2: User just created workspace (role not in token yet)
```
Token roles: {"workspace-456": "ADMIN"}  # Old token
Request: GET /workspaces/workspace-789  # Newly created workspace
→ Role not found in token
→ Middleware queries database
→ Database returns: {"workspace-789": "OWNER"}
→ Role found: "OWNER"
→ require_role("VIEWER") passes
→ Returns workspace details
```

### Scenario 3: User not a member
```
Token roles: {"workspace-123": "OWNER"}
Request: GET /workspaces/workspace-999  # Different workspace
→ Role not found in token
→ Middleware queries database
→ Database returns: {} (no role for this workspace)
→ role_for_workspace = None
→ require_role("VIEWER") fails
→ 403 Forbidden: "You do not have access to this workspace"
```

