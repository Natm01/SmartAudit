"""
Script para consultar los registros de audit_test_exec guardados en la base de datos
"""
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_db_connection
from datetime import datetime


def query_audit_test_exec(limit=100):
    """
    Consultar los últimos registros de audit_test_exec

    Args:
        limit: Número de registros a mostrar (default: 10)
    """
    print("=" * 100)
    print("CONSULTANDO REGISTROS DE workspace.audit_test_exec")
    print("=" * 100)
    print()

    try:
        with get_db_connection() as conn:
            conn.autocommit = True
            cursor = conn.cursor()

            # Query para obtener los últimos registros (solo columnas que existen)
            query = f"""
                SELECT TOP {limit}
                    id,
                    external_gid,
                    tenant_id,
                    workspace_id,
                    project_id,
                    audit_test_id,
                    name,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by
                FROM workspace.audit_test_exec
                ORDER BY id DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                print("❌ No se encontraron registros en la tabla.")
                return

            print(f"✅ Se encontraron {len(rows)} registro(s)\n")

            for i, row in enumerate(rows, 1):
                print(f"{'=' * 100}")
                print(f"REGISTRO #{i} - ID: {row.id}")
                print(f"{'=' * 100}")
                print(f"📋 INFORMACIÓN GENERAL:")
                print(f"   - ID: {row.id}")
                print(f"   - External GID: {row.external_gid}")
                print(f"   - Tenant ID: {row.tenant_id}")
                print(f"   - Workspace ID: {row.workspace_id}")
                print(f"   - Project ID: {row.project_id}")
                print(f"   - Audit Test ID: {row.audit_test_id}")
                print(f"   - Name: {row.name}")
                print()

                print(f"👤 AUDITORÍA:")
                print(f"   - Creado el: {row.created_at}")
                print(f"   - Creado por (user_id): {row.created_by}")
                print(f"   - Actualizado el: {row.updated_at}")
                print(f"   - Actualizado por (user_id): {row.updated_by}")
                print()

            print("=" * 100)

    except Exception as e:
        print(f"❌ Error al consultar la base de datos:")
        print(f"   {str(e)}")
        print()


def query_by_id(audit_test_id):
    """
    Consultar un registro específico por ID

    Args:
        audit_test_id: ID del registro a consultar
    """
    print("=" * 100)
    print(f"CONSULTANDO REGISTRO ID: {audit_test_id}")
    print("=" * 100)
    print()

    try:
        with get_db_connection() as conn:
            conn.autocommit = True
            cursor = conn.cursor()

            query = """
                SELECT
                    id,
                    external_gid,
                    tenant_id,
                    workspace_id,
                    project_id,
                    audit_test_id,
                    name,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by
                FROM workspace.audit_test_exec
                WHERE id = ?
            """

            cursor.execute(query, (audit_test_id,))
            row = cursor.fetchone()

            if not row:
                print(f"❌ No se encontró ningún registro con ID {audit_test_id}")
                return

            print(f"✅ Registro encontrado\n")

            print(f"📋 INFORMACIÓN GENERAL:")
            print(f"   - ID: {row.id}")
            print(f"   - External GID: {row.external_gid}")
            print(f"   - Tenant ID: {row.tenant_id}")
            print(f"   - Workspace ID: {row.workspace_id}")
            print(f"   - Project ID: {row.project_id}")
            print(f"   - Audit Test ID: {row.audit_test_id}")
            print(f"   - Name: {row.name}")
            print()

            print(f"👤 AUDITORÍA:")
            print(f"   - Creado el: {row.created_at}")
            print(f"   - Creado por (user_id): {row.created_by}")
            print(f"   - Actualizado el: {row.updated_at}")
            print(f"   - Actualizado por (user_id): {row.updated_by}")
            print()

            print("=" * 100)

    except Exception as e:
        print(f"❌ Error al consultar la base de datos:")
        print(f"   {str(e)}")
        print()


def query_by_project(project_id, limit=5):
    """
    Consultar registros por project_id

    Args:
        project_id: ID del proyecto
        limit: Número de registros a mostrar
    """
    print("=" * 100)
    print(f"CONSULTANDO REGISTROS DEL PROYECTO: {project_id}")
    print("=" * 100)
    print()

    try:
        with get_db_connection() as conn:
            conn.autocommit = True
            cursor = conn.cursor()

            query = f"""
                SELECT TOP {limit}
                    id,
                    external_gid,
                    tenant_id,
                    workspace_id,
                    project_id,
                    audit_test_id,
                    name,
                    created_at,
                    created_by
                FROM workspace.audit_test_exec
                WHERE project_id = ?
                ORDER BY id DESC
            """

            cursor.execute(query, (project_id,))
            rows = cursor.fetchall()

            if not rows:
                print(f"❌ No se encontraron registros para el proyecto {project_id}")
                return

            print(f"✅ Se encontraron {len(rows)} registro(s)\n")

            for i, row in enumerate(rows, 1):
                print(f"{i}. ID: {row.id} | Audit Test ID: {row.audit_test_id} | Name: {row.name}")
                print(f"   External GID: {row.external_gid}")
                print(f"   Creado: {row.created_at} por user_id: {row.created_by}")
                print()

    except Exception as e:
        print(f"❌ Error al consultar la base de datos:")
        print(f"   {str(e)}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Consultar registros de audit_test_exec')
    parser.add_argument('--limit', type=int, default=10, help='Número de registros a mostrar (default: 10)')
    parser.add_argument('--id', type=int, help='Consultar un registro específico por ID')
    parser.add_argument('--project', type=int, help='Consultar registros de un proyecto específico')

    args = parser.parse_args()

    if args.id:
        query_by_id(args.id)
    elif args.project:
        query_by_project(args.project, args.limit)
    else:
        query_audit_test_exec(args.limit)
