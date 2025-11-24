"""
Database adapter to handle differences between SQL Server and SQLite.
"""
from app.core.config import settings
from typing import Optional


class DBAdapter:
    """Adapter to handle SQL dialect differences."""
    
    @staticmethod
    def get_current_time_sql() -> str:
        """Get SQL for current timestamp."""
        if settings.db_type.lower() == "sqlite":
            print("SQLite")
            return "datetime('now')"
        else:  # SQL Server
            return "SYSDATETIME()"
    
    @staticmethod
    def get_uuid_type() -> str:
        """Get UUID/GUID column type."""
        if settings.db_type.lower() == "sqlite":
            return "TEXT"
        else:  # SQL Server
            return "UNIQUEIDENTIFIER"
    
    @staticmethod
    def get_boolean_type() -> str:
        """Get boolean column type."""
        if settings.db_type.lower() == "sqlite":
            return "INTEGER"  # SQLite uses INTEGER (0/1) for booleans
        else:  # SQL Server
            return "BIT"
    
    @staticmethod
    def get_text_type(max_length: Optional[int] = None) -> str:
        """Get text column type."""
        if settings.db_type.lower() == "sqlite":
            if max_length:
                return f"TEXT"  # SQLite doesn't enforce length, but we can document it
            return "TEXT"
        else:  # SQL Server
            if max_length:
                return f"NVARCHAR({max_length})"
            return "NVARCHAR(MAX)"
    
    @staticmethod
    def format_boolean(value: bool) -> int:
        """Format boolean value for database."""
        if settings.db_type.lower() == "sqlite":
            return 1 if value else 0
        else:  # SQL Server
            return 1 if value else 0
    
    @staticmethod
    def parse_boolean(value) -> bool:
        """Parse boolean value from database."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

