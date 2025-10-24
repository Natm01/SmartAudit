"""
Módulo de conexión a base de datos
"""
from .connection import get_connection_string, get_db_connection

__all__ = ["get_connection_string", "get_db_connection"]
