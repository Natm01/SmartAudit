# routes/preview.py
"""
Preview routes with Azure Storage support
ACTUALIZADO: Dos endpoints separados - original y mapeado
"""
import os
import pandas as pd
import tempfile
import logging
from fastapi import APIRouter, HTTPException, status, Query
from pathlib import Path

from services.execution_service import get_execution_service
from services.storage.azure_storage_service import get_azure_storage_service
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smau-proto/api/import", tags=["preview"])


def find_header_row_with_cuenta(df: pd.DataFrame) -> int:
    """
    Encuentra la fila que contiene la palabra 'CUENTA' en alguna columna.
    Para archivos de Sumas y Saldos.
    """
    for idx, row in df.iterrows():
        for value in row.values:
            if pd.notna(value) and isinstance(value, str):
                if 'CUENTA' in value.upper():
                    logger.info(f"Palabra 'CUENTA' encontrada en fila {idx}")
                    return int(idx)
    
    logger.warning("No se encontró la palabra 'CUENTA' en ninguna fila")
    return None


def _read_and_format_csv(file_path: str, rows: int = 10) -> dict:
    """Helper para leer CSV y formatearlo para preview"""
    df = pd.read_csv(file_path, nrows=rows)
    return {
        "converted": {
            "rows": df.fillna("").to_dict(orient='records')
        }
    }


def _read_and_format_excel(file_path: str, rows: int = 10, is_sumas_saldos: bool = False) -> dict:
    """Helper para leer Excel y formatearlo para preview"""
    if is_sumas_saldos:
        df_full = pd.read_excel(file_path, header=None)
        header_row = find_header_row_with_cuenta(df_full)
        
        if header_row is not None:
            df = pd.read_excel(file_path, header=header_row, nrows=rows)
        else:
            df = pd.read_excel(file_path, header=0, nrows=rows)
    else:
        df = pd.read_excel(file_path, nrows=rows)
    
    return {
        "converted": {
            "rows": df.fillna("").to_dict(orient='records')
        }
    }


def _download_azure_file_to_temp(azure_path: str, execution_id: str) -> tuple:
    """
    Helper para descargar archivo de Azure a temporal
    Returns: (local_file_path, temp_created_flag)
    """
    settings = get_settings()
    azure_service = get_azure_storage_service()
    
    if not azure_service.file_exists(azure_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in Azure Storage"
        )
    
    temp_dir = tempfile.gettempdir()
    filename = Path(azure_path).name.split('_', 1)[-1]
    local_file_path = os.path.join(temp_dir, f"temp_preview_{execution_id}_{filename}")
    
    azure_service.download_file(azure_path, local_file_path)
    return local_file_path, True


# ==========================================
# ENDPOINT 1: Preview Original (Convertido)
# ==========================================
@router.get("/preview/{execution_id}")
async def get_preview_original(execution_id: str, rows: int = Query(10, description="Number of rows to preview")):
    """
    Get preview of ORIGINAL converted file (before mapping).
    Shows data from result_path (converted file).
    """
    execution_service = get_execution_service()
    execution = execution_service.get_execution(execution_id)
    settings = get_settings()
    
    file_to_preview = None
    temp_file_created = False
    local_file_path = None
    
    file_type = getattr(execution, 'file_type', None)
    is_sumas_saldos = (file_type == 'Sys')
    
    try:
        # Prioridad para archivo original convertido
        if execution.result_path and execution.result_path != "":
            file_to_preview = execution.result_path
            logger.info(f"📄 Preview original - Using converted file: {file_to_preview}")
        elif execution.status == "completed" and execution.step == "validation":
            file_to_preview = execution.file_path
            logger.info(f"📄 Preview original - Using validated file: {file_to_preview}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No original file available for preview"
            )
        
        # Download from Azure if needed
        if file_to_preview.startswith("azure://") and settings.use_azure_storage:
            local_file_path, temp_file_created = _download_azure_file_to_temp(file_to_preview, execution_id)
        else:
            local_file_path = file_to_preview
            if not os.path.exists(local_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
        
        # Read and format file
        file_ext = os.path.splitext(local_file_path)[1].lower()
        
        if file_ext == '.csv':
            preview_data = _read_and_format_csv(local_file_path, rows)
        elif file_ext in ['.xlsx', '.xls']:
            preview_data = _read_and_format_excel(local_file_path, rows, is_sumas_saldos)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}"
            )
        
        return preview_data
        
    finally:
        if temp_file_created and local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Cleaned up temporary file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file: {e}")


# ==========================================
# ENDPOINT 2: Preview Mapeado (Manual Mapped)
# ==========================================
@router.get("/preview/{execution_id}/mapped")
async def get_preview_mapped(execution_id: str, rows: int = Query(10, description="Number of rows to preview")):
    """
    Get preview of MAPPED file (after manual mapping).
    Shows data from output_file (manual_mapped_Je.csv).
    """
    execution_service = get_execution_service()
    execution = execution_service.get_execution(execution_id)
    settings = get_settings()
    
    file_to_preview = None
    temp_file_created = False
    local_file_path = None
    
    try:
        # Buscar archivo mapeado manualmente
        if execution.output_file and "manual_mapped" in execution.output_file:
            file_to_preview = execution.output_file
            logger.info(f"📄 Preview mapped - Using manual mapped file: {file_to_preview}")
        
        # Fallback a archivo mapeado automático
        elif execution.mapeo_results and execution.mapeo_results.get('output_file'):
            file_to_preview = execution.mapeo_results.get('output_file')
            logger.info(f"📄 Preview mapped - Using automatic mapped file: {file_to_preview}")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No mapped file available yet. Please complete mapping first."
            )
        
        # Download from Azure if needed
        if file_to_preview.startswith("azure://") and settings.use_azure_storage:
            local_file_path, temp_file_created = _download_azure_file_to_temp(file_to_preview, execution_id)
        else:
            local_file_path = file_to_preview
            if not os.path.exists(local_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mapped file not found"
                )
        
        # Los archivos mapeados siempre son CSV
        file_ext = os.path.splitext(local_file_path)[1].lower()
        
        if file_ext != '.csv':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected CSV file for mapped preview, got: {file_ext}"
            )
        
        preview_data = _read_and_format_csv(local_file_path, rows)
        
        return preview_data
        
    finally:
        if temp_file_created and local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Cleaned up temporary file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file: {e}")