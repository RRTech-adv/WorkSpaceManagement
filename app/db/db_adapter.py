"""
Database adapter for SQL Server.
"""
from typing import Optional


class DBAdapter:
    """Adapter for SQL Server SQL dialect."""
    
    @staticmethod
    def get_current_time_sql() -> str:
        """Get SQL for current timestamp."""
        return "SYSDATETIME()"
    
    @staticmethod
    def get_uuid_type() -> str:
        """Get UUID/GUID column type."""
        return "UNIQUEIDENTIFIER"
    
    @staticmethod
    def get_boolean_type() -> str:
        """Get boolean column type."""
        return "BIT"
    
    @staticmethod
    def get_text_type(max_length: Optional[int] = None) -> str:
        """Get text column type."""
        if max_length:
            return f"NVARCHAR({max_length})"
        return "NVARCHAR(MAX)"
    
    @staticmethod
    def format_boolean(value: bool) -> int:
        """Format boolean value for database."""
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

