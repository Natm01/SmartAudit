# routes/sumas_saldos_validation.py
"""
Sumas y Saldos Validation Routes - Endpoints para validaciones de sumas y saldos
Solo ejecuta Fase 1 (validaciones de formato)
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile
import os


from services.execution_service import get_execution_service
from services.sumas_saldos_validation_service import get_sumas_saldos_validation_service
from services.storage.azure_storage_service import get_azure_storage_service
from utils.serialization import convert_numpy_types

router = APIRouter(prefix="/smau-proto/api/import", tags=["sumas_saldos_validation"])

# ==========================================
# Pydantic Models
# ==========================================

class SumasSaldosValidationResponse(BaseModel):
    """Response for sumas y saldos validation initiation"""
    execution_id: str
    message: str
    status: str

class SumasSaldosValidationStatusResponse(BaseModel):
    """Response for sumas y saldos validation status"""
    execution_id: str
    status: str
    validation_timestamp: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ==========================================
# Background Task
# ==========================================

async def run_sumas_saldos_validation_background(execution_id: str):
    """Background task para ejecutar validación de Sumas y Saldos"""
    execution_service = get_execution_service()
    validation_service = get_sumas_saldos_validation_service()
    azure_service = get_azure_storage_service()

    try:
        print(f"🔍 [BACKGROUND TASK INICIADO] Validación de Sumas y Saldos para: {execution_id}")

        # Update status to processing
        execution_service.update_execution(
            execution_id,
            status="processing",
            step="sumas_saldos_validation"
        )

        print(f"✅ [BACKGROUND TASK] Estado actualizado a processing con step=sumas_saldos_validation")
        print(f"🔍 Iniciando validación de Sumas y Saldos para: {execution_id}")
        
        # Get execution to find the processed file
        execution = execution_service.get_execution(execution_id)
        
        # ✅ OPCIÓN 1: Usar el path guardado en sumas_saldos_csv_path (PREFERIDO)
        if hasattr(execution, 'sumas_saldos_csv_path') and execution.sumas_saldos_csv_path:
            azure_file_path = execution.sumas_saldos_csv_path
            print(f"✅ Usando path guardado en execution.sumas_saldos_csv_path: {azure_file_path}")
        
        # ✅ OPCIÓN 2: Construir el path manualmente (FALLBACK)
        else:
            # El archivo procesado de Sumas y Saldos tiene este formato según sumas_saldos_service.py
            # Cuando se usa upload_file_chunked con file_type="Sys", el nombre es:
            # {execution_id}_mapeo_Sys.csv
            expected_filename = f"{execution_id}_mapeo_Sys.csv"
            
            # Azure Blob Storage tiene estructura plana
            # Formato: azure://container_name/blob_name
            azure_file_path = f"azure://mapeos/{expected_filename}"
            print(f"⚠️ Path no encontrado en execution, construyendo manualmente: {azure_file_path}")
        
        # Descargar archivo de Azure a un archivo temporal local
        try:
            local_file = tempfile.mktemp(suffix='.csv')
            print(f"📥 Descargando archivo desde: {azure_file_path}")
            print(f"📥 Guardando temporalmente en: {local_file}")
            
            azure_service.download_file(azure_file_path, local_file)
            print(f"✅ Archivo descargado exitosamente ({os.path.getsize(local_file)} bytes)")
            
        except Exception as e:
            error_msg = (
                f"Sumas y Saldos processed file not found.\n"
                f"Expected path: {azure_file_path}\n"
                f"Error: {str(e)}\n"
                f"Execution ID: {execution_id}\n"
                f"Has sumas_saldos_csv_path: {hasattr(execution, 'sumas_saldos_csv_path')}\n"
                f"Sumas Saldos Status: {getattr(execution, 'sumas_saldos_status', 'N/A')}"
            )
            print(f"❌ {error_msg}")
            
            # Intentar con nombres alternativos conocidos
            alternative_names = [
                f"{execution_id}_sumas_saldos.csv",
                f"{execution_id}_mapeo_Sys.csv",
            ]
            
            file_found = False
            for alt_name in alternative_names:
                try:
                    alt_path = f"azure://mapeos/{alt_name}"
                    print(f"🔄 Intentando con nombre alternativo: {alt_path}")
                    azure_service.download_file(alt_path, local_file)
                    print(f"✅ Archivo encontrado con nombre alternativo: {alt_name}")
                    file_found = True
                    break
                except:
                    continue
            
            if not file_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{error_msg}\nPlease ensure file processing is completed."
                )
        
        # Run validation (only fase 1)
        print(f"🔍 Ejecutando validación Fase 1")
        validation_results = validation_service.run_validation_fase_1(local_file)
        print(f"✅ Validación completada exitosamente")
        
        # Clean up temp file
        if os.path.exists(local_file):
            os.remove(local_file)
            print(f"🧹 Archivo temporal eliminado")
        
        # Convert numpy types to native Python types
        validation_results_clean = convert_numpy_types(validation_results)
        
        # Update execution with results
        execution_service.update_execution(
            execution_id,
            status="completed",
            step="sumas_saldos_validation_completed",
            sumas_saldos_validation_results=validation_results_clean
        )
        
        print(f"✅ Sumas y Saldos validation completed for execution {execution_id}")
        print(f"   - Total checks: {validation_results_clean.get('summary', {}).get('total_phases', 0)}")
        print(f"   - Passed: {validation_results_clean.get('summary', {}).get('passed_phases', 0)}")
        print(f"   - Failed: {validation_results_clean.get('summary', {}).get('failed_phases', 0)}")
        
    except Exception as e:
        print(f"❌ Error in sumas y saldos validation: {str(e)}")
        import traceback
        traceback.print_exc()
        
        execution_service.update_execution(
            execution_id,
            status="failed",
            step="sumas_saldos_validation_failed",
            error=f"Sumas y Saldos validation error: {str(e)}"
        )

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/validate-sumas-saldos/{execution_id}", response_model=SumasSaldosValidationResponse)
async def start_sumas_saldos_validation(
    execution_id: str,
    background_tasks: BackgroundTasks
):
    """
    Inicia proceso de validación para Sumas y Saldos.

    Solo ejecuta Fase 1 (Validaciones de Formato):
    - Valida gl_account_number
    - Valida period_beginning_balance (si existe)
    - Valida period_ending_balance
    - Valida period_activity_debit (si existe)
    - Valida period_activity_credit (si existe)

    IMPORTANTE: Este endpoint espera el archivo procesado guardado en
    execution.sumas_saldos_csv_path o busca {execution_id}_mapeo_Sys.csv
    """
    execution_service = get_execution_service()

    try:
        print(f"🚀 [POST] Iniciando validación para execution_id: {execution_id}")

        # Verify execution exists
        execution = execution_service.get_execution(execution_id)

        print(f"✅ [POST] Execution encontrado, agregando background task")

        # Start validation in background
        background_tasks.add_task(
            run_sumas_saldos_validation_background,
            execution_id
        )

        print(f"✅ [POST] Background task agregado, retornando respuesta")

        return SumasSaldosValidationResponse(
            execution_id=execution_id,
            message="Sumas y Saldos validation started",
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting sumas y saldos validation: {str(e)}"
        )

@router.get("/validate-sumas-saldos/{execution_id}/status",
            response_model=SumasSaldosValidationStatusResponse)
async def get_sumas_saldos_validation_status(execution_id: str):
    """
    Obtiene el estado y resultados de la validación de Sumas y Saldos.

    Retorna el estado actual y resultados completos si está completado.
    """
    execution_service = get_execution_service()

    try:
        execution = execution_service.get_execution(execution_id)

        print(f"📊 [STATUS] execution.step: {execution.step}, execution.status: {execution.status}")

        # Get validation results if available
        validation_results = (
            execution.sumas_saldos_validation_results
            if hasattr(execution, 'sumas_saldos_validation_results')
            else None
        )

        print(f"📊 [STATUS] validation_results present: {validation_results is not None}")

        # Determine status basándose en el step específico de validación
        current_status = "not_started"

        if execution.step == "sumas_saldos_validation_completed":
            current_status = "completed"
        elif execution.step == "sumas_saldos_validation_failed":
            current_status = "failed"
        elif execution.step == "sumas_saldos_validation":
            current_status = "processing"
        elif validation_results:
            # Si hay resultados pero el step no está actualizado
            current_status = "completed"

        print(f"📊 [STATUS] current_status: {current_status}")
        
        # Get summary if results available
        summary = None
        if validation_results:
            summary = validation_results.get('summary', {})
        
        return SumasSaldosValidationStatusResponse(
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
            detail=f"Error getting sumas y saldos validation status: {str(e)}"
        )

@router.get("/validate-sumas-saldos/{execution_id}/summary")
async def get_sumas_saldos_validation_summary(execution_id: str):
    """
    Obtiene resumen simplificado de la validación de Sumas y Saldos.
    Retorna estado por fase (solo fase 1).
    """
    execution_service = get_execution_service()

    try:
        execution = execution_service.get_execution(execution_id)

        print(f"📊 [SUMMARY] execution.step: {execution.step}, execution.status: {execution.status}")

        validation_results = (
            execution.sumas_saldos_validation_results
            if hasattr(execution, 'sumas_saldos_validation_results')
            else None
        )

        print(f"📊 [SUMMARY] validation_results present: {validation_results is not None}")

        # Verificar si la validación está en progreso
        # La validación está en progreso si:
        # 1. El step es exactamente "sumas_saldos_validation" (durante la ejecución)
        # 2. El status es "processing" y no tenemos resultados aún
        is_validating = (
            execution.step == "sumas_saldos_validation" or
            (execution.status == "processing" and not validation_results)
        )

        print(f"📊 [SUMMARY] is_validating: {is_validating}")

        if not validation_results:
            # Si el step indica que completó pero no hay resultados, es porque no se guardaron
            # Esto puede pasar si el modelo no tenía el campo cuando se ejecutó
            if execution.step == "sumas_saldos_validation_completed":
                print(f"⚠️ [SUMMARY] Validación completada pero resultados no disponibles")
                return {
                    "execution_id": execution_id,
                    "status": "completed",
                    "phases": [
                        {"phase": 1, "name": "Validaciones de Formato", "status": "completed"}
                    ],
                    "progress": {
                        "completed": 1,
                        "total": 1
                    },
                    "warning": "Validation completed but results not saved (field may not exist in execution model)"
                }

            # Si el step indica que falló
            if execution.step == "sumas_saldos_validation_failed":
                print(f"⚠️ [SUMMARY] Validación falló")
                return {
                    "execution_id": execution_id,
                    "status": "completed_with_errors",
                    "phases": [
                        {"phase": 1, "name": "Validaciones de Formato", "status": "failed"}
                    ],
                    "progress": {
                        "completed": 1,
                        "total": 1
                    }
                }

            # Si está validando, mostrar status "validating", sino "pending"
            phase_status = "validating" if is_validating else "pending"
            overall_status = "processing" if is_validating else "not_started"

            print(f"📊 [SUMMARY] Retornando status: {overall_status}, phase_status: {phase_status}")

            return {
                "execution_id": execution_id,
                "status": overall_status,
                "phases": [
                    {"phase": 1, "name": "Validaciones de Formato", "status": phase_status}
                ],
                "progress": {
                    "completed": 0,
                    "total": 1
                }
            }
        
        # Cuando hay resultados, construir las fases
        phases = []
        fase_1 = validation_results.get('fase_1_formato', {})

        phase_status = "completed" if fase_1.get('is_phase_valid') else "failed"

        phases.append({
            "phase": 1,
            "name": "Validaciones de Formato",
            "status": phase_status,
            "checks": fase_1.get('summary', {})
        })

        completed_phases = 1

        overall_status = "completed" if fase_1.get('is_phase_valid') else "completed_with_errors"
        
        return {
            "execution_id": execution_id,
            "status": overall_status,
            "file_type": "sumas_saldos",
            "phases": phases,
            "progress": {
                "completed": completed_phases,
                "total": 1,
                "has_errors": not fase_1.get('is_phase_valid', True) if fase_1 else False
            },
            "summary": validation_results.get('summary', {}),
            "validation_timestamp": validation_results.get('validation_timestamp')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sumas y saldos validation summary: {str(e)}"
        )

@router.get("/validate-sumas-saldos/{execution_id}/phase/1")
async def get_sumas_saldos_phase_details(execution_id: str):
    """
    Obtiene resultados detallados de la fase 1 de validación.
    """
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        validation_results = (
            execution.sumas_saldos_validation_results 
            if hasattr(execution, 'sumas_saldos_validation_results') 
            else None
        )
        
        if not validation_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation results not found. Please run validations first."
            )
        
        fase_1 = validation_results.get('fase_1_formato', {})
        
        if not fase_1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Phase 1 results not found"
            )
        
        return {
            "execution_id": execution_id,
            "phase": 1,
            "phase_name": "Validaciones de Formato",
            "details": fase_1,
            "validation_timestamp": validation_results.get('validation_timestamp')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting phase 1 details: {str(e)}"
        )