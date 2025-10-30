"""
Servicio para ejecutar procedimientos almacenados de pruebas de auditoría
"""
import logging
from typing import Dict, Any, Optional
from datetime import date
import pyodbc

from db.connection import get_db_connection

logger = logging.getLogger(__name__)


class AuditTestExecutionService:
    """Servicio para manejar la ejecución de pruebas de auditoría en la base de datos"""

    @staticmethod
    def _build_storage_relative_path(project_id: int, execution_id: int) -> str:
        """
        Construir el path relativo de storage

        Args:
            tenant_id: ID del tenant
            workspace_id: ID del workspace

        Returns:
            Path relativo: tenants/{tenant_id}/workspaces/{workspace_id}/
        """
        return f"libro-diario-resultados/{project_id}/{execution_id}"

    @staticmethod
    def insert_audit_test_exec_je_analysis(
        # Parámetros de usuario y contexto (sin defaults)
        auth_user_id: int,
        tenant_id: int,
        workspace_id: int,
        project_id: int,

        # Parámetros globales (sin defaults)
        period_beginning_date: date,
        period_ending_date: date,
        fiscal_year: int,

        # Parámetros de Journal Entry (sin defaults)
        je_original_file_name: str,
        je_file_name: str,
        je_file_size_bytes: int,

        # Parámetros de Trial Balance (sin defaults)
        tb_original_file_name: str,
        tb_file_name: str,
        tb_file_size_bytes: int,

        # Parámetros de Journal Entry (con defaults)
        je_file_type_code: str = 'CSV',
        je_file_data_structure_type_code: str = 'TABULAR',
        je_file_extension: str = 'csv',

        # Parámetros de Trial Balance (con defaults)
        tb_file_type_code: str = 'CSV',
        tb_file_data_structure_type_code: str = 'TABULAR',
        tb_file_extension: str = 'csv',

        # Parámetros opcionales
        external_gid: Optional[str] = None,
        correlation_id: Optional[str] = None,
        language_code: str = 'es-ES'
    ) -> Dict[str, Any]:
        """
        Ejecutar el procedimiento almacenado sp_insert_audit_test_exec_je_analysis

        Args:
            auth_user_id: ID del usuario autenticado
            tenant_id: ID del tenant
            workspace_id: ID del workspace
            project_id: ID del proyecto
            period_beginning_date: Fecha de inicio del período
            period_ending_date: Fecha de fin del período
            fiscal_year: Año fiscal
            je_original_file_name: Nombre original del archivo de Journal Entry
            je_file_name: Nombre normalizado del archivo de Journal Entry
            je_file_size_bytes: Tamaño del archivo de Journal Entry en bytes
            je_file_type_code: Tipo de archivo JE (CSV, XLS)
            je_file_data_structure_type_code: Estructura de datos JE (TABULAR, HEADER_AND_LINES)
            je_file_extension: Extensión del archivo JE
            tb_original_file_name: Nombre original del archivo de Trial Balance
            tb_file_name: Nombre normalizado del archivo de Trial Balance
            tb_file_size_bytes: Tamaño del archivo de Trial Balance en bytes
            tb_file_type_code: Tipo de archivo TB (CSV, XLS)
            tb_file_data_structure_type_code: Estructura de datos TB (TABULAR, HEADER_AND_LINES)
            tb_file_extension: Extensión del archivo TB
            external_gid: GUID externo (opcional)
            correlation_id: ID de correlación (opcional)
            language_code: Código de idioma (por defecto 'es-ES')

        Returns:
            Dict con:
                - new_id: ID del registro creado
                - has_error: Indica si hubo error
                - error_code: Código del error (si aplica)
                - error_message: Mensaje del error (si aplica)
                - error_title: Título del error (si aplica)
                - error_severity: Severidad del error (si aplica)
                - error_category: Categoría del error (si aplica)
        """
        logger.info(f"Ejecutando sp_insert_audit_test_exec_je_analysis para project_id={project_id}")

        # Construir storage_relative_path
        storage_relative_path = AuditTestExecutionService._build_storage_relative_path(
            project_id, external_gid
        )

        # Log detallado de TODOS los parámetros que se enviarán al SP
        logger.info("=" * 80)
        logger.info("📋 PARÁMETROS DEL SP sp_insert_audit_test_exec_je_analysis:")
        logger.info("=" * 80)
        logger.info("👤 Usuario y Contexto:")
        logger.info(f"   - auth_user_id: {auth_user_id}")
        logger.info(f"   - tenant_id: {tenant_id}")
        logger.info(f"   - workspace_id: {workspace_id}")
        logger.info(f"   - project_id: {project_id}")
        logger.info("")
        logger.info("📅 Período:")
        logger.info(f"   - period_beginning_date: {period_beginning_date}")
        logger.info(f"   - period_ending_date: {period_ending_date}")
        logger.info(f"   - fiscal_year: {fiscal_year}")
        logger.info("")
        logger.info("💾 Storage:")
        logger.info(f"   - storage_relative_path: {storage_relative_path}")
        logger.info("")
        logger.info("📄 Journal Entry (JE):")
        logger.info(f"   - je_file_type_code: {je_file_type_code}")
        logger.info(f"   - je_file_data_structure_type_code: {je_file_data_structure_type_code}")
        logger.info(f"   - je_original_file_name: {je_original_file_name}")
        logger.info(f"   - je_file_name: {je_file_name}")
        logger.info(f"   - je_file_extension: {je_file_extension}")
        logger.info(f"   - je_file_size_bytes: {je_file_size_bytes:,} bytes ({je_file_size_bytes / (1024*1024):.2f} MB)")
        logger.info("")
        logger.info("📊 Trial Balance (TB):")
        logger.info(f"   - tb_file_type_code: {tb_file_type_code}")
        logger.info(f"   - tb_file_data_structure_type_code: {tb_file_data_structure_type_code}")
        logger.info(f"   - tb_original_file_name: {tb_original_file_name}")
        logger.info(f"   - tb_file_name: {tb_file_name}")
        logger.info(f"   - tb_file_extension: {tb_file_extension}")
        logger.info(f"   - tb_file_size_bytes: {tb_file_size_bytes:,} bytes ({tb_file_size_bytes / (1024*1024):.2f} MB)")
        logger.info("")
        logger.info("🔧 Opcionales:")
        logger.info(f"   - external_gid: {external_gid}")
        logger.info(f"   - correlation_id: {correlation_id}")
        logger.info(f"   - language_code: {language_code}")
        logger.info("=" * 80)

        try:
            with get_db_connection() as conn:
                # Activar autocommit para evitar conflictos de transacciones con el SP
                conn.autocommit = True
                cursor = conn.cursor()

                # Ejecutar el procedimiento almacenado
                # pyodbc maneja OUTPUT params con DECLARE/SET en T-SQL
                sql = """
                    DECLARE @new_id BIGINT;
                    DECLARE @has_error BIT;
                    DECLARE @error_code NVARCHAR(50);
                    DECLARE @error_message NVARCHAR(MAX);
                    DECLARE @error_title NVARCHAR(255);
                    DECLARE @error_severity NVARCHAR(20);
                    DECLARE @error_category NVARCHAR(50);

                    EXEC [workspace].[sp_insert_audit_test_exec_je_analysis]
                        @auth_user_id = ?,
                        @tenant_id = ?,
                        @workspace_id = ?,
                        @project_id = ?,
                        @external_gid = ?,
                        @period_beginning_date = ?,
                        @period_ending_date = ?,
                        @fiscal_year = ?,
                        @storage_relative_path = ?,
                        @je_file_type_code = ?,
                        @je_file_data_structure_type_code = ?,
                        @je_original_file_name = ?,
                        @je_file_name = ?,
                        @je_file_extension = ?,
                        @je_file_size_bytes = ?,
                        @tb_file_type_code = ?,
                        @tb_file_data_structure_type_code = ?,
                        @tb_original_file_name = ?,
                        @tb_file_name = ?,
                        @tb_file_extension = ?,
                        @tb_file_size_bytes = ?,
                        @correlation_id = ?,
                        @language_code = ?,
                        @new_id = @new_id OUTPUT,
                        @has_error = @has_error OUTPUT,
                        @error_code = @error_code OUTPUT,
                        @error_message = @error_message OUTPUT,
                        @error_title = @error_title OUTPUT,
                        @error_severity = @error_severity OUTPUT,
                        @error_category = @error_category OUTPUT;

                    SELECT @new_id AS new_id,
                           @has_error AS has_error,
                           @error_code AS error_code,
                           @error_message AS error_message,
                           @error_title AS error_title,
                           @error_severity AS error_severity,
                           @error_category AS error_category;
                """

                cursor.execute(sql, (
                    auth_user_id,
                    tenant_id,
                    workspace_id,
                    project_id,
                    external_gid,
                    period_beginning_date,
                    period_ending_date,
                    fiscal_year,
                    storage_relative_path,
                    je_file_type_code,
                    je_file_data_structure_type_code,
                    je_original_file_name,
                    je_file_name,
                    je_file_extension,
                    je_file_size_bytes,
                    tb_file_type_code,
                    tb_file_data_structure_type_code,
                    tb_original_file_name,
                    tb_file_name,
                    tb_file_extension,
                    tb_file_size_bytes,
                    correlation_id,
                    language_code
                ))

                # Obtener los resultados (OUTPUT params)
                row = cursor.fetchone()

                # No hacer commit explícito - el SP maneja sus propias transacciones

                # Extraer valores de salida
                result = {
                    'new_id': row.new_id if row and row.new_id is not None else None,
                    'has_error': bool(row.has_error) if row and row.has_error is not None else False,
                    'error_code': row.error_code if row and row.error_code is not None else None,
                    'error_message': row.error_message if row and row.error_message is not None else None,
                    'error_title': row.error_title if row and row.error_title is not None else None,
                    'error_severity': row.error_severity if row and row.error_severity is not None else None,
                    'error_category': row.error_category if row and row.error_category is not None else None
                }

                if result['has_error']:
                    logger.error(
                        f"Error en SP: {result['error_code']} - {result['error_message']}"
                    )
                else:
                    logger.info(f"SP ejecutado exitosamente. new_id={result['new_id']}")

                return result

        except pyodbc.Error as e:
            logger.error(f"Error de base de datos al ejecutar SP: {e}")
            return {
                'new_id': None,
                'has_error': True,
                'error_code': 'DB_ERROR',
                'error_message': str(e),
                'error_title': 'Error de Base de Datos',
                'error_severity': 'HIGH',
                'error_category': 'DATABASE'
            }
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar SP: {e}")
            return {
                'new_id': None,
                'has_error': True,
                'error_code': 'UNEXPECTED_ERROR',
                'error_message': str(e),
                'error_title': 'Error Inesperado',
                'error_severity': 'HIGH',
                'error_category': 'SYSTEM'
            }


def get_audit_test_service() -> AuditTestExecutionService:
    """Obtener instancia del servicio de pruebas de auditoría"""
    return AuditTestExecutionService()
