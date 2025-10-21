# routes/validation_rules.py
"""
Validation Rules Routes - Endpoints for accounting validations after mapping
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile
import os

from services.execution_service import get_execution_service
from services.validation_rules_service import get_validation_rules_service
from services.storage.azure_storage_service import get_azure_storage_service
from utils.serialization import convert_numpy_types

router = APIRouter(prefix="/smau-proto/api/import", tags=["validation_rules"])

# ==========================================
# Pydantic Models
# ==========================================

class ValidationRulesRequest(BaseModel):
    """Request to start validation rules"""
    period: str  # Format: YYYY-MM

class ValidationRulesResponse(BaseModel):
    """Response for validation rules initiation"""
    execution_id: str
    message: str
    status: str

class ValidationRulesStatusResponse(BaseModel):
    """Response for validation rules status"""
    execution_id: str
    status: str
    validation_timestamp: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ==========================================
# Background Task
# ==========================================

async def run_validation_rules_background(execution_id: str, period: str):
    """Background task to run validation rules"""
    execution_service = get_execution_service()
    validation_service = get_validation_rules_service()
    azure_service = get_azure_storage_service()
    
    try:
        # Update status to processing
        execution_service.update_execution(
            execution_id,
            status="processing",
            step="validation_rules"
        )
        
        # Get execution to find the mapped CSV file
        execution = execution_service.get_execution(execution_id)
        
        # FIXED: Construct the correct filename for manual mapped file
        # Based on _get_blob_name logic with:
        # - filename="manual_mapped.csv", stage="manual_mapeo", description="manual_mapped", file_type="Je"
        # - keep_original_name=False
        # Pattern: {execution_id}_{stage}_{description}_{file_type}.csv
        # Result: {execution_id}_manual_mapped_Je.csv
        expected_filename = f"{execution_id}_manual_mapped_Je.csv"
        
        # Try to find the file in Azure Storage
        # The file should be in the mapeos container
        azure_file_path = None
        
        # Option 1: Check if output_file already has the correct path
        if execution.output_file and "manual_mapped" in execution.output_file:
            azure_file_path = execution.output_file
            print(f" Found manual mapped file in output_file: {azure_file_path}")
        
        # Option 2: Construct the path manually
        else:
            # Path pattern: azure://mapeos/{blob_name}
            # Note: Azure blob naming is flat, no subdirectories
            azure_file_path = f"azure://mapeos/{expected_filename}"
            print(f"🔍 Constructed manual mapped file path: {azure_file_path}")
        
        # Verify the file exists
        if not azure_file_path:
            raise Exception(
                f"Manual mapped file not found. Expected: {expected_filename}. "
                "Please complete manual mapping first."
            )
        
        # Download file from Azure to local temp
        temp_dir = tempfile.gettempdir()
        local_file = os.path.join(temp_dir, f"validation_{execution_id}.csv")
        
        try:
            azure_service.download_file(azure_file_path, local_file)
            print(f" Downloaded file for validation: {azure_file_path}")
        except Exception as e:
            raise Exception(
                f"Failed to download manual mapped file from Azure. "
                f"Path: {azure_file_path}. Error: {str(e)}. "
                "Please ensure manual mapping is completed."
            )
        
        # Run all validations
        validation_results = validation_service.run_all_validations(local_file, period)
        
        # Clean up temp file
        if os.path.exists(local_file):
            os.remove(local_file)
        
        # Convert numpy types to native Python types
        validation_results_clean = convert_numpy_types(validation_results)
        
        # Update execution with results
        execution_service.update_execution(
            execution_id,
            status="completed",
            step="validation_rules_completed",
            validation_rules_results=validation_results_clean
        )
        
        print(f" Validation rules completed for execution {execution_id}")
        
    except Exception as e:
        print(f"❌ Error in validation rules: {str(e)}")
        execution_service.update_execution(
            execution_id,
            status="failed",
            step="validation_rules_failed",
            error=f"Validation rules error: {str(e)}"
        )

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/validate-rules/{execution_id}", response_model=ValidationRulesResponse)
async def start_validation_rules(
    execution_id: str, 
    request: ValidationRulesRequest,
    background_tasks: BackgroundTasks
):
    """
    Start validation rules process for a mapped file.
    
    This runs 4 phases of validation:
    1. Format validations (dates, times, amounts)
    2. Identifier validations (unique IDs, sequential lines)
    3. Temporal validations (dates within period)
    4. Integrity validations (balanced entries)
    
    IMPORTANT: This endpoint expects the manual mapped file:
    {execution_id}_manual_mapped_Je.csv
    """
    execution_service = get_execution_service()
    
    try:
        # Verify execution exists
        execution = execution_service.get_execution(execution_id)
        
        # FIXED: Verify that manual mapping is completed
        # Check if the expected file exists or if manual mapping step is completed
        expected_filename = f"{execution_id}_manual_mapped_Je.csv"
        
        # Check if manual mapping step is completed
        if not execution.output_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Manual mapping must be completed before running validation rules. "
                       f"Expected file: {expected_filename}"
            )
        
        # Verify period format
        if not request.period or '-' not in request.period:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period format. Expected YYYY-MM (e.g., 2024-12)"
            )
        
        # Start validation in background
        background_tasks.add_task(
            run_validation_rules_background, 
            execution_id, 
            request.period
        )
        
        return ValidationRulesResponse(
            execution_id=execution_id,
            message="Validation rules started",
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting validation rules: {str(e)}"
        )

@router.get("/validate-rules/{execution_id}/status", response_model=ValidationRulesStatusResponse)
async def get_validation_rules_status(execution_id: str):
    """
    Get validation rules status and results.
    
    Returns the current status and full validation results if completed.
    """
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        # Get validation results if available
        validation_results = execution.validation_rules_results if hasattr(execution, 'validation_rules_results') else None
        
        # Determine status
        current_status = execution.status
        if execution.step == "validation_rules_completed":
            current_status = "completed"
        elif execution.step == "validation_rules_failed":
            current_status = "failed"
        elif execution.step == "validation_rules":
            current_status = "processing"
        
        # Get summary if results available
        summary = None
        if validation_results:
            summary = validation_results.get('summary', {})
        
        return ValidationRulesStatusResponse(
            execution_id=execution_id,
            status=current_status,
            validation_timestamp=validation_results.get('validation_timestamp') if validation_results else None,
            results=validation_results,
            summary=summary,
            error=execution.error if hasattr(execution, 'error') and execution.error else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting validation status: {str(e)}"
        )

@router.get("/validate-rules/{execution_id}/summary")
async def get_validation_summary(execution_id: str):
    """
    Get simplified validation summary (for UI progress indicators).
    
    Returns phase-by-phase completion status.
    """
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        # Get validation results
        validation_results = execution.validation_rules_results if hasattr(execution, 'validation_rules_results') else None
        
        if not validation_results:
            return {
                "execution_id": execution_id,
                "status": "not_started",
                "phases": [
                    {"phase": 1, "name": "Validaciones de Formato", "status": "pending"},
                    {"phase": 2, "name": "Validaciones de Identificadores", "status": "pending"},
                    {"phase": 3, "name": "Validaciones Temporales", "status": "pending"},
                    {"phase": 4, "name": "Validaciones de Integridad Contable", "status": "pending"}
                ],
                "progress": {
                    "completed": 0,
                    "total": 4
                }
            }
        
        # Build phase status
        phases = []
        
        # Phase 1
        fase_1 = validation_results.get('fase_1_formato', {})
        phases.append({
            "phase": 1,
            "name": "Validaciones de Formato",
            "status": "completed" if fase_1.get('is_phase_valid') else "failed",
            "checks": fase_1.get('summary', {})
        })
        
        # Phase 2
        fase_2 = validation_results.get('fase_2_identificadores', {})
        phases.append({
            "phase": 2,
            "name": "Validaciones de Identificadores",
            "status": "completed" if fase_2.get('is_phase_valid') else "failed",
            "checks": fase_2.get('summary', {})
        })
        
        # Phase 3
        fase_3 = validation_results.get('fase_3_temporales', {})
        phases.append({
            "phase": 3,
            "name": "Validaciones Temporales",
            "status": "completed" if fase_3.get('is_phase_valid') else "failed",
            "checks": fase_3.get('summary', {})
        })
        
        # Phase 4
        fase_4 = validation_results.get('fase_4_integridad', {})
        phases.append({
            "phase": 4,
            "name": "Validaciones de Integridad Contable",
            "status": "completed" if fase_4.get('is_phase_valid') else "failed",
            "checks": fase_4.get('summary', {})
        })
        
        # Calculate progress
        completed_phases = sum(1 for p in phases if p['status'] == 'completed')
        
        return {
            "execution_id": execution_id,
            "status": execution.status,
            "phases": phases,
            "progress": {
                "completed": completed_phases,
                "total": 4
            },
            "summary": validation_results.get('summary', {}),
            "validation_timestamp": validation_results.get('validation_timestamp')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting validation summary: {str(e)}"
        )

@router.get("/validate-rules/{execution_id}/phase/{phase_number}")
async def get_phase_details(execution_id: str, phase_number: int):
    """
    Get detailed results for a specific validation phase.
    
    phase_number: 1-4
    """
    execution_service = get_execution_service()
    
    if phase_number < 1 or phase_number > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase number must be between 1 and 4"
        )
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        validation_results = execution.validation_rules_results if hasattr(execution, 'validation_rules_results') else None
        
        if not validation_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation results not found. Please run validations first."
            )
        
        # Map phase number to result key
        phase_map = {
            1: 'fase_1_formato',
            2: 'fase_2_identificadores',
            3: 'fase_3_temporales',
            4: 'fase_4_integridad'
        }
        
        phase_key = phase_map[phase_number]
        phase_data = validation_results.get(phase_key, {})
        
        if not phase_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phase {phase_number} data not found"
            )
        
        return {
            "execution_id": execution_id,
            "phase_number": phase_number,
            "phase_data": phase_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting phase details: {str(e)}"
        )