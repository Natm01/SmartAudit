"""
Servicio para conexión y ejecución de stored procedures en Azure SQL Database
"""
import pyodbc
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from models.audit_execution import (
    AuditExecutionRequest,
    StoredProcedureResult
)

logger = logging.getLogger(__name__)


class AzureSQLService:
    """
    Servicio para ejecutar operaciones en Azure SQL Database.
    Maneja la conexión y ejecución de stored procedures.
    """

    def __init__(self):
        """
        Inicializa el servicio con las credenciales desde variables de entorno.

        Variables de entorno requeridas:
        - AZURE_SQL_SERVER: Nombre del servidor (ej: smau-dev-sql.database.windows.net)
        - AZURE_SQL_DATABASE: Nombre de la base de datos
        - AZURE_SQL_USERNAME: Usuario de la base de datos
        - AZURE_SQL_PASSWORD: Contraseña del usuario
        - AZURE_SQL_DRIVER: Driver ODBC (default: ODBC Driver 18 for SQL Server)
        """
        self.server = os.getenv('AZURE_SQL_SERVER')
        self.database = os.getenv('AZURE_SQL_DATABASE')
        self.username = os.getenv('AZURE_SQL_USERNAME')
        self.password = os.getenv('AZURE_SQL_PASSWORD')
        self.driver = os.getenv('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')

        # Validar que todas las variables estén configuradas
        self._validate_config()

        # Construir connection string
        self.connection_string = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "Encrypt=yes;TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

    def _validate_config(self):
        """Validar que todas las variables de entorno requeridas estén configuradas"""
        missing_vars = []

        if not self.server:
            missing_vars.append('AZURE_SQL_SERVER')
        if not self.database:
            missing_vars.append('AZURE_SQL_DATABASE')
        if not self.username:
            missing_vars.append('AZURE_SQL_USERNAME')
        if not self.password:
            missing_vars.append('AZURE_SQL_PASSWORD')

        if missing_vars:
            error_msg = f"Variables de entorno faltantes: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Azure SQL configurado: {self.server}/{self.database}")

    def get_connection(self) -> pyodbc.Connection:
        """
        Crear y retornar una conexión a Azure SQL Database.

        Returns:
            pyodbc.Connection: Conexión activa a la base de datos

        Raises:
            Exception: Si no se puede establecer la conexión
        """
        try:
            conn = pyodbc.connect(self.connection_string)
            logger.debug("Conexión a Azure SQL establecida exitosamente")
            return conn
        except pyodbc.Error as e:
            logger.error(f"Error al conectar con Azure SQL: {str(e)}")
            raise Exception(f"No se pudo conectar a Azure SQL Database: {str(e)}")

    def execute_audit_test_exec_sp(
        self,
        request: AuditExecutionRequest
    ) -> StoredProcedureResult:
        """
        Ejecuta el stored procedure sp_insert_audit_test_exec_je_analysis.

        Args:
            request: Objeto con todos los parámetros necesarios

        Returns:
            StoredProcedureResult: Resultado de la ejecución del SP

        Raises:
            Exception: Si ocurre un error durante la ejecución
        """
        conn = None
        cursor = None

        try:
            # Establecer conexión
            conn = self.get_connection()
            cursor = conn.cursor()

            logger.info(f"Ejecutando SP para execution_id: {request.execution_id}")

            # Preparar parámetros de salida
            new_id = cursor.var(int)
            has_error = cursor.var(bool)
            error_code = cursor.var(str, 50)
            error_message = cursor.var(str)
            error_title = cursor.var(str, 255)
            error_severity = cursor.var(str, 20)
            error_category = cursor.var(str, 50)

            # Construir el CALL al stored procedure con parámetros nombrados
            sp_call = """
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
                -- Journal Entry params
                @je_file_type_code = ?,
                @je_file_data_structure_type_code = ?,
                @je_original_file_name = ?,
                @je_file_name = ?,
                @je_file_extension = ?,
                @je_file_size_bytes = ?,
                -- Trial Balance params
                @tb_file_type_code = ?,
                @tb_file_data_structure_type_code = ?,
                @tb_original_file_name = ?,
                @tb_file_name = ?,
                @tb_file_extension = ?,
                @tb_file_size_bytes = ?,
                -- Optional params
                @correlation_id = ?,
                @language_code = ?,
                -- Output params
                @new_id = @new_id OUTPUT,
                @has_error = @has_error OUTPUT,
                @error_code = @error_code OUTPUT,
                @error_message = @error_message OUTPUT,
                @error_title = @error_title OUTPUT,
                @error_severity = @error_severity OUTPUT,
                @error_category = @error_category OUTPUT;

            SELECT @new_id as new_id, @has_error as has_error, @error_code as error_code,
                   @error_message as error_message, @error_title as error_title,
                   @error_severity as error_severity, @error_category as error_category;
            """

            # Preparar parámetros en el orden correcto
            params = (
                request.auth_user_id,
                request.tenant_id,
                request.workspace_id,
                request.project_id,
                request.external_gid,
                request.period_beginning_date.strftime('%Y-%m-%d'),
                request.period_ending_date.strftime('%Y-%m-%d'),
                request.fiscal_year,
                request.storage_relative_path,
                # Journal Entry
                request.journal_entry_file.file_type_code,
                request.journal_entry_file.file_data_structure_type_code,
                request.journal_entry_file.original_file_name,
                request.journal_entry_file.file_name,
                request.journal_entry_file.file_extension,
                request.journal_entry_file.file_size_bytes,
                # Trial Balance
                request.trial_balance_file.file_type_code,
                request.trial_balance_file.file_data_structure_type_code,
                request.trial_balance_file.original_file_name,
                request.trial_balance_file.file_name,
                request.trial_balance_file.file_extension,
                request.trial_balance_file.file_size_bytes,
                # Optional
                request.correlation_id,
                request.language_code,
            )

            # Ejecutar stored procedure
            cursor.execute(sp_call, params)

            # Obtener resultados (la última SELECT)
            row = cursor.fetchone()

            if row:
                result = StoredProcedureResult(
                    new_id=row.new_id,
                    has_error=bool(row.has_error) if row.has_error is not None else False,
                    error_code=row.error_code if row.error_code else None,
                    error_message=row.error_message if row.error_message else None,
                    error_title=row.error_title if row.error_title else None,
                    error_severity=row.error_severity if row.error_severity else None,
                    error_category=row.error_category if row.error_category else None,
                )
            else:
                # Si no hay fila de resultado, asumir éxito
                result = StoredProcedureResult(
                    new_id=None,
                    has_error=False
                )

            # Commit de la transacción
            conn.commit()

            logger.info(
                f"SP ejecutado exitosamente. new_id: {result.new_id}, "
                f"has_error: {result.has_error}"
            )

            return result

        except pyodbc.Error as e:
            # Error de base de datos
            logger.error(f"Error de SQL al ejecutar SP: {str(e)}")
            if conn:
                conn.rollback()

            return StoredProcedureResult(
                new_id=None,
                has_error=True,
                error_code="SQL_ERROR",
                error_message=str(e),
                error_title="Error de base de datos",
                error_severity="HIGH",
                error_category="DATABASE"
            )

        except Exception as e:
            # Error general
            logger.error(f"Error general al ejecutar SP: {str(e)}")
            if conn:
                conn.rollback()

            return StoredProcedureResult(
                new_id=None,
                has_error=True,
                error_code="EXECUTION_ERROR",
                error_message=str(e),
                error_title="Error en la ejecución",
                error_severity="HIGH",
                error_category="SYSTEM"
            )

        finally:
            # Cerrar cursor y conexión
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                logger.debug("Conexión a Azure SQL cerrada")

    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión a Azure SQL Database.

        Returns:
            Dict con el resultado de la prueba
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Ejecutar query simple de prueba
            cursor.execute("SELECT @@VERSION as version, DB_NAME() as database_name")
            row = cursor.fetchone()

            result = {
                "success": True,
                "message": "Conexión exitosa a Azure SQL Database",
                "database": row.database_name if row else None,
                "timestamp": datetime.utcnow().isoformat()
            }

            cursor.close()
            conn.close()

            return result

        except Exception as e:
            logger.error(f"Error al probar conexión: {str(e)}")
            return {
                "success": False,
                "message": f"Error al conectar: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
