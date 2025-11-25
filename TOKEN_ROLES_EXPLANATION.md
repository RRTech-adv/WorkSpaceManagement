# PMA Token Roles - Complete Explanation

## Yes! PMA Token Contains ALL Roles

The PMA token is created with **ALL workspace roles** for the user, and when decoded, you get **ALL roles** back.

---

## 1. Token Creation (Encoding)

### When Token is Generated

**Location:** `app/core/security.py` → `generate_pma_token()`

```python
def generate_pma_token(user_id: str, email: str, roles: Dict[str, str]) -> str:
    """Generate PM Assist token with user info and workspace roles."""
    payload = {
        "user_id": user_id,
        "email": email,
        "roles": roles,  # ← ALL roles embedded here
        "exp": datetime.utcnow() + timedelta(hours=settings.pma_token_expiry_hours),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.pma_token_secret, algorithm="HS256")
```

### Roles Structure

The `roles` parameter is a dictionary where:
- **Key:** `workspace_id` (string, GUID)
- **Value:** `role` (string: "OWNER", "ADMIN", "MEMBER", or "VIEWER")

**Example:**
```python
roles = {
    "workspace-123-uuid": "OWNER",
    "workspace-456-uuid": "ADMIN",
    "workspace-789-uuid": "MEMBER",
    "workspace-abc-uuid": "VIEWER"
}
```

### Where Roles Come From

**Location:** `app/core/token_service.py` → `validate_azure_token_and_generate_pma()`

```python
# Step 3: Fetch workspace roles from database
pool = await get_db_pool()
roles = await get_user_workspace_roles(pool, user_id)
# Returns: Dict[str, str] = {workspace_id: role, ...}

# Step 4: Generate PMA token with ALL roles embedded
pma_token = generate_pma_token(user_id, email, roles)
```

**Database Query:** `app/db/queries.py` → `get_user_workspace_roles()`

```sql
SELECT workspace_id, role 
FROM WorkspaceMember 
WHERE user_id = ?
```

This returns **ALL** workspace memberships for the user.

---

## 2. Token Decoding (Getting All Roles Back)

### When Token is Decoded

**Location:** `app/core/security.py` → `decode_pma_token()`

```python
def decode_pma_token(token: str) -> Optional[Dict]:
    """Decode and validate PM Assist token."""
    try:
        payload = jwt.decode(
            token,
            settings.pma_token_secret,
            algorithms=["HS256"]
        )
        return payload  # ← Contains ALL roles
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### Decoded Payload Structure

```python
payload = {
    "user_id": "user-123",
    "email": "user@example.com",
    "roles": {                    # ← ALL roles are here
        "workspace-123-uuid": "OWNER",
        "workspace-456-uuid": "ADMIN",
        "workspace-789-uuid": "MEMBER"
    },
    "exp": 1234567890,
    "iat": 1234567800
}

# Extract all roles
all_roles = payload.get("roles", {})  # Dict[str, str]
```

---

## 3. Usage in Middleware

**Location:** `app/core/middleware.py` → `AuthMiddleware.dispatch()`

```python
# Validate PMA token
pma_payload = decode_pma_token(pma_token)

# Get ALL roles from decoded token
roles = pma_payload.get("roles", {})  # ← All roles extracted here

# Example: roles = {
#     "workspace-123": "OWNER",
#     "workspace-456": "ADMIN",
#     "workspace-789": "MEMBER"
# }

# Then look up specific workspace role
workspace_id = "workspace-123"
role_for_workspace = roles.get(workspace_id)  # Returns "OWNER"
```

---

## 4. Complete Flow Example

### Scenario: User has 3 workspaces

**Step 1: Database Query**
```python
# Query: SELECT workspace_id, role FROM WorkspaceMember WHERE user_id = 'user-123'
# Returns:
[
    ("workspace-123-uuid", "OWNER"),
    ("workspace-456-uuid", "ADMIN"),
    ("workspace-789-uuid", "MEMBER")
]
```

**Step 2: Convert to Dictionary**
```python
roles = {
    "workspace-123-uuid": "OWNER",
    "workspace-456-uuid": "ADMIN",
    "workspace-789-uuid": "MEMBER"
}
```

**Step 3: Embed in Token**
```python
payload = {
    "user_id": "user-123",
    "email": "user@example.com",
    "roles": {                    # ← ALL 3 workspaces embedded
        "workspace-123-uuid": "OWNER",
        "workspace-456-uuid": "ADMIN",
        "workspace-789-uuid": "MEMBER"
    },
    "exp": ...,
    "iat": ...
}
pma_token = jwt.encode(payload, secret, algorithm="HS256")
```

**Step 4: Decode Token (Later)**
```python
decoded = decode_pma_token(pma_token)
all_roles = decoded.get("roles", {})

# all_roles = {
#     "workspace-123-uuid": "OWNER",
#     "workspace-456-uuid": "ADMIN",
#     "workspace-789-uuid": "MEMBER"
# }

# Get role for specific workspace
role = all_roles.get("workspace-123-uuid")  # Returns "OWNER"
```

---

## 5. Key Points

✅ **YES** - PMA token is created with **ALL roles** (all workspace memberships)

✅ **YES** - When decoding, you get **ALL roles** back as a dictionary

✅ **Structure:** `Dict[str, str]` = `{workspace_id: role, ...}`

✅ **Access:** Use `roles.get(workspace_id)` to get role for a specific workspace

✅ **All roles available:** You can iterate over all workspaces:
```python
for workspace_id, role in roles.items():
    print(f"Workspace {workspace_id}: {role}")
```

---

## 6. Token Size Consideration

**Note:** If a user has many workspaces (e.g., 100+), the token will be larger. However:
- JWT tokens are typically small enough for HTTP headers
- Most users won't have 100+ workspaces
- The convenience of having all roles in the token outweighs the size

**Example token size:**
- 3 workspaces: ~500-800 bytes
- 10 workspaces: ~1-2 KB
- 50 workspaces: ~5-10 KB

All well within HTTP header limits (typically 8-16 KB).

---

## Summary

| Question | Answer |
|----------|--------|
| Is PMA token created with all roles? | ✅ **YES** - All workspace roles are embedded |
| Do we get all roles when decoding? | ✅ **YES** - `payload.get("roles")` returns all roles |
| Structure | `Dict[str, str]` = `{workspace_id: role}` |
| Access method | `roles.get(workspace_id)` for specific workspace |
| Can iterate all? | ✅ **YES** - `for workspace_id, role in roles.items()` |

