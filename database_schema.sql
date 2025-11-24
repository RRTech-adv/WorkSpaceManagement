-- PM Assist Database Schema
-- SQL Server (T-SQL)

-- Workspace Table
CREATE TABLE Workspace (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    created_by NVARCHAR(200) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 DEFAULT SYSDATETIME(),
    blob_path NVARCHAR(500),
    is_active BIT DEFAULT 1
);

-- WorkspaceMember Table
CREATE TABLE WorkspaceMember (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    user_id NVARCHAR(200) NOT NULL,
    display_name NVARCHAR(200),
    role NVARCHAR(50) NOT NULL,
    added_at DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_WorkspaceMember_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- WorkspaceExternalLink Table
CREATE TABLE WorkspaceExternalLink (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    provider NVARCHAR(50) NOT NULL,
    external_id NVARCHAR(255) NOT NULL,
    display_name NVARCHAR(255),
    config NVARCHAR(MAX),
    linked_at DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_WorkspaceExternalLink_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- AuditLog Table
CREATE TABLE AuditLog (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    workspace_id UNIQUEIDENTIFIER NOT NULL,
    action NVARCHAR(255) NOT NULL,
    actor_id NVARCHAR(200) NOT NULL,
    details NVARCHAR(MAX) NULL,
    timestamp DATETIME2 DEFAULT SYSDATETIME(),
    CONSTRAINT FK_AuditLog_Workspace FOREIGN KEY (workspace_id) REFERENCES Workspace(id)
);

-- Indexes for performance
CREATE INDEX IX_WorkspaceMember_WorkspaceId ON WorkspaceMember(workspace_id);
CREATE INDEX IX_WorkspaceMember_UserId ON WorkspaceMember(user_id);
CREATE INDEX IX_WorkspaceExternalLink_WorkspaceId ON WorkspaceExternalLink(workspace_id);
CREATE INDEX IX_AuditLog_WorkspaceId ON AuditLog(workspace_id);
CREATE INDEX IX_AuditLog_Timestamp ON AuditLog(timestamp);

