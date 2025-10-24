"""
Módulo para gestionar la conexión a Azure SQL Database
"""
import pyodbc
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DATABASE")


def is_azure_environment():
    """Detecta si estamos ejecutando en Azure"""
    return bool(os.environ.get('WEBSITE_INSTANCE_ID'))


def get_connection_string():
    """
    Genera la cadena de conexión según el ambiente
    - Azure: usa Authentication=ActiveDirectoryMsi
    - Local: usa Authentication=ActiveDirectoryInteractive
    """
    base = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};"

    # Si estamos en Azure
    if is_azure_environment():
        return base + "Authentication=ActiveDirectoryMsi;"
    # Si estamos en local
    else:
        return base + "Authentication=ActiveDirectoryInteractive;"


def get_diagnostic_info():
    """Obtiene información de diagnóstico del ambiente"""
    try:
        drivers = pyodbc.drivers()
    except:
        drivers = ["Error obteniendo drivers"]

    return {
        "environment": "Azure" if is_azure_environment() else "Local",
        "server": SERVER,
        "database": DATABASE,
        "auth_type": "ActiveDirectoryMsi" if is_azure_environment() else "ActiveDirectoryInteractive",
        "odbc_drivers": drivers,
        "env_vars": {
            "DB_SERVER": os.getenv("DB_SERVER", "NOT_SET"),
            "DB_NAME": os.getenv("DB_NAME", "NOT_SET"),
            "WEBSITE_INSTANCE_ID": os.getenv("WEBSITE_INSTANCE_ID", "NOT_SET"),
            "CONTAINER_APP_NAME": os.getenv("CONTAINER_APP_NAME", "NOT_SET")
        }
    }


@contextmanager
def get_db_connection():
    """
    Context manager para manejar la conexión a la base de datos

    Uso:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            result = cursor.fetchone()
    """
    conn = None
    try:
        conn = pyodbc.connect(get_connection_string())
        yield conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()
