# services/database_upload_service.py
"""
Database Upload Service - Handles uploading accounting data to SQL Server
"""
import logging
import tempfile
import pandas as pd
from typing import Dict, Any, Optional
import os

from services.storage.azure_storage_service import get_azure_storage_service
from services.accounting_loader_prod import AccountingDataLoader

logger = logging.getLogger(__name__)


class DatabaseUploadService:
    """Service to handle database uploads for accounting data"""
    
    def __init__(self):
        self.storage_service = get_azure_storage_service()
        self.accounting_loader = None
        
    async def validate_files_exist(self, execution_id: str, project_id: int) -> Dict[str, Any]:
        """
        Validate that all required CSV files exist in blob storage.

        Args:
            execution_id: The execution ID
            project_id: The project ID

        Returns:
            Dict with 'valid' boolean and list of 'missing_files'
        """
        required_files = [
            f"{project_id}/{execution_id}/je/{execution_id}_journal_entries_Je.csv",
            f"{project_id}/{execution_id}/je/{execution_id}_journal_entry_lines_Je.csv",
            f"{project_id}/{execution_id}/sys/{execution_id}_trial_balance_sys.csv"
        ]

        missing_files = []

        for filename in required_files:
            # Construct blob URL - files are in "libro-diario-resultados" container
            blob_url = f"azure://libro-diario-resultados/{filename}"
            
            if not self.storage_service.file_exists(blob_url):
                missing_files.append(filename)
                logger.warning(f"Required file not found: {filename}")
        
        valid = len(missing_files) == 0
        
        if valid:
            logger.info(f"All required files found for execution {execution_id}")
        else:
            logger.error(f"Missing files for execution {execution_id}: {missing_files}")
        
        return {
            "valid": valid,
            "missing_files": missing_files,
            "required_files": required_files
        }
    
    async def upload_to_database(
        self,
        execution_id: str,
        tenant_id: int,
        workspace_id: int,
        project_id: int,
        fiscal_year: int,
        period_ending_date: str,
        needs_mapping: bool = False
    ) -> Dict[str, Any]:
        """
        Upload accounting data to SQL Server database.

        This method:
        1. Constructs blob paths for the 3 CSV files
        2. Creates AccountingDataLoader instance with parameters from execution
        3. Runs the data loading process (SPs read directly from blob)
        4. Uploads totality report back to blob storage if generated

        Args:
            execution_id: The execution ID
            tenant_id: Tenant ID from execution
            workspace_id: Workspace ID from execution
            project_id: Project ID from execution
            fiscal_year: Fiscal year from execution
            period_ending_date: Period ending date from execution (YYYY-MM-DD)
            needs_mapping: Whether to use reporting_account mapping

        Returns:
            Dict with success status and optional error/report information
        """
        try:
            logger.info(f"Starting database upload for execution {execution_id}")
            logger.info(f"Tenant ID: {tenant_id}, Workspace ID: {workspace_id}, Project ID: {project_id}")
            logger.info(f"Fiscal year: {fiscal_year}, Period ending: {period_ending_date}")
            logger.info(f"Needs mapping: {needs_mapping}")
            
            # Define blob relative paths (for SQL Server External Data Source)
            # The SPs expect paths relative to the blob container root
            # Files are in "libro-diario-resultados" container with structure:
            # {project_id}/{execution_id}/je/ - Journal entries files
            # {project_id}/{execution_id}/sys/ - Trial balance (sumas y saldos) file
            blob_paths = {
                "journal_entries": f"libro-diario-resultados/{project_id}/{execution_id}/je/{execution_id}_journal_entries_Je.csv",
                "journal_entry_lines": f"libro-diario-resultados/{project_id}/{execution_id}/je/{execution_id}_journal_entry_lines_Je.csv",
                "trial_balance": f"libro-diario-resultados/{project_id}/{execution_id}/sys/{execution_id}_trial_balance_sys.csv"
            }
            
            logger.info(f"Blob paths configured:")
            for file_type, blob_path in blob_paths.items():
                logger.info(f"  {file_type}: {blob_path}")
            
            # Initialize AccountingDataLoader with execution parameters
            logger.info("Initializing AccountingDataLoader...")
            self.accounting_loader = AccountingDataLoader(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                fiscal_year=fiscal_year,
                period_ending_date=period_ending_date
            )
            
            # Run the data loading process
            # The SPs will read directly from blob storage using External Data Source
            logger.info("Starting data load process...")
            result = self.accounting_loader.process_data_load(
                je_file=blob_paths["journal_entries"],
                jel_file=blob_paths["journal_entry_lines"],
                tb_file=blob_paths["trial_balance"],
                needs_mapping=needs_mapping
            )
            
            if result["success"]:
                logger.info("Database upload completed successfully")
                
                # Handle totality report if generated
                totality_report_url = None
                if result.get("totality_df") is not None:
                    totality_report_url = await self._upload_totality_report(
                        execution_id, 
                        result["totality_df"]
                    )
                
                return {
                    "success": True,
                    "message": "Data uploaded to database successfully",
                    "dataset_version_id": 201,
                    "totality_report_url": totality_report_url
                }
            else:
                # Process failed
                error_msg = result.get("error", "Unknown error during database upload")
                logger.error(f"Database upload failed: {error_msg}")
                
                # Still try to upload totality report if available
                totality_report_url = None
                if result.get("totality_df") is not None:
                    try:
                        totality_report_url = await self._upload_totality_report(
                            execution_id, 
                            result["totality_df"],
                            failed=True
                        )
                    except Exception as e:
                        logger.warning(f"Could not upload totality report: {e}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "totality_report_url": totality_report_url,
                    "unmapped_accounts": result.get("unmapped_accounts")
                }
                
        except Exception as e:
            error_msg = f"Error during database upload: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg
            }
    
    async def _upload_totality_report(
        self, 
        execution_id: str, 
        totality_df: pd.DataFrame,
        failed: bool = False
    ) -> str:
        """
        Upload totality validation report to blob storage.
        
        Args:
            execution_id: The execution ID
            totality_df: DataFrame with totality validation results
            failed: Whether the upload process failed
            
        Returns:
            Blob URL of uploaded report
        """
        try:
            # Create temporary CSV file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.csv', 
                delete=False,
                encoding='utf-8-sig'
            )
            
            # Write DataFrame to CSV
            totality_df.to_csv(temp_file.name, index=False)
            temp_file.close()
            
            # Upload to blob storage in results container
            description = "totality_report_FAILED" if failed else "totality_report"
            
            blob_url = self.storage_service.upload_file_chunked(
                local_path=temp_file.name,
                container_type="results",
                execution_id=execution_id,
                file_type="Je",
                stage="result",
                description=description
            )
            
            logger.info(f"Totality report uploaded: {blob_url}")
            
            # Clean up temp file
            try:
                os.remove(temp_file.name)
            except:
                pass
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading totality report: {str(e)}")
            raise


# Global service instance
_database_upload_service: Optional[DatabaseUploadService] = None


def get_database_upload_service() -> DatabaseUploadService:
    """Get global database upload service instance"""
    global _database_upload_service
    if _database_upload_service is None:
        _database_upload_service = DatabaseUploadService()
        logger.info("Initialized DatabaseUploadService")
    return _database_upload_service