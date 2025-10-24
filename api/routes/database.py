"""
Router para endpoints de base de datos
"""
from fastapi import APIRouter, HTTPException
from db.connection import get_db_connection, SERVER, DATABASE, get_diagnostic_info
import traceback

router = APIRouter(
    prefix="/smau-proto/api/database",
    tags=["database"]
)


@router.get("/test-connection")
def test_connection():
    """
    Prueba la conexión a la base de datos y devuelve la versión de SQL Server
    """
    diagnostic_info = get_diagnostic_info()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION as version")
            result = cursor.fetchone()

            return {
                "status": "Conectado exitosamente",
                "sql_version": result.version,
                "server": SERVER,
                "database": DATABASE,
                "diagnostics": diagnostic_info
            }
    except Exception as e:
        # Capturar más información del error
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "diagnostics": diagnostic_info
        }

        raise HTTPException(
            status_code=500,
            detail=error_details
        )
