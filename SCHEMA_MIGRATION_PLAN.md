# Database Schema Migration Plan - Two-Level Architecture

## 🎯 Overview

Migrating from single global schema to two-level architecture:
- **Global Schema (pmassist_master)**: Workspace, WorkspaceMember, AuditLog
- **Per-Workspace Schema (ws_<guid>)**: workspace_integrations, workspace_agents, automation_jobs, etc.

## ✅ Completed Changes

### 1. Schema Files
- ✅ Updated `database_schema.sql` with pmassist_master schema
- ✅ Created `app/db/workspace_schema.py` for per-workspace schema creation

### 2. Query Updates (In Progress)
- ✅ Updated `create_workspace()` to include new fields (db_schema_name, status, last_seen_utc)
- ✅ Updated all queries to use `pmassist_master.` prefix
- ⏳ Need to: Remove WorkspaceExternalLink queries
- ⏳ Need to: Create per-workspace integration queries

## 📋 Remaining Tasks

### 1. Update Workspace Queries Response
- Add new fields to workspace response: `db_schema_name`, `last_seen_utc`, `status`

### 2. Remove WorkspaceExternalLink Queries
- Remove `create_external_link()`
- Remove `get_workspace_external_links()`

### 3. Create Per-Workspace Integration Queries
- Create `create_workspace_integration()` - uses dynamic schema
- Create `get_workspace_integrations()` - uses dynamic schema

### 4. Update Workspace Service
- Add schema creation step in `create_workspace()`
- Update to use new integration queries

### 5. Update Integration Service
- Update to use per-workspace schema queries

## 🔧 Key Implementation Details

### Schema Name Generation
```python
# Format: ws_<guid_no_hyphens>
workspace_id = "123e4567-e89b-12d3-a456-426614174000"
schema_name = "ws_123e4567e89b12d3a456426614174000"
```

### Dynamic Schema Queries
```python
# Get schema name
schema_name = await get_workspace_schema_name_from_db(workspace_id)

# Query in per-workspace schema
query = f"SELECT * FROM {schema_name}.workspace_integrations WHERE provider = ?"
```

### Workspace Creation Flow
1. Create workspace record in pmassist_master.Workspace
2. Generate schema name (ws_<guid>)
3. Create schema: `CREATE SCHEMA ws_<guid>`
4. Create tables in schema
5. Update workspace record with db_schema_name

