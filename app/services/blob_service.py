from azure.storage.blob import BlobServiceClient
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BlobService:
    """Service for Azure Blob Storage operations."""
    
    def __init__(self):
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.container_name = settings.azure_storage_container_name or "workspaces"
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of blob service client."""
        if self._initialized:
            return
        
        if settings.azure_storage_connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
                self._initialized = True
                logger.info("Blob service initialized with connection string")
            except Exception as e:
                logger.warning(f"Failed to initialize blob service with connection string: {e}")
                self.blob_service_client = None
        elif settings.azure_storage_account_name:
            try:
                # Use Azure Identity if connection string not provided
                from azure.identity import DefaultAzureCredential
                account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential
                )
                self._initialized = True
                logger.info("Blob service initialized with Azure Identity")
            except Exception as e:
                logger.warning(f"Failed to initialize blob service with Azure Identity: {e}")
                self.blob_service_client = None
        else:
            logger.warning("Blob storage not configured. Blob operations will be unavailable.")
            self.blob_service_client = None
            self._initialized = True  # Mark as initialized to avoid repeated warnings
    
    async def create_workspace_folders(self, workspace_id: str) -> str:
        """
        Create folder structure for a workspace.
        Returns the blob path.
        """
        self._ensure_initialized()
        
        if not self.blob_service_client:
            logger.warning("Blob storage not configured. Returning path without creating folders.")
            return f"workspaces/{workspace_id}"
        
        blob_path = f"workspaces/{workspace_id}"
        folders = ["documents", "attachments", "logs"]
        
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # Create container if it doesn't exist
            try:
                container_client.create_container()
            except Exception:
                pass  # Container may already exist
            
            # Create placeholder files to represent folders
            for folder in folders:
                blob_name = f"{blob_path}/{folder}/.keep"
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(".", overwrite=True)
            
            return blob_path
        except Exception as e:
            logger.error(f"Error creating workspace folders: {e}")
            # Return path anyway so workspace creation can continue
            return blob_path

