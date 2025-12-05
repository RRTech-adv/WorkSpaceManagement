# Two-Level Database Schema Migration Guide

## 🎯 Architecture Overview

The database now uses a **two-level architecture**:

1. **Global Schema (`pmassist_master`)**: Shared metadata
2. **Per-Workspace Schema (`ws_<guid>`)**: Tenant-specific data

---

## 📊 Schema Structure

### Global Schema: `pmassist_master`

**Tables:**
- `Workspace` - Updated with new fields
- `WorkspaceMember` - Unchanged
- `AuditLog` - Unchanged (global audit)

**Workspace Table Changes:**
```sql
-- NEW FIELDS:
db_schema_name NVARCHAR(128)    -- Schema name: ws_<guid_no_hyphens>
last_seen_utc DATETIME2          -- Last activity timestamp
status NVARCHAR(50)              -- Active / Archived
```

### Per-Workspace Schema: `ws_<guid_no_hyphens>`

**Tables (in each workspace schema):**
1. `workspace_integrations` - Replaces WorkspaceExternalLink
2. `workspace_agents`
3. `automation_jobs`
4. `automation_job_runs`
5. `file_artifacts`

---

## ✅ Implementation Status

### Completed ✅
1. ✅ Updated `database_schema.sql` with new structure
2. ✅ Created `app/db/workspace_schema.py` for schema creation
3. ✅ Updated workspace creation query to include new fields
4. ✅ Updated all global queries to use `pmassist_master.` prefix

### In Progress ⏳
1. ⏳ Update workspace response to include new fields
2. ⏳ Replace WorkspaceExternalLink queries with per-workspace queries
3. ⏳ Update workspace creation to create per-workspace schema
4. ⏳ Create dynamic schema query helpers

### To Do 📋
1. Update integration service to use per-workspace schema
2. Update workspace service to create schema on creation
3. Update schemas/models to include new fields
4. Test and verify all queries

---

## 🔧 Key Changes Required

### 1. Workspace Creation Flow

**Before:**
```python
1. Create workspace record
2. Add creator as OWNER
3. Done
```

**After:**
```python
1. Generate workspace_id (GUID)
2. Generate schema_name: ws_<guid_no_hyphens>
3. Create workspace record (with db_schema_name)
4. Create per-workspace schema and tables
5. Add creator as OWNER
6. Done
```

### 2. Integration Queries

**Before:**
```python
# Global table
SELECT * FROM WorkspaceExternalLink WHERE workspace_id = ?
```

**After:**
```python
# Per-workspace schema
schema_name = await get_workspace_schema_name_from_db(workspace_id)
query = f"SELECT * FROM {schema_name}.workspace_integrations WHERE workspace_id = ?"
```

### 3. Dynamic Schema Access Pattern

```python
# 1. Get workspace schema name
from app.db.workspace_schema import get_workspace_schema_name_from_db
schema_name = await get_workspace_schema_name_from_db(workspace_id)

# 2. Build dynamic query
query = f"SELECT * FROM {schema_name}.workspace_integrations WHERE provider = ?"

# 3. Execute with proper escaping (SQL injection safe via parameterized queries)
```

---

## 📝 Next Implementation Steps

1. **Update Workspace Response Fields**
   - Add `db_schema_name`, `last_seen_utc`, `status` to all workspace responses

2. **Replace WorkspaceExternalLink Queries**
   - Remove old queries
   - Create new per-workspace integration queries

3. **Update Workspace Service**
   - Add schema creation in `create_workspace()`

4. **Update Integration Service**
   - Use dynamic schema queries

5. **Update Schemas/Models**
   - Add new fields to Pydantic models

---

## 🚨 Important Notes

- **Schema naming**: `ws_<guid_no_hyphens>` (e.g., `ws_123e4567e89b12d3a456426614174000`)
- **Dynamic queries**: Always use parameterized queries (safe from SQL injection)
- **Schema creation**: Must happen during workspace creation
- **Backward compatibility**: Existing workspaces need migration script

---

This is a major architectural change. All changes are documented here for review.

