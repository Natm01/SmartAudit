"""
Script para ver la estructura de la tabla audit_test_exec
"""
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_db_connection


def describe_table():
    """Ver la estructura de la tabla workspace.audit_test_exec"""
    print("=" * 100)
    print("ESTRUCTURA DE LA TABLA workspace.audit_test_exec")
    print("=" * 100)
    print()

    try:
        with get_db_connection() as conn:
            conn.autocommit = True
            cursor = conn.cursor()

            # Query para obtener las columnas de la tabla
            query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'workspace'
                  AND TABLE_NAME = 'audit_test_exec'
                ORDER BY ORDINAL_POSITION
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                print("❌ No se encontró la tabla workspace.audit_test_exec")
                return

            print(f"✅ La tabla tiene {len(rows)} columna(s)\n")
            print(f"{'#':<4} {'COLUMNA':<40} {'TIPO':<20} {'LARGO':<10} {'NULL':<8} {'DEFAULT':<20}")
            print("-" * 100)

            for i, row in enumerate(rows, 1):
                column_name = row.COLUMN_NAME
                data_type = row.DATA_TYPE
                max_length = row.CHARACTER_MAXIMUM_LENGTH if row.CHARACTER_MAXIMUM_LENGTH else '-'
                is_nullable = 'YES' if row.IS_NULLABLE == 'YES' else 'NO'
                default_value = row.COLUMN_DEFAULT if row.COLUMN_DEFAULT else '-'

                print(f"{i:<4} {column_name:<40} {data_type:<20} {str(max_length):<10} {is_nullable:<8} {str(default_value):<20}")

            print()
            print("=" * 100)

    except Exception as e:
        print(f"❌ Error al consultar la base de datos:")
        print(f"   {str(e)}")
        print()


if __name__ == "__main__":
    describe_table()
