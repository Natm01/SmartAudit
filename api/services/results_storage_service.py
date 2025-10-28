# api/services/results_storage_service.py
import os
import json
import logging
import pandas as pd
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime, UTC

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv

from services.storage.azure_storage_service import get_azure_storage_service
from models.execution import ExecutionStatus

load_dotenv()
logger = logging.getLogger(__name__)


class ResultsStorageService:
    """Service for storing validated results in Azure Blob Storage"""

    def __init__(self):
        self.storage_service = get_azure_storage_service()
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required")

        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.results_container = "libro-diario-resultados"

        # Load column configurations
        self.config_dir = Path(__file__).parent.parent / "config"
        self.journal_config = self._load_json_config("journal_entries_table_mapping.json")
        self.trial_balance_config = self._load_json_config("trial_balance_table_mapping.json")

        self._ensure_results_container_exists()

    def _ensure_results_container_exists(self):
        """Create results container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.results_container)
            container_client.create_container()
            logger.info(f"Created container: {self.results_container}")
        except ResourceExistsError:
            logger.debug(f"Container already exists: {self.results_container}")
        except Exception as e:
            logger.error(f"Error creating container {self.results_container}: {e}")
            raise

    def _load_json_config(self, filename: str) -> Dict:
        """Load JSON configuration file"""
        try:
            config_path = self.config_dir / filename
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config {filename}: {e}")
            raise

    def _get_journal_header_columns(self) -> List[str]:
        """Get list of header column names for journal entries"""
        header_fields = self.journal_config.get("journal_entries", {}).get("header_fields", [])
        return [field["name"] for field in header_fields]

    def _get_journal_detail_columns(self) -> List[str]:
        """Get list of detail column names for journal entries"""
        detail_fields = self.journal_config.get("journal_entries", {}).get("detail_fields", [])
        return [field["name"] for field in detail_fields]

    def _get_trial_balance_columns(self) -> List[str]:
        """Get list of column names for trial balance"""
        fields = self.trial_balance_config.get("trial_balance", {}).get("fields", [])
        return [field["name"] for field in fields]

    def _check_all_validations_passed(self, execution: ExecutionStatus) -> Tuple[bool, str]:
        """
        Check if ALL validations passed for both journal entries and trial balance

        Returns:
            Tuple[bool, str]: (all_passed, error_message)
        """
        errors = []

        # Check if we have both types of data
        has_journal = execution.output_file is not None
        # Use sumas_saldos_csv_path (updated after both auto and manual mapping)
        has_trial_balance = execution.sumas_saldos_csv_path is not None

        if not has_journal and not has_trial_balance:
            return False, "No hay archivos procesados para guardar"

        # Check Journal Entries validations (if exists)
        if has_journal:
            if not execution.validation_rules_results:
                errors.append("Libro Diario: No se encontraron resultados de validaciones")
            else:
                journal_summary = execution.validation_rules_results.get("summary", {})
                if not journal_summary.get("all_passed", False):
                    errors.append(f"Libro Diario: Validaciones fallidas ({journal_summary.get('failed_phases', 0)} fases)")
                    logger.warning(f"Journal validation failed: {journal_summary}")

        # Check Trial Balance validations (if exists)
        if has_trial_balance:
            if not execution.sumas_saldos_validation_results:
                errors.append("Sumas y Saldos: No se encontraron resultados de validaciones")
            else:
                trial_summary = execution.sumas_saldos_validation_results.get("summary", {})
                if not trial_summary.get("all_passed", False):
                    errors.append(f"Sumas y Saldos: Validaciones fallidas ({trial_summary.get('failed_phases', 0)} fases)")
                    logger.warning(f"Trial balance validation failed: {trial_summary}")

        if errors:
            return False, "; ".join(errors)

        return True, ""

    def _create_blob_path(self, project_id: str, execution_id: str,
                         file_type: str, filename: str) -> str:
        """
        Create blob path following structure:
        {project_id}/{execution_id}/sys/{filename}  (for trial balance)
        {project_id}/{execution_id}/je/{filename}   (for journal entries)
        """
        if file_type == "sys":
            folder = "sys"
        elif file_type == "je":
            folder = "je"
        else:
            raise ValueError(f"Invalid file_type: {file_type}")

        return f"{project_id}/{execution_id}/{folder}/{filename}"

    def _filter_and_save_csv(self, source_blob_url: str, columns: List[str],
                            output_path: str) -> str:
        """
        Download CSV from Azure, filter columns, and save to temp file

        Returns:
            Path to temporary CSV file
        """
        # Download source file
        temp_source = self.storage_service.download_file(source_blob_url)

        try:
            # Read CSV
            df = pd.read_csv(temp_source)
            logger.info(f"Read CSV with {len(df)} rows and columns: {list(df.columns)}")

            # Filter columns (only keep those that exist in both config and dataframe)
            available_columns = [col for col in columns if col in df.columns]
            missing_columns = [col for col in columns if col not in df.columns]

            if missing_columns:
                logger.warning(f"Missing columns in data: {missing_columns}")

            # Select only available columns
            df_filtered = df[available_columns]
            logger.info(f"Filtered to {len(available_columns)} columns: {available_columns}")

            # Save to output path
            df_filtered.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Saved filtered CSV to {output_path}")

            return output_path

        finally:
            # Clean up temp source file
            if os.path.exists(temp_source):
                os.remove(temp_source)

    def _upload_to_results_container(self, local_file: str, blob_path: str) -> str:
        """
        Upload file to results container

        Returns:
            Azure blob URL
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.results_container,
            blob=blob_path
        )

        with open(local_file, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="text/csv"),
                max_concurrency=4
            )

        blob_url = f"azure://{self.results_container}/{blob_path}"
        logger.info(f"Uploaded to results: {blob_url}")

        return blob_url

    def save_validated_results(self, execution: ExecutionStatus,
                              project_id: str) -> Dict[str, str]:
        """
        Save validated results to Azure Blob Storage

        Args:
            execution: Execution status with validation results
            project_id: Project ID for folder structure

        Returns:
            Dictionary with paths to saved files

        Raises:
            ValueError: If validations didn't pass or required data is missing
        """
        # Check if all validations passed
        all_passed, error_msg = self._check_all_validations_passed(execution)
        if not all_passed:
            raise ValueError(f"No se pueden guardar resultados: {error_msg}")

        logger.info(f"All validations passed for execution {execution.id}. Starting to save results...")

        saved_files = {}
        temp_files = []

        try:
            # Save Journal Entries (if exists)
            if execution.output_file:
                logger.info("Processing Libro Diario files...")

                # Get columns for header and detail
                header_columns = self._get_journal_header_columns()
                detail_columns = self._get_journal_detail_columns()
                all_columns = header_columns + detail_columns

                # Download and read the journal entries file
                temp_source = self.storage_service.download_file(execution.output_file)
                temp_files.append(temp_source)

                df = pd.read_csv(temp_source)
                logger.info(f"Read journal entries CSV with {len(df)} rows")

                # Separate header and detail data
                available_header_cols = [col for col in header_columns if col in df.columns]
                available_detail_cols = [col for col in detail_columns if col in df.columns]

                # Create header file (unique by journal_entry_id)
                if available_header_cols:
                    df_header = df[available_header_cols].drop_duplicates(subset=['journal_entry_id'], keep='first')
                    temp_header = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
                    temp_header.close()
                    temp_files.append(temp_header.name)

                    df_header.to_csv(temp_header.name, index=False, encoding='utf-8')
                    logger.info(f"Created header file with {len(df_header)} rows and {len(available_header_cols)} columns")

                    # Upload header
                    header_filename = f"{execution.id}-je-cabecera.csv"
                    header_blob_path = self._create_blob_path(project_id, execution.id, "je", header_filename)
                    saved_files['journal_header'] = self._upload_to_results_container(temp_header.name, header_blob_path)

                # Create detail file (all rows with detail columns)
                if available_detail_cols:
                    # Include journal_entry_id to link with header
                    detail_cols_with_id = ['journal_entry_id'] + available_detail_cols if 'journal_entry_id' not in available_detail_cols else available_detail_cols
                    detail_cols_with_id = [col for col in detail_cols_with_id if col in df.columns]

                    df_detail = df[detail_cols_with_id]
                    temp_detail = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
                    temp_detail.close()
                    temp_files.append(temp_detail.name)

                    df_detail.to_csv(temp_detail.name, index=False, encoding='utf-8')
                    logger.info(f"Created detail file with {len(df_detail)} rows and {len(detail_cols_with_id)} columns")

                    # Upload detail
                    detail_filename = f"{execution.id}-je-detalle.csv"
                    detail_blob_path = self._create_blob_path(project_id, execution.id, "je", detail_filename)
                    saved_files['journal_detail'] = self._upload_to_results_container(temp_detail.name, detail_blob_path)

            # Save Trial Balance (if exists)
            if execution.sumas_saldos_csv_path:
                logger.info("Processing Sumas y Saldos file...")

                trial_columns = self._get_trial_balance_columns()

                temp_trial = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
                temp_trial.close()
                temp_files.append(temp_trial.name)

                # Filter and save
                self._filter_and_save_csv(
                    execution.sumas_saldos_csv_path,
                    trial_columns,
                    temp_trial.name
                )

                # Upload trial balance
                trial_filename = f"{execution.id}-sys.csv"
                trial_blob_path = self._create_blob_path(project_id, execution.id, "sys", trial_filename)
                saved_files['trial_balance'] = self._upload_to_results_container(temp_trial.name, trial_blob_path)

            logger.info(f"Successfully saved {len(saved_files)} files to results container")
            return saved_files

        except Exception as e:
            logger.error(f"Error saving validated results: {e}")
            raise

        finally:
            # Clean up all temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"Could not remove temp file {temp_file}: {e}")


def get_results_storage_service() -> ResultsStorageService:
    """Get global Results Storage service instance"""
    global _results_storage_service
    if '_results_storage_service' not in globals():
        globals()['_results_storage_service'] = ResultsStorageService()
    return globals()['_results_storage_service']
