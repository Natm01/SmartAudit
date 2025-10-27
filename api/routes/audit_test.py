"""
Rutas para la gestión de pruebas de auditoría
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from models.execution import AuditTestExecRequest, AuditTestExecResponse
from services.audit_test_service import get_audit_test_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smau-proto/api/audit-test", tags=["audit-test"])


@router.post("/exec", response_model=AuditTestExecResponse)
async def create_audit_test_execution(request: AuditTestExecRequest):
    """
    Crear una nueva ejecución de prueba de auditoría en la base de datos

    Este endpoint ejecuta el procedimiento almacenado sp_insert_audit_test_exec_je_analysis
    para registrar una nueva prueba de auditoría con sus archivos de Journal Entry y Trial Balance.

    Args:
        request: Datos de la prueba de auditoría a crear

    Returns:
        Respuesta con el ID creado o información de error
    """
    try:
        logger.info(f"Creando audit test execution para project_id={request.project_id}")

        # Convertir fechas string a date objects
        try:
            period_beginning_date = datetime.strptime(request.period_beginning_date, "%Y-%m-%d").date()
            period_ending_date = datetime.strptime(request.period_ending_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de fecha inválido. Use YYYY-MM-DD. Error: {str(e)}"
            )

        # Validar que la fecha de inicio sea anterior a la de fin
        if period_beginning_date > period_ending_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Obtener el servicio
        audit_service = get_audit_test_service()

        # Ejecutar el procedimiento almacenado
        result = audit_service.insert_audit_test_exec_je_analysis(
            auth_user_id=request.auth_user_id,
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            period_beginning_date=period_beginning_date,
            period_ending_date=period_ending_date,
            fiscal_year=request.fiscal_year,
            je_original_file_name=request.je_original_file_name,
            je_file_name=request.je_file_name,
            je_file_size_bytes=request.je_file_size_bytes,
            je_file_type_code=request.je_file_type_code,
            je_file_data_structure_type_code=request.je_file_data_structure_type_code,
            je_file_extension=request.je_file_extension,
            tb_original_file_name=request.tb_original_file_name,
            tb_file_name=request.tb_file_name,
            tb_file_size_bytes=request.tb_file_size_bytes,
            tb_file_type_code=request.tb_file_type_code,
            tb_file_data_structure_type_code=request.tb_file_data_structure_type_code,
            tb_file_extension=request.tb_file_extension,
            external_gid=request.external_gid,
            correlation_id=request.correlation_id,
            language_code=request.language_code
        )

        # Verificar si hubo error
        if result['has_error']:
            logger.warning(
                f"Error en SP para project_id={request.project_id}: "
                f"{result['error_code']} - {result['error_message']}"
            )
            # Retornar el error pero con status 200 ya que el SP se ejecutó correctamente
            # El error es del negocio, no técnico
            return AuditTestExecResponse(**result)

        logger.info(
            f"Audit test execution creado exitosamente. "
            f"new_id={result['new_id']}, project_id={request.project_id}"
        )

        return AuditTestExecResponse(**result)

    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear audit test execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la ejecución de prueba de auditoría: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint para verificar que el servicio está activo"""
    return {
        "status": "healthy",
        "service": "audit-test",
        "timestamp": datetime.now().isoformat()
    }
