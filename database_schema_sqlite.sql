-- PM Assist Database Schema
-- SQLite3

-- Workspace Table
CREATE TABLE IF NOT EXISTS Workspace (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    blob_path TEXT,
    is_active INTEGER DEFAULT 1
);

-- WorkspaceMember Table
CREATE TABLE IF NOT EXISTS WorkspaceMember (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL,
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- WorkspaceExternalLink Table
CREATE TABLE IF NOT EXISTS WorkspaceExternalLink (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    display_name TEXT,
    config TEXT,
    linked_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- AuditLog Table
CREATE TABLE IF NOT EXISTS AuditLog (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    details TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS IX_WorkspaceMember_WorkspaceId ON WorkspaceMember(workspace_id);
CREATE INDEX IF NOT EXISTS IX_WorkspaceMember_UserId ON WorkspaceMember(user_id);
CREATE INDEX IF NOT EXISTS IX_WorkspaceExternalLink_WorkspaceId ON WorkspaceExternalLink(workspace_id);
CREATE INDEX IF NOT EXISTS IX_AuditLog_WorkspaceId ON AuditLog(workspace_id);
CREATE INDEX IF NOT EXISTS IX_AuditLog_Timestamp ON AuditLog(timestamp);

