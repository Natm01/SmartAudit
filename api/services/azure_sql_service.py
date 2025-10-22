"""
Servicio para conexión y ejecución de stored procedures en Azure SQL Database

Soporta dos métodos de autenticación:
1. Managed Identity (recomendado para Azure Container Apps/VM)
2. SQL Authentication (usuario/contraseña como fallback)
"""
import pyodbc
import os
import logging
import struct
from typing import Optional, Dict, Any
from datetime import datetime
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
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
        Inicializa el servicio con configuración desde variables de entorno.

        Métodos de autenticación soportados:

        1. MANAGED IDENTITY (recomendado para Azure):
           - AZURE_SQL_AUTH_METHOD=managed_identity
           - AZURE_SQL_SERVER: Servidor SQL
           - AZURE_SQL_DATABASE: Nombre de la base de datos
           - AZURE_MANAGED_IDENTITY_CLIENT_ID (opcional): Client ID de la Managed Identity

        2. SQL AUTHENTICATION (fallback para desarrollo local):
           - AZURE_SQL_AUTH_METHOD=sql_auth o no configurado
           - AZURE_SQL_SERVER: Servidor SQL
           - AZURE_SQL_DATABASE: Nombre de la base de datos
           - AZURE_SQL_USERNAME: Usuario
           - AZURE_SQL_PASSWORD: Contraseña
        """
        self.server = os.getenv('AZURE_SQL_SERVER')
        self.database = os.getenv('AZURE_SQL_DATABASE')
        self.driver = os.getenv('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')

        # Método de autenticación
        self.auth_method = os.getenv('AZURE_SQL_AUTH_METHOD', 'sql_auth').lower()

        # Validar configuración básica
        if not self.server or not self.database:
            raise ValueError("AZURE_SQL_SERVER y AZURE_SQL_DATABASE son requeridos")

        # Configurar según método de autenticación
        if self.auth_method == 'managed_identity':
            logger.info("Usando Managed Identity para autenticación con Azure SQL")
            self.managed_identity_client_id = os.getenv('AZURE_MANAGED_IDENTITY_CLIENT_ID')
            self.credential = None  # Se inicializará al conectar
        else:
            logger.info("Usando SQL Authentication para autenticación con Azure SQL")
            self.username = os.getenv('AZURE_SQL_USERNAME')
            self.password = os.getenv('AZURE_SQL_PASSWORD')

            if not self.username or not self.password:
                raise ValueError(
                    "Para SQL Authentication se requieren: "
                    "AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD"
                )

        logger.info(f"Azure SQL configurado: {self.server}/{self.database}")

    def _get_access_token_for_sql(self) -> bytes:
        """
        Obtiene el access token para Azure SQL usando Managed Identity.

        Returns:
            bytes: Token de acceso en formato compatible con pyodbc

        Raises:
            Exception: Si no se puede obtener el token
        """
        try:
            # Crear credential según configuración
            if self.managed_identity_client_id:
                logger.debug(f"Usando Managed Identity con Client ID: {self.managed_identity_client_id}")
                credential = ManagedIdentityCredential(client_id=self.managed_identity_client_id)
            else:
                logger.debug("Usando DefaultAzureCredential (incluye Managed Identity)")
                credential = DefaultAzureCredential()

            # Scope para Azure SQL Database
            # https://database.windows.net/.default es el scope estándar para Azure SQL
            token = credential.get_token("https://database.windows.net/.default")

            # pyodbc requiere el token en un formato específico
            token_bytes = token.token.encode("utf-16-le")
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

            logger.debug("Access token obtenido exitosamente")
            return token_struct

        except Exception as e:
            logger.error(f"Error al obtener access token: {str(e)}")
            raise Exception(f"No se pudo obtener access token de Managed Identity: {str(e)}")

    def get_connection(self) -> pyodbc.Connection:
        """
        Crear y retornar una conexión a Azure SQL Database.

        Soporta dos métodos:
        1. Managed Identity: Usa Azure AD para autenticación (más seguro)
        2. SQL Authentication: Usa usuario/contraseña (fallback)

        Returns:
            pyodbc.Connection: Conexión activa a la base de datos

        Raises:
            Exception: Si no se puede establecer la conexión
        """
        try:
            if self.auth_method == 'managed_identity':
                # MÉTODO 1: Managed Identity (recomendado para Azure)
                logger.debug("Conectando con Managed Identity...")

                # Obtener access token
                token_struct = self._get_access_token_for_sql()

                # Construir connection string sin usuario/contraseña
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    "Encrypt=yes;TrustServerCertificate=no;"
                    "Connection Timeout=30;"
                )

                # Conectar usando el token
                # SQL_COPT_SS_ACCESS_TOKEN = 1256 es el atributo para el token
                conn = pyodbc.connect(
                    connection_string,
                    attrs_before={1256: token_struct}
                )

                logger.debug("Conexión con Managed Identity establecida exitosamente")

            else:
                # MÉTODO 2: SQL Authentication (usuario/contraseña)
                logger.debug("Conectando con SQL Authentication...")

                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                    "Encrypt=yes;TrustServerCertificate=no;"
                    "Connection Timeout=30;"
                )

                conn = pyodbc.connect(connection_string)
                logger.debug("Conexión con SQL Authentication establecida exitosamente")

            return conn

        except pyodbc.Error as e:
            logger.error(f"Error de pyodbc al conectar con Azure SQL: {str(e)}")
            raise Exception(f"No se pudo conectar a Azure SQL Database: {str(e)}")
        except Exception as e:
            logger.error(f"Error general al conectar con Azure SQL: {str(e)}")
            raise Exception(f"Error al establecer conexión: {str(e)}")

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
