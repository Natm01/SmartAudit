"""
Router para endpoints de base de datos
"""
from fastapi import APIRouter, HTTPException
from db.connection import get_db_connection, SERVER, DATABASE

router = APIRouter(
    prefix="/smau-proto/api/database",
    tags=["database"]
)


@router.get("/test-connection")
def test_connection():
    """
    Prueba la conexión a la base de datos y devuelve la versión de SQL Server
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION as version")
            result = cursor.fetchone()

            return {
                "status": "Conectado exitosamente",
                "sql_version": result.version,
                "server": SERVER,
                "database": DATABASE
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error conectando a la BD: {str(e)}"
        )
