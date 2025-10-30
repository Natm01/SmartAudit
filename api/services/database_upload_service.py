# services/database_upload_service.py
"""
Database Upload Service - Handles uploading accounting data to SQL Server
"""
import logging
from typing import Dict, Any, Optional

from services.accounting_loader_prod import AccountingDataLoader

logger = logging.getLogger(__name__)


class DatabaseUploadService:
    """Service to handle database uploads for accounting data"""

    def __init__(self):
        pass

    async def upload_to_database(
        self,
        execution_id: str,
        auth_user_id: int
    ) -> Dict[str, Any]:
        """
        Upload accounting data to SQL Server database.

        This method executes 3 stored procedures:
        1. staging.sp_load_journal_entries_csv_from_blob
        2. staging.sp_load_journal_entry_lines_csv_from_blob
        3. staging.sp_load_trial_balance_csv_from_blob

        Each SP receives:
        - @auth_user_id: The authenticated user ID
        - @je_analysis_exec_gid: The execution ID (GUID)

        The SPs handle internally:
        - Resolving dataset_version_id from execution_id
        - Finding blob paths
        - Data validation
        - Loading data to staging tables

        Args:
            execution_id: The execution ID (GUID)
            auth_user_id: The authenticated user ID

        Returns:
            Dict with success status and optional error information
        """
        try:
            logger.info(f"Starting database upload for execution {execution_id}")
            logger.info(f"Auth User ID: {auth_user_id}")

            # Initialize AccountingDataLoader with simple parameters
            logger.info("Initializing AccountingDataLoader...")
            loader = AccountingDataLoader(
                execution_id=execution_id,
                auth_user_id=auth_user_id
            )

            # Run the data loading process
            # The SPs will read directly from blob storage using External Data Source
            logger.info("Starting data load process...")
            result = loader.process_data_load()

            if result["success"]:
                logger.info("Database upload completed successfully")
                return {
                    "success": True,
                    "message": "Data uploaded to database successfully",
                    "elapsed_time": result.get("elapsed_time")
                }
            else:
                # Process failed
                error_msg = result.get("error", "Unknown error during database upload")
                logger.error(f"Database upload failed: {error_msg}")

                return {
                    "success": False,
                    "error": error_msg,
                    "elapsed_time": result.get("elapsed_time")
                }

        except Exception as e:
            error_msg = f"Error during database upload: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "error": error_msg
            }


# Global service instance
_database_upload_service: Optional[DatabaseUploadService] = None


def get_database_upload_service() -> DatabaseUploadService:
    """Get global database upload service instance"""
    global _database_upload_service
    if _database_upload_service is None:
        _database_upload_service = DatabaseUploadService()
        logger.info("Initialized DatabaseUploadService")
    return _database_upload_service