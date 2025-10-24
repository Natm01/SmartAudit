"""
Módulo para gestionar la conexión a Azure SQL Database
"""
import pyodbc
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("DB_SERVER", "tu-servidor.database.windows.net")
DATABASE = os.getenv("DB_NAME", "tu-base-datos")


def get_connection_string():
    """
    Genera la cadena de conexión según el ambiente
    - Azure: usa Authentication=ActiveDirectoryMsi
    - Local: usa Authentication=ActiveDirectoryInteractive
    """
    base = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};"

    # Si estamos en Azure
    if os.environ.get('WEBSITE_INSTANCE_ID'):
        return base + "Authentication=ActiveDirectoryMsi;"
    # Si estamos en local
    else:
        return base + "Authentication=ActiveDirectoryInteractive;"


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
