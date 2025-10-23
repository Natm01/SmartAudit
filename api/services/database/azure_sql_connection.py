import pyodbc
import struct
import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, AzureCliCredential
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    """Modos de conexión soportados."""
    MANAGED_IDENTITY = "managed_identity"
    AZURE_CLI = "azure_cli"
    CONNECTION_STRING = "connection_string"


class AzureSqlConnection:
    """
    Gestor de conexiones a Azure SQL que funciona tanto en local como en Azure.

    Modos de operación:
    1. Local (desarrollo): Usa Azure CLI credential
    2. Azure (producción): Usa Managed Identity
    3. Fallback: Connection string tradicional (solo para casos especiales)
    """

    def __init__(
        self,
        server: str,
        database: str,
        driver: str = "ODBC Driver 18 for SQL Server",
        connection_string: Optional[str] = None,
        force_mode: Optional[ConnectionMode] = None
    ):
        """
        Args:
            server: Nombre del servidor (ej: 'myserver.database.windows.net')
            database: Nombre de la base de datos
            driver: Driver ODBC a usar
            connection_string: Connection string completo (opcional, para casos legacy)
            force_mode: Forzar un modo específico de conexión
        """
        self.server = server
        self.database = database
        self.driver = driver
        self.connection_string = connection_string
        self.force_mode = force_mode
        self._connection: Optional[pyodbc.Connection] = None
        self._detected_mode: Optional[ConnectionMode] = None

    def _is_running_in_azure(self) -> bool:
        """
        Detecta si estamos ejecutando en Azure.
        """
        # Container Apps y Functions tienen estas variables
        return any([
            os.getenv("AZURE_CLIENT_ID"),  # Managed Identity
            os.getenv("MSI_ENDPOINT"),     # Managed Identity
            os.getenv("IDENTITY_ENDPOINT"), # Managed Identity
            os.getenv("WEBSITE_INSTANCE_ID"), # App Service/Functions
            os.getenv("CONTAINER_APP_NAME")  # Container Apps
        ])

    def _detect_connection_mode(self) -> ConnectionMode:
        """
        Detecta automáticamente el modo de conexión apropiado.
        """
        if self.force_mode:
            logger.info(f"Usando modo forzado: {self.force_mode.value}")
            return self.force_mode

        if self.connection_string:
            logger.info("Usando connection string proporcionado")
            return ConnectionMode.CONNECTION_STRING

        if self._is_running_in_azure():
            logger.info("Entorno Azure detectado - usando Managed Identity")
            return ConnectionMode.MANAGED_IDENTITY

        logger.info("Entorno local detectado - usando Azure CLI")
        return ConnectionMode.AZURE_CLI

    def _get_access_token(self) -> bytes:
        """
        Obtiene token usando DefaultAzureCredential (método universal).
        Este es el método recomendado que funciona en todos los escenarios.
        """
        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default")

            token_bytes = token.token.encode("utf-16-le")
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

            logger.info("Token obtenido vía DefaultAzureCredential")
            return token_struct

        except Exception as e:
            logger.error(f"Error obteniendo token: {e}")
            logger.error(
                "En local: ejecuta 'az login'\n"
                "En Azure: verifica que la Managed Identity esté configurada"
            )
            raise

    def get_connection(self) -> pyodbc.Connection:
        """
        Retorna una conexión activa a la base de datos.
        """
        if self._connection is None or self._connection.closed:
            self._connection = self._create_connection()

        return self._connection

    def _create_connection(self) -> pyodbc.Connection:
        """
        Crea una nueva conexión según el modo detectado.
        """
        mode = self._detect_connection_mode()
        self._detected_mode = mode

        try:
            if mode == ConnectionMode.CONNECTION_STRING:
                return self._connect_with_connection_string()
            else:
                return self._connect_with_token()

        except Exception as e:
            logger.error(f"Error creando conexión en modo {mode.value}: {e}")
            raise

    def _connect_with_token(self) -> pyodbc.Connection:
        """
        Conecta usando token de Azure AD (funciona local y en Azure).
        """
        # Obtener token (funciona automáticamente en local y Azure)
        token_struct = self._get_access_token()

        # Construir connection string
        connection_string = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

        # Conectar usando el token
        # SQL_COPT_SS_ACCESS_TOKEN = 1256
        connection = pyodbc.connect(
            connection_string,
            attrs_before={1256: token_struct}
        )

        logger.info(f"Conexión exitosa a {self.database} en {self.server}")
        return connection

    def _connect_with_connection_string(self) -> pyodbc.Connection:
        """
        Conecta usando connection string tradicional (fallback).
        """
        if not self.connection_string:
            raise ValueError("Connection string no proporcionado")

        connection = pyodbc.connect(self.connection_string)
        logger.info("Conexión exitosa usando connection string")
        return connection

    def test_connection(self) -> bool:
        """
        Prueba la conexión y retorna True si es exitosa.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info(f"Test de conexión exitoso: {result}")
            return True
        except Exception as e:
            logger.error(f"Test de conexión falló: {e}")
            return False

    def get_connection_info(self) -> dict:
        """
        Retorna información sobre la conexión actual.
        """
        return {
            "server": self.server,
            "database": self.database,
            "mode": self._detected_mode.value if self._detected_mode else "not_connected",
            "is_azure": self._is_running_in_azure(),
            "connected": self._connection is not None and not self._connection.closed
        }

    def close(self):
        """
        Cierra la conexión si está abierta.
        """
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Conexión cerrada")

    def __enter__(self):
        """Context manager: entrada."""
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: salida."""
        self.close()
