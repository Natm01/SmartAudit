"""
Script para consultar los registros de audit_test_exec guardados en la base de datos
"""
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.connection import get_db_connection
from datetime import datetime


def query_audit_test_exec(limit=10):
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

            # Query para obtener los últimos registros
            query = f"""
                SELECT TOP {limit}
                    id,
                    tenant_id,
                    workspace_id,
                    project_id,
                    external_gid,
                    period_beginning_date,
                    period_ending_date,
                    fiscal_year,
                    storage_relative_path,
                    je_file_type_code,
                    je_file_data_structure_type_code,
                    je_original_file_name,
                    je_file_name,
                    je_file_extension,
                    je_file_size_bytes,
                    tb_file_type_code,
                    tb_file_data_structure_type_code,
                    tb_original_file_name,
                    tb_file_name,
                    tb_file_extension,
                    tb_file_size_bytes,
                    created_at,
                    created_by_user_id
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
                print(f"   - Tenant ID: {row.tenant_id}")
                print(f"   - Workspace ID: {row.workspace_id}")
                print(f"   - Project ID: {row.project_id}")
                print(f"   - External GID: {row.external_gid or 'NULL'}")
                print()

                print(f"📅 PERÍODO:")
                print(f"   - Fecha inicio: {row.period_beginning_date}")
                print(f"   - Fecha fin: {row.period_ending_date}")
                print(f"   - Año fiscal: {row.fiscal_year}")
                print()

                print(f"💾 STORAGE:")
                print(f"   - Path relativo: {row.storage_relative_path}")
                print()

                print(f"📄 JOURNAL ENTRY (JE):")
                print(f"   - Tipo: {row.je_file_type_code}")
                print(f"   - Estructura: {row.je_file_data_structure_type_code}")
                print(f"   - Nombre original: {row.je_original_file_name}")
                print(f"   - Nombre sistema: {row.je_file_name}")
                print(f"   - Extensión: {row.je_file_extension}")
                print(f"   - Tamaño: {row.je_file_size_bytes:,} bytes ({row.je_file_size_bytes / 1024 / 1024:.2f} MB)")
                print()

                print(f"📊 TRIAL BALANCE (TB):")
                print(f"   - Tipo: {row.tb_file_type_code}")
                print(f"   - Estructura: {row.tb_file_data_structure_type_code}")
                print(f"   - Nombre original: {row.tb_original_file_name}")
                print(f"   - Nombre sistema: {row.tb_file_name}")
                print(f"   - Extensión: {row.tb_file_extension}")
                print(f"   - Tamaño: {row.tb_file_size_bytes:,} bytes ({row.tb_file_size_bytes / 1024 / 1024:.2f} MB)")
                print()

                print(f"👤 AUDITORÍA:")
                print(f"   - Creado el: {row.created_at}")
                print(f"   - Creado por (user_id): {row.created_by_user_id}")
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
                    tenant_id,
                    workspace_id,
                    project_id,
                    external_gid,
                    period_beginning_date,
                    period_ending_date,
                    fiscal_year,
                    storage_relative_path,
                    je_file_type_code,
                    je_file_data_structure_type_code,
                    je_original_file_name,
                    je_file_name,
                    je_file_extension,
                    je_file_size_bytes,
                    tb_file_type_code,
                    tb_file_data_structure_type_code,
                    tb_original_file_name,
                    tb_file_name,
                    tb_file_extension,
                    tb_file_size_bytes,
                    created_at,
                    created_by_user_id
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
            print(f"   - Tenant ID: {row.tenant_id}")
            print(f"   - Workspace ID: {row.workspace_id}")
            print(f"   - Project ID: {row.project_id}")
            print(f"   - External GID: {row.external_gid or 'NULL'}")
            print()

            print(f"📅 PERÍODO:")
            print(f"   - Fecha inicio: {row.period_beginning_date}")
            print(f"   - Fecha fin: {row.period_ending_date}")
            print(f"   - Año fiscal: {row.fiscal_year}")
            print()

            print(f"💾 STORAGE:")
            print(f"   - Path relativo: {row.storage_relative_path}")
            print()

            print(f"📄 JOURNAL ENTRY (JE):")
            print(f"   - Tipo: {row.je_file_type_code}")
            print(f"   - Estructura: {row.je_file_data_structure_type_code}")
            print(f"   - Nombre original: {row.je_original_file_name}")
            print(f"   - Nombre sistema: {row.je_file_name}")
            print(f"   - Extensión: {row.je_file_extension}")
            print(f"   - Tamaño: {row.je_file_size_bytes:,} bytes ({row.je_file_size_bytes / 1024 / 1024:.2f} MB)")
            print()

            print(f"📊 TRIAL BALANCE (TB):")
            print(f"   - Tipo: {row.tb_file_type_code}")
            print(f"   - Estructura: {row.tb_file_data_structure_type_code}")
            print(f"   - Nombre original: {row.tb_original_file_name}")
            print(f"   - Nombre sistema: {row.tb_file_name}")
            print(f"   - Extensión: {row.tb_file_extension}")
            print(f"   - Tamaño: {row.tb_file_size_bytes:,} bytes ({row.tb_file_size_bytes / 1024 / 1024:.2f} MB)")
            print()

            print(f"👤 AUDITORÍA:")
            print(f"   - Creado el: {row.created_at}")
            print(f"   - Creado por (user_id): {row.created_by_user_id}")
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
                    tenant_id,
                    workspace_id,
                    project_id,
                    period_beginning_date,
                    period_ending_date,
                    fiscal_year,
                    je_original_file_name,
                    tb_original_file_name,
                    created_at
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
                print(f"{i}. ID: {row.id} | Período: {row.period_beginning_date} - {row.period_ending_date} | Año: {row.fiscal_year}")
                print(f"   JE: {row.je_original_file_name}")
                print(f"   TB: {row.tb_original_file_name}")
                print(f"   Creado: {row.created_at}")
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
