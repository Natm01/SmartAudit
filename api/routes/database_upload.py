# routes/database_upload.py
"""
Database Upload Routes - Load accounting data to SQL Server database
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from services.execution_service import get_execution_service
from services.database_upload_service import get_database_upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smau-proto/api/import", tags=["database_upload"])


# ==========================================
# Pydantic Models
# ==========================================

class DatabaseUploadRequest(BaseModel):
    """Request to upload data to database"""
    execution_id: str
    auth_user_id: int


class DatabaseUploadResponse(BaseModel):
    """Response for database upload initiation"""
    execution_id: str
    message: str
    status: str


class DatabaseUploadStatusResponse(BaseModel):
    """Response with database upload status"""
    execution_id: str
    status: str
    step: Optional[str] = None
    error: Optional[str] = None
    elapsed_time: Optional[float] = None


# ==========================================
# Background Task
# ==========================================

async def upload_to_database_background(execution_id: str, auth_user_id: int):
    """Background task for database upload"""
    execution_service = get_execution_service()
    db_upload_service = get_database_upload_service()

    try:
        logger.info(f"Starting database upload for execution {execution_id}")

        # Update status to processing
        execution_service.update_execution(
            execution_id,
            status="processing",
            step="database_upload"
        )

        # Execute database upload
        result = await db_upload_service.upload_to_database(
            execution_id=execution_id,
            auth_user_id=auth_user_id
        )

        if result["success"]:
            # Update execution with success
            update_data = {
                "status": "completed",
                "step": "database_upload"
            }

            execution_service.update_execution(execution_id, **update_data)

            logger.info(f"Database upload completed successfully for {execution_id}")

        else:
            # Update execution with error
            error_msg = result.get("error", "Unknown error during database upload")
            execution_service.update_execution(
                execution_id,
                status="failed",
                step="database_upload",
                error=error_msg
            )

            logger.error(f"Database upload failed for {execution_id}: {error_msg}")

    except Exception as e:
        error_msg = f"Database upload error: {str(e)}"
        logger.error(f"Error in database upload background task: {error_msg}")

        execution_service.update_execution(
            execution_id,
            status="failed",
            step="database_upload",
            error=error_msg
        )


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/database-upload", response_model=DatabaseUploadResponse)
async def start_database_upload(
    request: DatabaseUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Start database upload process for accounting data.

    This endpoint executes 3 stored procedures in the background:
    1. staging.sp_load_journal_entries_csv_from_blob
    2. staging.sp_load_journal_entry_lines_csv_from_blob
    3. staging.sp_load_trial_balance_csv_from_blob

    Each SP receives:
    - @auth_user_id: The authenticated user ID
    - @je_analysis_exec_gid: The execution ID (GUID)

    The SPs handle internally:
    - Resolving dataset_version_id from execution_id
    - Finding blob paths for the CSV files
    - Data validation
    - Loading data to staging tables

    Args:
        request: DatabaseUploadRequest with execution_id and auth_user_id

    Returns:
        DatabaseUploadResponse with execution_id, message, and status
    """
    execution_service = get_execution_service()

    try:
        # Validate execution exists
        execution = execution_service.get_execution(request.execution_id)

        # Start background task
        background_tasks.add_task(
            upload_to_database_background,
            request.execution_id,
            request.auth_user_id
        )

        logger.info(f"Database upload started for execution {request.execution_id}")

        return DatabaseUploadResponse(
            execution_id=request.execution_id,
            message="Database upload started successfully",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting database upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting database upload: {str(e)}"
        )


@router.get("/database-upload/{execution_id}/status", response_model=DatabaseUploadStatusResponse)
async def get_database_upload_status(execution_id: str):
    """
    Get status of database upload process.

    Returns current status and progress information.
    """
    execution_service = get_execution_service()

    try:
        execution = execution_service.get_execution(execution_id)

        response = DatabaseUploadStatusResponse(
            execution_id=execution_id,
            status=execution.status,
            step=execution.step,
            error=execution.error
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database upload status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}"
        )
