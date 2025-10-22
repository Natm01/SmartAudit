"""
Endpoints para la creación y gestión de ejecuciones de análisis de auditoría
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Dict, Any

from models.audit_execution import (
    AuditExecutionRequest,
    AuditExecutionResponse
)
from services.azure_sql_service import AzureSQLService

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router con prefijo
router = APIRouter(
    prefix="/smau-proto/api/audit",
    tags=["Audit Execution"]
)


@router.post(
    "/executions",
    response_model=AuditExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva ejecución de análisis de auditoría",
    description="""
    Crea una nueva ejecución de análisis de asientos contables (Journal Entries).

    **Datos requeridos del front-end:**
    - Información del proyecto (tenant_id, workspace_id, project_id)
    - Usuario autenticado (auth_user_id)
    - Período fiscal (fiscal_year, period_beginning_date, period_ending_date)
    - Metadatos del archivo Libro Diario (nombre, tamaño, extensión)
    - Metadatos del archivo Sumas y Saldos (nombre, tamaño, extensión)
    - ID de ejecución (execution_id)

    **Este endpoint:**
    1. Valida todos los datos recibidos
    2. Se conecta a Azure SQL Database
    3. Ejecuta el stored procedure `workspace.sp_insert_audit_test_exec_je_analysis`
    4. Retorna el ID de la ejecución creada y cualquier error si ocurre

    **Ejemplo de request:**
    ```json
    {
      "tenant_id": 100,
      "workspace_id": 100,
      "project_id": 1150,
      "auth_user_id": 1186,
      "execution_id": "550e8400-e29b-41d4-a716-446655440000",
      "fiscal_year": 2024,
      "period_beginning_date": "2024-01-01",
      "period_ending_date": "2024-12-31",
      "journal_entry_file": {
        "original_file_name": "Libro Diario 2024.xlsx",
        "file_name": "libro_diario_2024.xlsx",
        "file_extension": "xlsx",
        "file_size_bytes": 2048576,
        "file_type_code": "XLSX",
        "file_data_structure_type_code": "TABULAR"
      },
      "trial_balance_file": {
        "original_file_name": "Sumas y Saldos 2024.xlsx",
        "file_name": "sumas_saldos_2024.xlsx",
        "file_extension": "xlsx",
        "file_size_bytes": 1024768,
        "file_type_code": "XLSX",
        "file_data_structure_type_code": "TABULAR"
      },
      "language_code": "es-ES"
    }
    ```
    """
)
async def create_audit_execution(request: AuditExecutionRequest) -> AuditExecutionResponse:
    """
    Endpoint principal para crear una nueva ejecución de análisis de auditoría.

    Args:
        request: Objeto con todos los datos necesarios del front-end

    Returns:
        AuditExecutionResponse: Respuesta con el ID de ejecución creado o errores

    Raises:
        HTTPException: Si ocurre un error de configuración o validación
    """
    try:
        logger.info(
            f"Recibida petición para crear ejecución de auditoría. "
            f"Project ID: {request.project_id}, Execution ID: {request.execution_id}"
        )

        # Inicializar servicio de Azure SQL
        try:
            azure_sql_service = AzureSQLService()
        except ValueError as e:
            logger.error(f"Error de configuración de Azure SQL: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "CONFIG_ERROR",
                    "error_message": str(e),
                    "error_title": "Error de configuración",
                    "error_category": "CONFIGURATION"
                }
            )

        # Ejecutar stored procedure
        sp_result = azure_sql_service.execute_audit_test_exec_sp(request)

        # Preparar respuesta
        timestamp = datetime.utcnow().isoformat() + "Z"

        if sp_result.has_error:
            # El SP retornó un error
            logger.warning(
                f"SP retornó error para execution_id {request.execution_id}: "
                f"{sp_result.error_code} - {sp_result.error_message}"
            )

            return AuditExecutionResponse(
                success=False,
                execution_id=request.execution_id,
                audit_test_exec_id=sp_result.new_id,
                message="Error al crear la ejecución de auditoría",
                error_code=sp_result.error_code,
                error_message=sp_result.error_message,
                error_title=sp_result.error_title,
                error_severity=sp_result.error_severity,
                error_category=sp_result.error_category,
                timestamp=timestamp
            )

        # Éxito
        logger.info(
            f"Ejecución de auditoría creada exitosamente. "
            f"Execution ID: {request.execution_id}, DB ID: {sp_result.new_id}"
        )

        return AuditExecutionResponse(
            success=True,
            execution_id=request.execution_id,
            audit_test_exec_id=sp_result.new_id,
            message="Ejecución de auditoría creada exitosamente",
            timestamp=timestamp
        )

    except HTTPException:
        # Re-lanzar HTTPException ya manejadas
        raise

    except Exception as e:
        # Error inesperado
        logger.error(f"Error inesperado al crear ejecución: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(e),
                "error_title": "Error interno del servidor",
                "error_category": "SYSTEM"
            }
        )


@router.get(
    "/executions/{execution_id}",
    response_model=Dict[str, Any],
    summary="Obtener información de una ejecución",
    description="Obtiene el estado y detalles de una ejecución de auditoría por su ID"
)
async def get_audit_execution(execution_id: str) -> Dict[str, Any]:
    """
    Obtiene información de una ejecución específica.

    Args:
        execution_id: ID único de la ejecución

    Returns:
        Dict con información de la ejecución

    Note:
        Este endpoint requiere implementar una query a la BD para obtener la info.
        Por ahora retorna un placeholder.
    """
    # TODO: Implementar query a la BD para obtener información de la ejecución
    logger.info(f"Solicitada información de execution_id: {execution_id}")

    return {
        "execution_id": execution_id,
        "message": "Endpoint en desarrollo - implementar query a BD",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get(
    "/test-connection",
    summary="Probar conexión a Azure SQL",
    description="Endpoint de prueba para verificar la conectividad con Azure SQL Database"
)
async def test_azure_sql_connection() -> Dict[str, Any]:
    """
    Prueba la conexión a Azure SQL Database.

    Returns:
        Dict con el resultado de la prueba

    Raises:
        HTTPException: Si hay error de configuración
    """
    try:
        azure_sql_service = AzureSQLService()
        result = azure_sql_service.test_connection()

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result
            )

        return result

    except ValueError as e:
        # Error de configuración
        logger.error(f"Error de configuración: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Error de configuración: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error al probar conexión: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Error inesperado: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
