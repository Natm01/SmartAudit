# routes/results_storage.py
"""
Results Storage Routes - Endpoints para guardar resultados validados
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from services.execution_service import get_execution_service
from services.results_storage_service import get_results_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smau-proto/api/import", tags=["results_storage"])

# ==========================================
# Pydantic Models
# ==========================================

class SaveResultsRequest(BaseModel):
    """Request to save validated results"""
    project_id: str

class SaveResultsResponse(BaseModel):
    """Response for save results operation"""
    execution_id: str
    message: str
    status: str
    saved_files: Optional[Dict[str, str]] = None
    error: Optional[str] = None

class SaveResultsStatusResponse(BaseModel):
    """Response for checking if results can be saved"""
    execution_id: str
    can_save: bool
    validation_status: Dict[str, Any]
    message: str

# ==========================================
# Background Task
# ==========================================

async def save_results_background(execution_id: str, project_id: str):
    """Background task to save validated results"""
    execution_service = get_execution_service()
    results_service = get_results_storage_service()

    try:
        logger.info(f"Starting background task to save results for execution {execution_id}")

        # Get execution
        execution = execution_service.get_execution(execution_id)

        # Save results
        saved_files = results_service.save_validated_results(execution, project_id)

        # Update execution with saved files info
        execution_service.update_execution(
            execution_id,
            status="completed",
            step="results_saved",
            stats={
                **(execution.stats or {}),
                "saved_results": {
                    "timestamp": datetime.now().isoformat(),
                    "project_id": project_id,
                    "files": saved_files
                }
            }
        )

        logger.info(f"✅ Results saved successfully for execution {execution_id}")
        logger.info(f"   - Files saved: {list(saved_files.keys())}")

    except Exception as e:
        error_msg = f"Error saving results: {str(e)}"
        logger.error(f"❌ {error_msg}")
        execution_service.update_execution(
            execution_id,
            status="failed",
            step="results_save_failed",
            error=error_msg
        )

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/save-results/{execution_id}", response_model=SaveResultsResponse)
async def save_validated_results(
    execution_id: str,
    request: SaveResultsRequest,
    background_tasks: BackgroundTasks
):
    """
    Guardar resultados validados en el contenedor libro-diario-resultados.

    Solo guarda los archivos si TODAS las validaciones pasaron correctamente.

    Estructura de carpetas:
    - libro-diario-resultados/{project_id}/{execution_id}/sys/{execution_id}-sys.csv
    - libro-diario-resultados/{project_id}/{execution_id}/je/{execution_id}-je-cabecera.csv
    - libro-diario-resultados/{project_id}/{execution_id}/je/{execution_id}-je-detalle.csv

    Args:
        execution_id: ID de la ejecución
        request: Solicitud con project_id

    Returns:
        SaveResultsResponse con información de los archivos guardados
    """
    execution_service = get_execution_service()

    try:
        # Verify execution exists
        execution = execution_service.get_execution(execution_id)

        # Check validation status for each file type
        results_service = get_results_storage_service()
        validation_status = results_service._check_validations_status(execution)

        can_save_journal = validation_status["journal_entries"]["can_save"]
        can_save_trial = validation_status["trial_balance"]["can_save"]

        if not can_save_journal and not can_save_trial:
            errors = []
            if validation_status["journal_entries"]["exists"]:
                errors.append(f"Libro Diario: {validation_status['journal_entries']['error']}")
            if validation_status["trial_balance"]["exists"]:
                errors.append(f"Sumas y Saldos: {validation_status['trial_balance']['error']}")
            if not errors:
                errors.append("No hay archivos con validaciones exitosas para guardar")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(errors)
            )

        # Start save in background
        background_tasks.add_task(
            save_results_background,
            execution_id,
            request.project_id
        )

        return SaveResultsResponse(
            execution_id=execution_id,
            message="Guardado de resultados iniciado",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating save results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar guardado de resultados: {str(e)}"
        )

@router.get("/save-results/{execution_id}/status", response_model=SaveResultsStatusResponse)
async def check_save_results_status(execution_id: str):
    """
    Verificar si los resultados pueden ser guardados.

    Revisa el estado de las validaciones y determina si se pueden guardar los resultados.

    Args:
        execution_id: ID de la ejecución

    Returns:
        SaveResultsStatusResponse con información del estado
    """
    execution_service = get_execution_service()
    results_service = get_results_storage_service()

    try:
        # Get execution
        execution = execution_service.get_execution(execution_id)

        # Check validation status for each file type
        validation_check = results_service._check_validations_status(execution)

        # Build validation status with detailed information
        validation_status = {
            "journal_entries": {
                "exists": validation_check["journal_entries"]["exists"],
                "validated": execution.validation_rules_results is not None,
                "passed": validation_check["journal_entries"]["can_save"],
                "error": validation_check["journal_entries"]["error"]
            },
            "trial_balance": {
                "exists": validation_check["trial_balance"]["exists"],
                "validated": execution.sumas_saldos_validation_results is not None,
                "passed": validation_check["trial_balance"]["can_save"],
                "error": validation_check["trial_balance"]["error"]
            }
        }

        if execution.validation_rules_results:
            journal_summary = execution.validation_rules_results.get("summary", {})
            validation_status["journal_entries"]["summary"] = journal_summary

        if execution.sumas_saldos_validation_results:
            trial_summary = execution.sumas_saldos_validation_results.get("summary", {})
            validation_status["trial_balance"]["summary"] = trial_summary

        can_save_journal = validation_check["journal_entries"]["can_save"]
        can_save_trial = validation_check["trial_balance"]["can_save"]
        can_save = can_save_journal or can_save_trial

        if can_save:
            files_to_save = []
            if can_save_journal:
                files_to_save.append("Libro Diario")
            if can_save_trial:
                files_to_save.append("Sumas y Saldos")
            message = f"Se pueden guardar: {', '.join(files_to_save)}"
        else:
            message = "Ningún archivo tiene validaciones exitosas"

        return SaveResultsStatusResponse(
            execution_id=execution_id,
            can_save=can_save,
            validation_status=validation_status,
            message=message
        )

    except Exception as e:
        logger.error(f"Error checking save results status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar estado: {str(e)}"
        )

@router.get("/save-results/{execution_id}/files", response_model=Dict[str, str])
async def get_saved_results_files(execution_id: str):
    """
    Obtener las rutas de los archivos guardados para una ejecución.

    Args:
        execution_id: ID de la ejecución

    Returns:
        Diccionario con las rutas de los archivos guardados
    """
    execution_service = get_execution_service()

    try:
        # Get execution
        execution = execution_service.get_execution(execution_id)

        # Check if results have been saved
        if not execution.stats or "saved_results" not in execution.stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron resultados guardados para esta ejecución"
            )

        saved_results = execution.stats.get("saved_results", {})
        return saved_results.get("files", {})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved results files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener archivos guardados: {str(e)}"
        )
