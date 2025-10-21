# routes/execution_status.py
"""
Execution Status Routes - Generic endpoint to get execution information
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from services.execution_service import get_execution_service

router = APIRouter(prefix="/smau-proto/api/import", tags=["execution_status"])

# ==========================================
# Pydantic Models
# ==========================================

class ExecutionStatusResponse(BaseModel):
    """Complete execution status response"""
    execution_id: str
    status: str
    step: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    test_type: Optional[str] = None
    file_path: Optional[str] = None
    created_at: str
    updated_at: str
    
    # Optional fields
    project_id: Optional[str] = None
    period: Optional[str] = None
    parent_execution_id: Optional[str] = None
    
    # Validation
    validation_result: Optional[Dict[str, Any]] = None
    
    # Conversion
    result_path: Optional[str] = None
    conversion_stats: Optional[Dict[str, Any]] = None
    
    # Mapeo (Libro Diario)
    mapeo_results: Optional[Dict[str, Any]] = None
    manual_mapping_required: Optional[bool] = None
    unmapped_fields_count: Optional[int] = None
    output_file: Optional[str] = None
    
    # Sumas y Saldos specific
    sumas_saldos_status: Optional[str] = None
    sumas_saldos_raw_path: Optional[str] = None
    sumas_saldos_csv_path: Optional[str] = None
    sumas_saldos_mapping: Optional[Dict[str, Any]] = None
    sumas_saldos_stats: Optional[Dict[str, Any]] = None
    sumas_saldos_manual_mapping_required: Optional[bool] = None
    sumas_saldos_unmapped_count: Optional[int] = None
    sumas_saldos_error: Optional[str] = None
    
    # Errors
    error: Optional[str] = None

# ==========================================
# ENDPOINT: Get Execution Status
# ==========================================

@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get complete execution status including all processing steps.
    Works for both Libro Diario and Sumas y Saldos executions.
    """
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        # Build response with all available fields
        response = ExecutionStatusResponse(
            execution_id=execution_id,
            status=execution.status,
            step=getattr(execution, 'step', None),
            file_name=getattr(execution, 'file_name', None),
            file_type=getattr(execution, 'file_type', None),
            test_type=getattr(execution, 'test_type', None),
            file_path=execution.file_path,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
            
            # Optional fields
            project_id=getattr(execution, 'project_id', None),
            period=getattr(execution, 'period', None),
            parent_execution_id=getattr(execution, 'parent_execution_id', None),
            
            # Validation
            validation_result=getattr(execution, 'validation_result', None),
            
            # Conversion
            result_path=getattr(execution, 'result_path', None),
            conversion_stats=getattr(execution, 'stats', None),
            
            # Mapeo (Libro Diario)
            mapeo_results=getattr(execution, 'mapeo_results', None),
            manual_mapping_required=getattr(execution, 'manual_mapping_required', None),
            unmapped_fields_count=getattr(execution, 'unmapped_fields_count', None),
            
            # Sumas y Saldos
            sumas_saldos_status=getattr(execution, 'sumas_saldos_status', None),
            sumas_saldos_raw_path=getattr(execution, 'sumas_saldos_raw_path', None),
            sumas_saldos_csv_path=getattr(execution, 'sumas_saldos_csv_path', None),
            sumas_saldos_mapping=getattr(execution, 'sumas_saldos_mapping', None),
            sumas_saldos_stats=getattr(execution, 'sumas_saldos_stats', None),
            sumas_saldos_manual_mapping_required=getattr(execution, 'sumas_saldos_manual_mapping_required', None),
            sumas_saldos_unmapped_count=getattr(execution, 'sumas_saldos_unmapped_count', None),
            sumas_saldos_error=getattr(execution, 'sumas_saldos_error', None),
            
            # Errors
            error=getattr(execution, 'error', None)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting execution status: {str(e)}"
        )

# ==========================================
# ENDPOINT: Get Coordinated Executions
# ==========================================

@router.get("/status/{execution_id}/coordinated")
async def get_coordinated_executions_status(execution_id: str):
    """
    Get status of coordinated executions (Libro Diario + Sumas y Saldos).
    Returns both executions if they exist.
    """
    execution_service = get_execution_service()
    
    try:
        coordinated = execution_service.get_coordinated_executions(execution_id)
        
        result = {
            "execution_id": execution_id,
            "libro_diario": None,
            "sumas_saldos": None
        }
        
        # Get Libro Diario info
        if coordinated.get('libro_diario'):
            ld_execution = coordinated['libro_diario']
            result["libro_diario"] = {
                "execution_id": ld_execution.id,
                "status": ld_execution.status,
                "step": getattr(ld_execution, 'step', None),
                "file_name": getattr(ld_execution, 'file_name', None),
                "file_type": getattr(ld_execution, 'file_type', None)
            }
        
        # Get Sumas y Saldos info
        if coordinated.get('sumas_saldos'):
            ss_execution = coordinated['sumas_saldos']
            result["sumas_saldos"] = {
                "execution_id": ss_execution.id,
                "status": ss_execution.status,
                "step": getattr(ss_execution, 'step', None),
                "file_name": getattr(ss_execution, 'file_name', None),
                "file_type": getattr(ss_execution, 'file_type', None),
                "sumas_saldos_status": getattr(ss_execution, 'sumas_saldos_status', None)
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting coordinated executions: {str(e)}"
        )