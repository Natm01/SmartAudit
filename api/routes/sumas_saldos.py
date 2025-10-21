# routes/sumas_saldos.py
"""
Sumas y Saldos routes - Following Journal Entry structure
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from services.execution_service import get_execution_service
from services.sumas_saldos_service import get_sumas_saldos_service

router = APIRouter(prefix="/smau-proto/api/import", tags=["sumas_saldos"])

# Pydantic Models
class SumasSaldosPreviewResponse(BaseModel):
    execution_id: str
    file_name: str
    total_rows: int
    preview_data: List[dict]
    column_names: List[str]
    status: str

class SumasSaldosStatusResponse(BaseModel):
    execution_id: str
    status: str
    file_path: Optional[str] = None
    message: str

# ==========================================
# ENDPOINT 1: Start Automatic Mapping (Background)
# ==========================================
@router.post("/mapeo-sumas-saldos/{execution_id}")
async def start_sumas_saldos_mapeo(
    execution_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start automatic Sumas y Saldos mapping in background.
    Similar to journal entry mapeo endpoint.
    """
    execution_service = get_execution_service()
    
    try:
        # Verify execution exists and Sumas y Saldos was uploaded
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'sumas_saldos_raw_path') or not execution.sumas_saldos_raw_path:
            # Check if it's a file_type="Sys" upload
            if execution.file_type == "Sys" and execution.file_path:
                # Use the main file_path as sumas_saldos_raw_path
                execution_service.update_execution(
                    execution_id,
                    sumas_saldos_raw_path=execution.file_path
                )
                execution = execution_service.get_execution(execution_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sumas y Saldos not uploaded yet"
                )
        
        # Check if already processing
        if hasattr(execution, 'sumas_saldos_status') and execution.sumas_saldos_status == "processing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos mapping already in progress"
            )
        
        # Update status to processing
        execution_service.update_execution(
            execution_id,
            sumas_saldos_status="processing"
        )
        
        # Start mapping in background
        background_tasks.add_task(
            _process_sumas_saldos_mapeo_background,
            execution_id,
            execution.sumas_saldos_raw_path
        )
        
        return {
            "execution_id": execution_id,
            "status": "processing",
            "message": "Sumas y Saldos mapping started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        execution_service.update_execution(
            execution_id,
            sumas_saldos_status="failed",
            sumas_saldos_error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting Sumas y Saldos mapping: {str(e)}"
        )

async def _process_sumas_saldos_mapeo_background(execution_id: str, raw_file_path: str):
    """Background task for Sumas y Saldos mapping"""
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        # Step 1: Detect automatic mapping
        automatic_mapping_result = await sumas_saldos_service.detect_automatic_mapping(raw_file_path)
        
        automatic_mapping = automatic_mapping_result["mapping"]
        available_columns = automatic_mapping_result["available_columns"]
        
        # Check if there are unmapped columns
        mapped_columns = set(k for k, v in automatic_mapping.items() if v is not None)
        all_columns = set(available_columns)
        unmapped_columns = all_columns - mapped_columns
        
        manual_mapping_required = len(unmapped_columns) > 0
        
        # Step 2: Process with automatic mapping
        result = await sumas_saldos_service.process_sumas_saldos(
            raw_file_path,
            automatic_mapping,
            execution_id
        )
        
        # Update execution with results
        if manual_mapping_required:
            execution_service.update_execution(
                execution_id,
                sumas_saldos_status="completed",
                sumas_saldos_mapping=automatic_mapping,
                sumas_saldos_csv_path=result["csv_path"],
                sumas_saldos_stats=result["stats"],
                sumas_saldos_manual_mapping_required=True,
                sumas_saldos_unmapped_count=len(unmapped_columns)
            )
        else:
            execution_service.update_execution(
                execution_id,
                sumas_saldos_status="completed",
                sumas_saldos_mapping=automatic_mapping,
                sumas_saldos_csv_path=result["csv_path"],
                sumas_saldos_stats=result["stats"],
                sumas_saldos_manual_mapping_required=False,
                sumas_saldos_unmapped_count=0
            )
        
    except Exception as e:
        execution_service.update_execution(
            execution_id,
            sumas_saldos_status="failed",
            sumas_saldos_error=str(e)
        )

# ==========================================
# ENDPOINT 2: Get Sumas y Saldos Status
# ==========================================
@router.get("/mapeo-sumas-saldos/{execution_id}/status")
async def get_sumas_saldos_mapeo_status(execution_id: str):
    """
    Get Sumas y Saldos mapping status.
    Similar to journal entry mapeo status endpoint.
    """
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        response = {
            "execution_id": execution_id,
            "status": execution.sumas_saldos_status if hasattr(execution, 'sumas_saldos_status') else "not_started",
            "manual_mapping_required": execution.sumas_saldos_manual_mapping_required if hasattr(execution, 'sumas_saldos_manual_mapping_required') else False,
            "unmapped_fields_count": execution.sumas_saldos_unmapped_count if hasattr(execution, 'sumas_saldos_unmapped_count') else 0
        }
        
        if hasattr(execution, 'sumas_saldos_mapping') and execution.sumas_saldos_mapping:
            response["mapping"] = execution.sumas_saldos_mapping
        
        if hasattr(execution, 'sumas_saldos_stats') and execution.sumas_saldos_stats:
            response["stats"] = execution.sumas_saldos_stats
        
        if hasattr(execution, 'sumas_saldos_error') and execution.sumas_saldos_error:
            response["error"] = execution.sumas_saldos_error
        
        if hasattr(execution, 'sumas_saldos_csv_path') and execution.sumas_saldos_csv_path:
            response["csv_path"] = execution.sumas_saldos_csv_path
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Sumas y Saldos status: {str(e)}"
        )

# ==========================================
# ENDPOINT 3: Get Unmapped Fields
# ==========================================
@router.get("/mapeo-sumas-saldos/{execution_id}/unmapped-fields")
async def get_sumas_saldos_unmapped_fields(execution_id: str):
    """
    Get unmapped fields that require manual mapping.
    Similar to journal entry unmapped-fields endpoint.
    """
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'sumas_saldos_mapping') or not execution.sumas_saldos_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos mapping not completed yet"
            )
        
        if not hasattr(execution, 'sumas_saldos_raw_path') or not execution.sumas_saldos_raw_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos raw file not found"
            )
        
        # Get unmapped fields analysis
        analysis = await sumas_saldos_service.get_unmapped_fields_analysis(
            execution.sumas_saldos_raw_path,
            execution.sumas_saldos_mapping
        )
        
        return {
            "execution_id": execution_id,
            "unmapped_fields": analysis["unmapped_fields"],
            "available_standard_fields": analysis["available_standard_fields"],
            "total_unmapped": analysis["total_unmapped"],
            "total_available_fields": analysis["total_available_fields"],
            "message": f"Found {analysis['total_unmapped']} unmapped fields" if analysis['total_unmapped'] > 0 else "All fields mapped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting unmapped fields: {str(e)}"
        )

# ==========================================
# ENDPOINT 4: Download Sumas y Saldos File
# ==========================================
@router.get("/mapeo-sumas-saldos/{execution_id}/download/{file_type}")
async def download_sumas_saldos_file(execution_id: str, file_type: str):
    """
    Download Sumas y Saldos files (csv or report).
    Similar to journal entry download endpoint.
    """
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'sumas_saldos_csv_path') or not execution.sumas_saldos_csv_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos CSV not generated yet"
            )
        
        file_map = {
            'csv': execution.sumas_saldos_csv_path,
            'report': None  # TODO: Implement report generation
        }
        
        if file_type not in file_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Must be one of: {list(file_map.keys())}"
            )
        
        file_path = file_map[file_type]
        
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File type '{file_type}' not available yet"
            )
        
        # Return file URL/path
        return {
            "execution_id": execution_id,
            "file_type": file_type,
            "file_path": file_path,
            "message": f"Sumas y Saldos {file_type} file ready for download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )

# ==========================================
# ENDPOINT 5: Preview Sumas y Saldos
# ==========================================
@router.get("/preview-sumas-saldos/{execution_id}", response_model=SumasSaldosPreviewResponse)
async def preview_sumas_saldos(execution_id: str):
    """
    Get preview of processed Sumas y Saldos CSV.
    Similar to journal entry preview endpoint.
    """
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'sumas_saldos_csv_path') or not execution.sumas_saldos_csv_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos CSV not generated yet"
            )
        
        # Get preview (default 10 rows)
        preview_data = await sumas_saldos_service.get_preview(
            execution.sumas_saldos_csv_path,
            rows=10
        )
        
        return SumasSaldosPreviewResponse(
            execution_id=execution_id,
            file_name=f"{execution_id}_sumas_saldos.csv",
            total_rows=preview_data["total_rows"],
            preview_data=preview_data["data"],
            column_names=preview_data["columns"],
            status="ready"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error previewing Sumas y Saldos: {str(e)}"
        )

@router.get("/preview-sumas-saldos/{execution_id}/original", response_model=SumasSaldosPreviewResponse)
async def preview_sumas_saldos_original(execution_id: str):
    """
    Get preview of ORIGINAL Sumas y Saldos Excel (antes del mapeo).
    Devuelve las columnas originales del archivo.
    """
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'sumas_saldos_raw_path') or not execution.sumas_saldos_raw_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos raw file not found"
            )
        
        # Get preview del archivo ORIGINAL (Excel)
        preview_data = await sumas_saldos_service.get_original_preview(
            execution.sumas_saldos_raw_path,
            rows=10
        )
        
        return SumasSaldosPreviewResponse(
            execution_id=execution_id,
            file_name=execution.sumas_saldos_raw_path.split('/')[-1],
            total_rows=preview_data["total_rows"],
            preview_data=preview_data["data"],
            column_names=preview_data["columns"],
            status="ready"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error previewing original Sumas y Saldos: {str(e)}"
        )