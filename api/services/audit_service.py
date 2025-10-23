# services/audit_service.py
"""
Servicio de auditoría para registrar importaciones en Azure SQL Database
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os

from services.database.azure_sql_connection import AzureSqlConnection

logger = logging.getLogger(__name__)


class AuditService:
    """Servicio para registrar auditorías de importación en Azure SQL"""

    def __init__(self):
        """Inicializa el servicio de auditoría"""
        self.sql_connection: Optional[AzureSqlConnection] = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Inicializa la conexión a Azure SQL Database"""
        try:
            server = os.getenv("AZURE_SQL_SERVER")
            database = os.getenv("AZURE_SQL_DATABASE")
            connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")

            if not server or not database:
                logger.warning(
                    "Azure SQL no configurado. Variables requeridas: "
                    "AZURE_SQL_SERVER, AZURE_SQL_DATABASE"
                )
                return

            self.sql_connection = AzureSqlConnection(
                server=server,
                database=database,
                connection_string=connection_string if connection_string else None
            )

            logger.info("Conexión a Azure SQL inicializada correctamente")

        except Exception as e:
            logger.error(f"Error inicializando conexión a Azure SQL: {e}")
            self.sql_connection = None

    def _parse_period(self, period: str) -> tuple[date, date, int]:
        """
        Parsea el período y retorna (fecha_inicio, fecha_fin, año_fiscal)

        Args:
            period: Período en formato YYYY-MM (ej: "2024-12")

        Returns:
            Tupla con (period_beginning_date, period_ending_date, fiscal_year)
        """
        try:
            # Parsear año y mes
            year, month = map(int, period.split('-'))

            # Fecha de fin: último día del mes
            period_ending_date = date(year, month, 1) + relativedelta(months=1, days=-1)

            # Fecha de inicio: primer día del mes
            period_beginning_date = date(year, month, 1)

            # Año fiscal
            fiscal_year = year

            return period_beginning_date, period_ending_date, fiscal_year

        except Exception as e:
            logger.error(f"Error parseando período '{period}': {e}")
            # Valores por defecto
            today = date.today()
            return (
                date(today.year, 1, 1),  # Inicio del año actual
                date(today.year, 12, 31),  # Fin del año actual
                today.year
            )

    def _get_file_type_code(self, file_extension: str) -> str:
        """
        Determina el tipo de archivo basado en la extensión

        Args:
            file_extension: Extensión del archivo (.csv, .xlsx, etc.)

        Returns:
            Código de tipo de archivo ('CSV' o 'XLS')
        """
        ext = file_extension.lower().lstrip('.')
        if ext in ['xlsx', 'xls']:
            return 'XLS'
        return 'CSV'

    def _get_storage_path(
        self,
        tenant_id: int,
        workspace_id: int,
        project_id: int
    ) -> str:
        """
        Construye el path relativo de almacenamiento

        Returns:
            Path en formato: tenants/{tenant_id}/workspaces/{workspace_id}/projects/{project_id}/
        """
        return f"tenants/{tenant_id}/workspaces/{workspace_id}/projects/{project_id}/"

    def register_import_execution(
        self,
        # Datos del proyecto
        project_id: int,
        period: str,

        # Datos del Journal Entry (Libro Diario)
        je_original_file_name: str,
        je_file_name: str,
        je_file_extension: str,
        je_file_size_bytes: int,

        # Datos del Trial Balance (Sumas y Saldos) - Opcionales
        tb_original_file_name: Optional[str] = None,
        tb_file_name: Optional[str] = None,
        tb_file_extension: Optional[str] = None,
        tb_file_size_bytes: Optional[int] = None,

        # Parámetros del sistema (con valores por defecto)
        auth_user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        external_gid: Optional[str] = None,
        correlation_id: Optional[str] = None,
        language_code: str = "es-ES"
    ) -> Optional[int]:
        """
        Registra una ejecución de importación en la base de datos de auditoría

        Args:
            project_id: ID del proyecto
            period: Período en formato YYYY-MM
            je_original_file_name: Nombre original del archivo de Journal Entry
            je_file_name: Nombre normalizado del archivo JE
            je_file_extension: Extensión del archivo JE
            je_file_size_bytes: Tamaño en bytes del archivo JE
            tb_original_file_name: Nombre original del archivo de Trial Balance
            tb_file_name: Nombre normalizado del archivo TB
            tb_file_extension: Extensión del archivo TB
            tb_file_size_bytes: Tamaño en bytes del archivo TB
            auth_user_id: ID del usuario autenticado
            tenant_id: ID del tenant
            workspace_id: ID del workspace
            external_gid: GUID externo (opcional)
            correlation_id: ID de correlación (opcional)
            language_code: Código de idioma

        Returns:
            ID de la auditoría creada o None si falla
        """
        if not self.sql_connection:
            logger.warning("Conexión a Azure SQL no disponible. Registro omitido.")
            return None

        try:
            # Obtener valores de variables de entorno si no se proporcionan
            tenant_id = tenant_id or int(os.getenv("AZURE_SQL_TENANT_ID", "101"))
            workspace_id = workspace_id or int(os.getenv("AZURE_SQL_WORKSPACE_ID", "101"))
            auth_user_id = auth_user_id or int(os.getenv("AZURE_SQL_DEFAULT_USER_ID", "1"))

            # Parsear período
            period_beginning_date, period_ending_date, fiscal_year = self._parse_period(period)

            # Construir storage path
            storage_relative_path = self._get_storage_path(tenant_id, workspace_id, project_id)

            # Determinar tipos de archivo
            je_file_type_code = self._get_file_type_code(je_file_extension)

            # Trial Balance (puede ser None)
            tb_file_type_code = None
            if tb_file_extension:
                tb_file_type_code = self._get_file_type_code(tb_file_extension)

            # Ejecutar stored procedure
            with self.sql_connection as conn:
                cursor = conn.cursor()

                # Preparar parámetros de salida
                new_id = cursor.var(int)
                has_error = cursor.var(bool)
                error_code = cursor.var(str)
                error_message = cursor.var(str)
                error_title = cursor.var(str)
                error_severity = cursor.var(str)
                error_category = cursor.var(str)

                # Llamar al stored procedure
                cursor.execute(
                    """
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
                        @je_file_data_structure_type_code = 'TABULAR',
                        @je_original_file_name = ?,
                        @je_file_name = ?,
                        @je_file_extension = ?,
                        @je_file_size_bytes = ?,
                        @tb_file_type_code = ?,
                        @tb_file_data_structure_type_code = 'TABULAR',
                        @tb_original_file_name = ?,
                        @tb_file_name = ?,
                        @tb_file_extension = ?,
                        @tb_file_size_bytes = ?,
                        @correlation_id = ?,
                        @language_code = ?,
                        @new_id = ? OUTPUT,
                        @has_error = ? OUTPUT,
                        @error_code = ? OUTPUT,
                        @error_message = ? OUTPUT,
                        @error_title = ? OUTPUT,
                        @error_severity = ? OUTPUT,
                        @error_category = ? OUTPUT
                    """,
                    (
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
                        je_original_file_name,
                        je_file_name,
                        je_file_extension,
                        je_file_size_bytes,
                        tb_file_type_code,
                        tb_original_file_name,
                        tb_file_name,
                        tb_file_extension,
                        tb_file_size_bytes,
                        correlation_id,
                        language_code,
                        new_id,
                        has_error,
                        error_code,
                        error_message,
                        error_title,
                        error_severity,
                        error_category
                    )
                )

                # Obtener valores de salida
                audit_id = new_id.getvalue()
                has_error_value = has_error.getvalue()

                if has_error_value:
                    logger.error(
                        f"Error en stored procedure: "
                        f"Code={error_code.getvalue()}, "
                        f"Message={error_message.getvalue()}"
                    )
                    return None

                logger.info(f"Auditoría registrada exitosamente con ID: {audit_id}")
                return audit_id

        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}", exc_info=True)
            return None

    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos

        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        if not self.sql_connection:
            return False

        return self.sql_connection.test_connection()


# Singleton del servicio de auditoría
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """
    Obtiene la instancia global del servicio de auditoría

    Returns:
        Instancia de AuditService
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
