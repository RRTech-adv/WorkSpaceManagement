-- PM Assist Database Schema
-- SQL Server (T-SQL)
-- Two-Level Architecture: Global Schema (pmassist_master) + Per-Workspace Schemas

-- ============================================
-- GLOBAL SCHEMA: pmassist_master
-- ============================================

-- Create global schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'pmassist_master')
BEGIN
    EXEC('CREATE SCHEMA pmassist_master')
END
GO

-- Workspace Table (Updated with new fields)
CREATE TABLE pmassist_master.Workspace (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    created_by NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    blob_path NVARCHAR(500),
    is_active BIT DEFAULT 1,
    db_schema_name NVARCHAR(128) NULL,  -- NEW: Schema name for this workspace (e.g., 'ws_abc123...')
    last_seen_utc DATETIME2 NULL,       -- NEW: Last activity timestamp
    status NVARCHAR(50) DEFAULT 'Active' -- NEW: Active / Archived
);

-- WorkspaceMember Table (Unchanged)
CREATE TABLE pmassist_master.WorkspaceMember (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    user_id NVARCHAR(200) NOT NULL,
    display_name NVARCHAR(200),
    role NVARCHAR(50) NOT NULL,
    added_at DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_WorkspaceMember_Workspace FOREIGN KEY (workspace_id) REFERENCES pmassist_master.Workspace(id)
);

-- AuditLog Table (Unchanged - Global audit)
CREATE TABLE pmassist_master.AuditLog (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    action NVARCHAR(255) NOT NULL,
    actor_id NVARCHAR(255) NOT NULL,
    details NVARCHAR(MAX) NULL,
    timestamp DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_AuditLog_Workspace FOREIGN KEY (workspace_id) REFERENCES pmassist_master.Workspace(id)
);

-- Indexes for performance
CREATE INDEX IX_WorkspaceMember_WorkspaceId ON pmassist_master.WorkspaceMember(workspace_id);
CREATE INDEX IX_WorkspaceMember_UserId ON pmassist_master.WorkspaceMember(user_id);
CREATE INDEX IX_AuditLog_WorkspaceId ON pmassist_master.AuditLog(workspace_id);
CREATE INDEX IX_AuditLog_Timestamp ON pmassist_master.AuditLog(timestamp);
CREATE INDEX IX_Workspace_Status ON pmassist_master.Workspace(status);
CREATE INDEX IX_Workspace_DbSchemaName ON pmassist_master.Workspace(db_schema_name);

GO

-- ============================================
-- PER-WORKSPACE SCHEMA TEMPLATE
-- ============================================
-- Note: This template shows the structure for per-workspace schemas
-- Actual schemas are created dynamically: CREATE SCHEMA ws_<guid_no_hyphens>
-- See app/db/workspace_schema.py for the creation function
--
