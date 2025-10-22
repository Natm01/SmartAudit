# routes/execution_status.py
"""
Execution Status Routes - Generic endpoint to get execution information
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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


class FileMetadata(BaseModel):
    """Metadata de un archivo"""
    file_name: str
    file_size: Optional[int] = None  # Tamaño en bytes
    file_extension: Optional[str] = None  # Extensión (.csv, .xlsx, etc.)
    file_path: Optional[str] = None


class ImportDetailsResponse(BaseModel):
    """Respuesta completa con todos los detalles de importación"""
    execution_id: str

    # Información del proyecto
    project_id: Optional[str] = None
    fiscal_year: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_final: Optional[str] = None

    # Archivo Libro Diario
    libro_diario: Optional[FileMetadata] = None

    # Archivo Sumas y Saldos
    sumas_saldos: Optional[FileMetadata] = None

    # Estado de procesamiento
    status: str
    step: Optional[str] = None
    created_at: str
    updated_at: str
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


# ==========================================
# ENDPOINT: Get Import Details
# ==========================================

@router.get("/import-details/{execution_id}", response_model=ImportDetailsResponse)
async def get_import_details(execution_id: str):
    """
    Obtiene todos los datos de la importación del Libro Diario, incluyendo:
    - Proyecto
    - Año fiscal
    - Fecha inicio
    - Fecha final
    - Nombre del archivo Libro diario y todos sus metadatos (peso, extensión)
    - Nombre del archivo Sumas y saldos y todos sus metadatos (peso, extensión)
    - El execution id asignado
    """
    execution_service = get_execution_service()

    try:
        # Obtener la ejecución principal
        execution = execution_service.get_execution(execution_id)

        # Extraer fechas del campo period (formato: "YYYY-MM-DD a YYYY-MM-DD")
        fecha_inicio = None
        fecha_final = None
        fiscal_year = None

        if execution.period:
            try:
                # Parsear el periodo para extraer fechas
                parts = execution.period.split(" a ")
                if len(parts) == 2:
                    fecha_inicio = parts[0].strip()
                    fecha_final = parts[1].strip()
                    # Extraer el año fiscal de la fecha de inicio
                    fiscal_year = fecha_inicio.split("-")[0]
            except:
                pass

        # Crear metadata del Libro Diario
        libro_diario_metadata = None
        if execution.file_name:
            libro_diario_metadata = FileMetadata(
                file_name=execution.file_name,
                file_size=getattr(execution, 'file_size', None),
                file_extension=getattr(execution, 'file_extension', None),
                file_path=execution.file_path
            )

        # Buscar Sumas y Saldos relacionado
        sumas_saldos_metadata = None
        try:
            # Intentar encontrar la ejecución de Sumas y Saldos relacionada
            ss_execution_id = f"{execution_id}-ss"
            ss_execution = execution_service.get_execution(ss_execution_id)

            if ss_execution:
                sumas_saldos_metadata = FileMetadata(
                    file_name=getattr(ss_execution, 'file_name', None),
                    file_size=getattr(ss_execution, 'file_size', None),
                    file_extension=getattr(ss_execution, 'file_extension', None),
                    file_path=getattr(ss_execution, 'file_path', None)
                )
        except:
            # Si no existe Sumas y Saldos, continuar sin error
            pass

        # Construir respuesta
        response = ImportDetailsResponse(
            execution_id=execution_id,
            project_id=getattr(execution, 'project_id', None),
            fiscal_year=fiscal_year,
            fecha_inicio=fecha_inicio,
            fecha_final=fecha_final,
            libro_diario=libro_diario_metadata,
            sumas_saldos=sumas_saldos_metadata,
            status=execution.status,
            step=getattr(execution, 'step', None),
            created_at=execution.created_at,
            updated_at=execution.updated_at,
            error=getattr(execution, 'error', None)
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo detalles de importación: {str(e)}"
        )