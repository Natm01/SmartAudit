import pyodbc
import pandas as pd
from datetime import datetime
from typing import Tuple, List, Dict, Optional, Any
import sys
import os
import time
from db.connection import get_connection_string


class AccountingDataLoader:
    """
    Loader para el nuevo paradigma:
      • STAGING (según DDL; con FKs y entry_type en journal_entries y business_category en lines)
      • ADS:
          - Mantiene entry_type en ads.journal_entries
          - Copia business_category ORIGINAL desde staging a ads.journal_entry_lines
      • ANALYTICS:
          - analytics.account_combination: bitmask + account_combination (por asiento)
          - analytics.entry_type: business_category por apunte **SIEMPRE calculado**, FK a ADS
    """

    def __init__(
        self,
        workspace_id: int,
        project_id: int,
        entity_id: int,
        fiscal_year: int,
        period_ending_date: str,
        dataset_version_id: int = 201
    ):
        # Parámetros fijos
        self.tenant_id = 101
        self.dataset_id = 101
        self.platform_user_id = 1

        # Parámetros desde execution
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.entity_id = entity_id
        self.fiscal_year = fiscal_year
        self.period_ending_date = period_ending_date
        self.dataset_version_id = dataset_version_id

        # Usa mapping de reporting_account para bitmask/combination
        self.uses_mapping_default = False

        # FK de analytics.entry_type → ADS.journal_entry_lines
        self.analytics_entry_type_fk_refs_ads = True

    # ----------------------------------------------------------------------
    # Infraestructura PGC (se requiere que ya exista y esté poblada)
    # ----------------------------------------------------------------------
    def ensure_pgc_estructura_exists(self, conn):
        """Ensure PGC structure table exists with Spanish accounting plan data"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'pgc_estructura' AND TABLE_SCHEMA = 'dbo'
            """)
            table_exists = cursor.fetchone()[0] > 0
            if not table_exists:
                cursor.execute("""
                    CREATE TABLE dbo.pgc_estructura (
                        id INT PRIMARY KEY,
                        cuenta_inicio VARCHAR(11) NOT NULL,
                        cuenta_fin VARCHAR(11) NOT NULL,
                        estado VARCHAR(20),
                        seccion VARCHAR(20),
                        epigrafe VARCHAR(10),
                        subepigrafe VARCHAR(10),
                        descripcion VARCHAR(255) NOT NULL,
                        naturaleza VARCHAR(50) NOT NULL,
                        criterio VARCHAR(50) NOT NULL,
                        es_compensadora BIT NOT NULL DEFAULT 0,
                        signo_negativo_pn BIT NOT NULL DEFAULT 0
                    )
                """)
                # Create performance indexes
                cursor.execute("CREATE INDEX idx_cuenta_inicio ON dbo.pgc_estructura(cuenta_inicio)")
                cursor.execute("CREATE INDEX idx_cuenta_fin ON dbo.pgc_estructura(cuenta_fin)")
                cursor.execute("CREATE INDEX idx_estado ON dbo.pgc_estructura(estado)")
                cursor.execute("CREATE INDEX idx_epigrafe ON dbo.pgc_estructura(epigrafe)")
                cursor.execute("CREATE INDEX idx_subepigrafe ON dbo.pgc_estructura(subepigrafe)")
                # Insert Spanish accounting plan data
                pgc_data = [
                    (1, '10000000000', '10999999999', 'Balance', 'PN', 'FP', 'I', 'Capital', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (2, '11000000000', '11999999999', 'Balance', 'PN', 'FP', 'II', 'Reservas y otros instrumentos de patrimonio', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (3, '12000000000', '12899999999', 'Balance', 'PN', 'FP', 'V', 'Resultados pendientes de aplicación', 'Variable', 'Por saldo', 0, 0),
                    (4, '12900000000', '12999999999', 'Balance', 'PN', 'FP', 'VII', 'Resultado del ejercicio', 'Variable', 'Por saldo', 0, 0),
                    (5, '13000000000', '13099999999', 'Balance', 'PN', 'Sub', 'I', 'Subvenciones oficiales de capital', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (6, '13100000000', '13199999999', 'Balance', 'PN', 'Sub', 'II', 'Donaciones y legados de capital', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (7, '13200000000', '13299999999', 'Balance', 'PN', 'Sub', 'III', 'Otras subvenciones donaciones y legados', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (8, '13300000000', '13399999999', 'Balance', 'PN', 'ACV', 'I', 'Ajustes por valoración en activos financieros a valor razonable con cambios en el patrimonio neto', 'Variable', 'Por saldo', 0, 0),
                    (9, '13400000000', '13499999999', 'Balance', 'PN', 'ACV', 'II', 'Operaciones de cobertura', 'Variable', 'Por saldo', 0, 0),
                    (10, '13500000000', '13599999999', 'Balance', 'PN', 'ACV', 'III', 'Diferencias de conversión', 'Variable', 'Por saldo', 0, 0),
                    (11, '13600000000', '13699999999', 'Balance', 'PN', 'ACV', 'IV', 'Ajustes por valoración en activos no corrientes y grupos enajenables mantenidos para la venta', 'Variable', 'Por saldo', 0, 0),
                    (12, '13700000000', '13799999999', 'Balance', 'PN', 'ACV', 'V', 'Ingresos fiscales a distribuir en varios ejercicios', 'Acreedor', 'Siempre patrimonio', 0, 0),
                    (13, '14000000000', '14999999999', 'Balance', 'Pasivo NC', 'I', '-', 'Provisiones', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (14, '15000000000', '15999999999', 'Balance', 'Pasivo NC', 'II', '-', 'Deudas a largo plazo con características especiales', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (15, '16000000000', '16999999999', 'Balance', 'Pasivo NC', 'III', '-', 'Deudas a largo plazo con partes vinculadas', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (16, '17000000000', '17999999999', 'Balance', 'Pasivo NC', 'IV', '-', 'Deudas a largo plazo por préstamos recibidos empréstitos y otros conceptos', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (17, '18000000000', '18999999999', 'Balance', 'Pasivo NC', 'V', '-', 'Pasivos por fianzas garantías y otros conceptos a largo plazo', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (18, '19000000000', '19999999999', 'Balance', 'Pasivo NC', 'VI', '-', 'Situaciones transitorias de financiación', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (19, '20000000000', '20999999999', 'Balance', 'Activo NC', 'I', '-', 'Inmovilizaciones intangibles', 'Deudor', 'Siempre activo', 0, 0),
                    (20, '21000000000', '21999999999', 'Balance', 'Activo NC', 'II', '-', 'Inmovilizaciones materiales', 'Deudor', 'Siempre activo', 0, 0),
                    (21, '22000000000', '22999999999', 'Balance', 'Activo NC', 'III', '-', 'Inversiones inmobiliarias', 'Deudor', 'Siempre activo', 0, 0),
                    (22, '23000000000', '23999999999', 'Balance', 'Activo NC', 'IV', '-', 'Inmovilizaciones materiales en curso', 'Deudor', 'Siempre activo', 0, 0),
                    (23, '24000000000', '24999999999', 'Balance', 'Activo NC', 'V', '-', 'Inversiones financieras a largo plazo en partes vinculadas', 'Deudor', 'Siempre activo', 0, 0),
                    (24, '25000000000', '25999999999', 'Balance', 'Activo NC', 'VI', '-', 'Otras inversiones financieras a largo plazo', 'Deudor', 'Siempre activo', 0, 0),
                    (25, '26000000000', '26999999999', 'Balance', 'Activo NC', 'VII', '-', 'Fianzas y depósitos constituidos a largo plazo', 'Deudor', 'Siempre activo', 0, 0),
                    (26, '27000000000', '27999999999', 'Balance', 'Activo NC', 'VIII', '-', 'Periodificaciones a largo plazo', 'Deudor', 'Siempre activo', 0, 0),
                    (27, '28000000000', '28999999999', '-', '-', '-', '-', 'Amortización acumulada del inmovilizado', 'Acreedor', 'Compensadora', 1, 0),
                    (28, '29000000000', '29999999999', '-', '-', '-', '-', 'Deterioro de valor de activos no corrientes', 'Acreedor', 'Compensadora', 1, 0),
                    (29, '30000000000', '30999999999', 'Balance', 'Activo C', 'II', '1', 'Comerciales', 'Deudor', 'Siempre activo', 0, 0),
                    (30, '31000000000', '31999999999', 'Balance', 'Activo C', 'II', '2', 'Materias primas', 'Deudor', 'Siempre activo', 0, 0),
                    (31, '32000000000', '32999999999', 'Balance', 'Activo C', 'II', '3', 'Otros aprovisionamientos', 'Deudor', 'Siempre activo', 0, 0),
                    (32, '33000000000', '33999999999', 'Balance', 'Activo C', 'II', '4', 'Productos en curso', 'Deudor', 'Siempre activo', 0, 0),
                    (33, '34000000000', '34999999999', 'Balance', 'Activo C', 'II', '5', 'Productos semiterminados', 'Deudor', 'Siempre activo', 0, 0),
                    (34, '35000000000', '35999999999', 'Balance', 'Activo C', 'II', '6', 'Productos terminados', 'Deudor', 'Siempre activo', 0, 0),
                    (35, '36000000000', '36999999999', 'Balance', 'Activo C', 'II', '7', 'Subproductos residuos y materiales recuperados', 'Deudor', 'Siempre activo', 0, 0),
                    (36, '37000000000', '37999999999', 'Balance', 'Activo C', 'II', '8', 'Anticipos a proveedores', 'Deudor', 'Siempre activo', 0, 0),
                    (37, '38000000000', '38999999999', 'Balance', 'Activo C', 'II', '9', 'Anticipos para inmovilizaciones', 'Deudor', 'Siempre activo', 0, 0),
                    (38, '39000000000', '39999999999', '-', '-', '-', '-', 'Deterioro de valor de las existencias', 'Acreedor', 'Compensadora', 1, 0),
                    (39, '40000000000', '40999999999', 'Balance', 'Pasivo C', 'V', '1', 'Proveedores', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (40, '41000000000', '41999999999', 'Balance', 'Pasivo C', 'V', '2', 'Acreedores varios', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (41, '42000000000', '42999999999', 'Balance', 'Pasivo C', 'V', '3', 'Acreedores específicos (subgrupo reservado)', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (42, '43000000000', '43999999999', 'Balance', 'Variable', 'III/V', '3/8', 'Clientes', 'Variable', 'Por saldo', 0, 0),
                    (43, '44000000000', '44999999999', 'Balance', 'Variable', 'III/V', '4/4', 'Deudores varios', 'Variable', 'Por saldo', 0, 0),
                    (44, '45000000000', '45999999999', 'Balance', 'Variable', 'III/V', '5/5', 'Deudores específicos (subgrupo reservado)', 'Variable', 'Por saldo', 0, 0),
                    (45, '46000000000', '46999999999', 'Balance', 'Variable', 'III/V', '6/6', 'Personal', 'Variable', 'Por saldo', 0, 0),
                    (46, '47000000000', '47999999999', 'Balance', 'Variable', 'III/V', '7/7', 'Administraciones Públicas', 'Variable', 'Por saldo', 0, 0),
                    (47, '48000000000', '48999999999', 'Balance', 'Variable', 'VI/VII', '-', 'Ajustes por periodificación', 'Variable', 'Por saldo', 0, 0),
                    (48, '49000000000', '49999999999', '-', '-', '-', '-', 'Deterioro de valor de créditos comerciales y provisiones a corto plazo', 'Acreedor', 'Compensadora', 1, 0),
                    (49, '50000000000', '50999999999', 'Balance', 'Pasivo C', 'III', '1', 'Empréstitos deudas con características especiales y otras emisiones análogas a corto plazo', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (50, '51000000000', '51999999999', 'Balance', 'Pasivo C', 'III', '2', 'Deudas a corto plazo con partes vinculadas', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (51, '52000000000', '52999999999', 'Balance', 'Pasivo C', 'III', '3', 'Deudas a corto plazo por préstamos recibidos y otros conceptos', 'Acreedor', 'Siempre pasivo', 0, 0),
                    (52, '53000000000', '53999999999', 'Balance', 'Activo C', 'IV', '1', 'Inversiones financieras a corto plazo en partes vinculadas', 'Deudor', 'Siempre activo', 0, 0),
                    (53, '54000000000', '54999999999', 'Balance', 'Variable', 'V/III', '2/4', 'Otras inversiones financieras a corto plazo', 'Variable', 'Por saldo', 0, 0),
                    (54, '55000000000', '55999999999', 'Balance', 'Variable', 'III/V', '7/5', 'Otras cuentas no bancarias', 'Variable', 'Por saldo', 0, 0),
                    (55, '56000000000', '56999999999', 'Balance', 'Variable', 'VII/VIII', '-', 'Fianzas y depósitos recibidos y constituidos a corto plazo y ajustes por periodificación', 'Variable', 'Por saldo', 0, 0),
                    (56, '57000000000', '57999999999', 'Balance', 'Activo C', 'VII', '1', 'Tesorería', 'Deudor', 'Siempre activo', 0, 0),
                    (57, '58000000000', '58999999999', 'Balance', 'Variable', 'I/I', '-', 'Activos no corrientes mantenidos para la venta y activos y pasivos asociados', 'Variable', 'Por saldo', 0, 0),
                    (58, '59000000000', '59999999999', '-', '-', '-', '-', 'Deterioro del valor de inversiones financieras a corto plazo y de activos no corrientes mantenidos para la venta', 'Acreedor', 'Compensadora', 1, 0),
                    (59, '60000000000', '60999999999', 'PyG', '-', '4', '-', 'Compras', 'Deudor', 'Siempre gasto', 0, 0),
                    (60, '61000000000', '61999999999', 'PyG', '-', '4', '-', 'Variación de existencias', 'Variable', 'Por saldo', 0, 0),
                    (61, '62000000000', '62999999999', 'PyG', '-', '7', 'a', 'Servicios exteriores', 'Deudor', 'Siempre gasto', 0, 0),
                    (62, '63000000000', '63999999999', 'PyG', '-', '7', 'b', 'Tributos', 'Variable', 'Por saldo', 0, 0),
                    (63, '64000000000', '64999999999', 'PyG', '-', '6', '-', 'Gastos de personal', 'Deudor', 'Siempre gasto', 0, 0),
                    (64, '65000000000', '65999999999', 'PyG', '-', '7', 'c', 'Otros gastos de gestión', 'Deudor', 'Siempre gasto', 0, 0),
                    (65, '66000000000', '66999999999', 'PyG', '-', '15', '-', 'Gastos financieros', 'Deudor', 'Siempre gasto', 0, 0),
                    (66, '67000000000', '67999999999', 'PyG', '-', '11', 'a', 'Pérdidas procedentes de activos no corrientes y gastos excepcionales', 'Deudor', 'Siempre gasto', 0, 0),
                    (67, '68000000000', '68999999999', 'PyG', '-', '8', '-', 'Dotaciones para amortizaciones', 'Deudor', 'Siempre gasto', 0, 0),
                    (68, '69000000000', '69999999999', 'PyG', '-', '11', 'a', 'Pérdidas por deterioro y otras dotaciones', 'Deudor', 'Siempre gasto', 0, 0),
                    (69, '70000000000', '70999999999', 'PyG', '-', '1', '-', 'Ventas de mercaderías de producción propia de servicios etc', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (70, '71000000000', '71999999999', 'PyG', '-', '2', '-', 'Variación de existencias', 'Variable', 'Por saldo', 0, 0),
                    (71, '72000000000', '72999999999', 'PyG', '-', '3', '-', 'Ingresos específicos de la actividad (subgrupo reservado)', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (72, '73000000000', '73999999999', 'PyG', '-', '3', '-', 'Trabajos realizados para la empresa', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (73, '74000000000', '74999999999', 'PyG', '-', '5', '-', 'Subvenciones donaciones y legados', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (74, '75000000000', '75999999999', 'PyG', '-', '5', 'a', 'Otros ingresos de gestión', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (75, '76000000000', '76999999999', 'PyG', '-', '14', '-', 'Ingresos financieros', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (76, '77000000000', '77999999999', 'PyG', '-', '11', 'b', 'Beneficios procedentes de activos no corrientes e ingresos excepcionales', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (77, '79000000000', '79999999999', 'PyG', '-', '10', '-', 'Excesos y aplicaciones de provisiones y de pérdidas por deterioro', 'Acreedor', 'Siempre ingreso', 0, 0),
                    (78, '80000000000', '89999999999', 'PN', 'PN', 'VIII', '-', 'Gastos imputados al patrimonio neto', 'Deudor', 'Siempre gasto', 0, 0),
                    (79, '90000000000', '99999999999', 'PN', 'PN', 'IX', '-', 'Ingresos imputados al patrimonio neto', 'Acreedor', 'Siempre ingreso', 0, 0)
                ]
                cursor.executemany("""
                    INSERT INTO dbo.pgc_estructura
                    (id, cuenta_inicio, cuenta_fin, estado, seccion, epigrafe, subepigrafe,
                     descripcion, naturaleza, criterio, es_compensadora, signo_negativo_pn)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, pgc_data)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error creating pgc_estructura: {str(e)}")

    # ----------------------------------------------------------------------
    # Carga STAGING desde CSV usando #raw_* y respetando FKs
    # ----------------------------------------------------------------------
    def bulk_insert_files(self, conn, je_blob_path: str, jel_blob_path: str, tb_blob_path: str):
        """
        Carga los CSVs desde Azure Blob Storage mediante SPs.
        - Usa los SPs staging.sp_load_*_csv_from_blob
        - Limpia staging de manera segura (por dataset_version_id)
        - Muestra resultados detallados de cada operación
        """
        cursor = conn.cursor()
        try:
            print("=" * 80)
            print("CLEANING STAGING...")
            print("=" * 80)

            # Limpieza por dataset_version_id (en lotes, para evitar bloqueos)
            tables = [
                "staging.journal_entry_lines",
                "staging.journal_entries",
                "staging.trial_balance",
                "staging.chart_of_accounts"
            ]
            
            for table in tables:
                total_deleted = 0
                while True:
                    cursor.execute(f"""
                        DELETE TOP (10000) FROM {table}
                        WHERE dataset_version_id = ?
                    """, (self.dataset_version_id,))
                    conn.commit()
                    deleted_rows = cursor.rowcount
                    total_deleted += deleted_rows
                    if deleted_rows == 0:
                        break
                
                if total_deleted > 0:
                    print(f"  ✓ {table}: {total_deleted:,} rows deleted")
                else:
                    print(f"  ○ {table}: No rows to delete")
            
            print("✓ Staging cleaned successfully\n")

            # === Journal Entries ===
            self._execute_and_log_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_journal_entries_csv_from_blob",
                file_type="JOURNAL ENTRIES",
                blob_path=je_blob_path
            )

            # === Journal Entry Lines ===
            self._execute_and_log_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_journal_entry_lines_csv_from_blob",
                file_type="JOURNAL ENTRY LINES",
                blob_path=jel_blob_path
            )

            # === Trial Balance ===
            self._execute_and_log_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_trial_balance_csv_from_blob",
                file_type="TRIAL BALANCE",
                blob_path=tb_blob_path
            )

            print("=" * 80)
            print("✓ ALL DATA LOADED SUCCESSFULLY INTO STAGING")
            print("=" * 80)

            # Regenerar Chart of Accounts
            print("Rebuilding Chart of Accounts...")

            # Asegurar estructura PGC (si no existe)
            self.ensure_pgc_estructura_exists(conn)

            # Crear/actualizar cuentas en chart_of_accounts
            cursor.execute(f"""
                WITH acc AS (
                    SELECT DISTINCT gl_account_number FROM staging.journal_entry_lines
                    WHERE dataset_version_id = {self.dataset_version_id}
                    UNION
                    SELECT DISTINCT gl_account_number FROM staging.trial_balance
                    WHERE dataset_version_id = {self.dataset_version_id}
                ),
                norm AS (
                    SELECT 
                        a.gl_account_number,
                        LEFT(RIGHT(REPLICATE('0',11) + REPLACE(a.gl_account_number, ' ', ''), 11), 11) AS padded
                    FROM acc a
                )
                INSERT INTO staging.chart_of_accounts (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number,
                    gl_account_name, account_type, account_description,
                    parent_account_number, account_level, account_hierarchy,
                    is_active, posting_account,
                    financial_statement_line_item, financial_statement_section, report_sequence,
                    normal_balance, account_category, account_subcategory,
                    account_creation_date, account_closure_date, effective_date,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    n.gl_account_number,
                    ISNULL(p.descripcion, CONCAT('Account ', n.gl_account_number)) AS gl_account_name,
                    CASE p.estado WHEN 'Balance' THEN 'Balance' WHEN 'PyG' THEN 'PyG' WHEN 'PN' THEN 'PN' ELSE 'Other' END AS account_type,
                    ISNULL(p.criterio, CONCAT('Account ', n.gl_account_number, ' (not in PGC)')) AS account_description,
                    NULL, 1, NULL,
                    1, 1,
                    NULL, p.seccion, NULL,
                    CASE p.naturaleza WHEN 'Deudor' THEN 'D' WHEN 'Acreedor' THEN 'C' ELSE 'V' END,
                    p.epigrafe, p.subepigrafe,
                    GETUTCDATE(), NULL, GETUTCDATE(),
                    NULL, NULL, NULL,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM norm n
                LEFT JOIN dbo.pgc_estructura p
                ON n.padded BETWEEN p.cuenta_inicio AND p.cuenta_fin;
            """)
            conn.commit()

            print("Chart of Accounts rebuilt successfully.")
            print("STAGING load complete via Stored Procedures.")

        except Exception as e:
            conn.rollback()
            print("\n" + "=" * 80)
            print("✗ ERROR LOADING STAGING")
            print("=" * 80)
            raise Exception(f"Error loading staging via SPs: {str(e)}")



    def _execute_and_log_sp(self, cursor, conn, sp_name: str, file_type: str, blob_path: str):
        """
        Ejecuta un SP de carga y muestra los resultados de forma legible.
        """
        print("=" * 80)
        print(f"LOADING {file_type}")
        print("=" * 80)
        print(f"Stored Procedure: {sp_name}")
        print(f"Blob Path: {blob_path}")
        print(f"Dataset Version ID: {self.dataset_version_id}")
        print("-" * 80)

        try:
            cursor.execute(f"""
                EXEC {sp_name}
                    @auth_user_id = ?, 
                    @dataset_version_id = ?, 
                    @blob_relative_path = ?
            """, (self.platform_user_id, self.dataset_version_id, blob_path))
            
            # Capturar el resultado del SP
            result = cursor.fetchone()
            
            if result:
                # Formatear el resultado de manera legible
                print("RESULT:")
                print(f"  Dataset Version ID    : {result.dataset_version_id}")
                print(f"  Blob Path             : {result.blob_relative_path}")
                print(f"  Rows Loaded           : {result.rows_loaded:,}")
                print(f"  Batch ID              : {result.batch_id}")
                print(f"  Temp Table            : {result.tmp_table_name}")
                print(f"  New State             : {result.dataset_version_state_code}")
                print("-" * 80)
                
                if result.rows_loaded > 0:
                    print(f"✓ {file_type}: {result.rows_loaded:,} rows loaded successfully")
                else:
                    print(f"⚠ {file_type}: No rows loaded (empty file?)")
            else:
                print("⚠ No result returned from SP")
            
            conn.commit()
            print(f"Stored Procedure: {sp_name}")

        except Exception as e:
            print(f"✗ Error loading {file_type}: {str(e)}")
            raise


    ''' 
    def bulk_insert_files(self, conn, je_blob_path: str, jel_blob_path: str, tb_blob_path: str):
        """
        Carga los CSVs desde Azure Blob Storage mediante SPs y actualiza el Chart of Accounts.
        - Usa los SPs staging.sp_load_*_csv_from_blob
        - Limpia staging de manera segura (por dataset_version_id)
        - Regenera el chart_of_accounts según las cuentas nuevas detectadas
        """
        cursor = conn.cursor()
        try:
            print("Cleaning STAGING...")

            # Limpieza por dataset_version_id (en lotes, para evitar bloqueos)
            tables = [
                "staging.journal_entry_lines",
                "staging.journal_entries",
                "staging.trial_balance",
                "staging.chart_of_accounts"
            ]
            for table in tables:
                while True:
                    cursor.execute(f"""
                        DELETE TOP (10000) FROM {table}
                        WHERE dataset_version_id = ?
                    """, (self.dataset_version_id,))
                    conn.commit()
                    if cursor.rowcount == 0:
                        break
            print("Staging cleaned")

            # Ejecutar SP: Journal Entries
            print("Loading journal_entries from blob...")
            cursor.execute("""
                EXEC staging.sp_load_journal_entries_csv_from_blob 
                    @auth_user_id = ?, 
                    @dataset_version_id = ?, 
                    @blob_relative_path = ?
            """, (self.platform_user_id, self.dataset_version_id, je_blob_path))
            conn.commit()

            # Ejecutar SP: Journal Entry Lines
            print("Loading journal_entry_lines from blob...")
            cursor.execute("""
                EXEC staging.sp_load_journal_entry_lines_csv_from_blob 
                    @auth_user_id = ?, 
                    @dataset_version_id = ?, 
                    @blob_relative_path = ?
            """, (self.platform_user_id, self.dataset_version_id, jel_blob_path))
            conn.commit()

            # Ejecutar SP: Trial Balance
            print("Loading trial_balance from blob...")
            cursor.execute("""
                EXEC staging.sp_load_trial_balance_csv_from_blob 
                    @auth_user_id = ?, 
                    @dataset_version_id = ?, 
                    @blob_relative_path = ?
            """, (self.platform_user_id, self.dataset_version_id, tb_blob_path))
            conn.commit()

            # Regenerar Chart of Accounts
            print("Rebuilding Chart of Accounts...")

            # Asegurar estructura PGC (si no existe)
            self.ensure_pgc_estructura_exists(conn)

            # Crear/actualizar cuentas en chart_of_accounts
            cursor.execute(f"""
                WITH acc AS (
                    SELECT DISTINCT gl_account_number FROM staging.journal_entry_lines
                    WHERE dataset_version_id = {self.dataset_version_id}
                    UNION
                    SELECT DISTINCT gl_account_number FROM staging.trial_balance
                    WHERE dataset_version_id = {self.dataset_version_id}
                ),
                norm AS (
                    SELECT 
                        a.gl_account_number,
                        LEFT(RIGHT(REPLICATE('0',11) + REPLACE(a.gl_account_number, ' ', ''), 11), 11) AS padded
                    FROM acc a
                )
                INSERT INTO staging.chart_of_accounts (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number,
                    gl_account_name, account_type, account_description,
                    parent_account_number, account_level, account_hierarchy,
                    is_active, posting_account,
                    financial_statement_line_item, financial_statement_section, report_sequence,
                    normal_balance, account_category, account_subcategory,
                    account_creation_date, account_closure_date, effective_date,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    n.gl_account_number,
                    ISNULL(p.descripcion, CONCAT('Account ', n.gl_account_number)) AS gl_account_name,
                    CASE p.estado WHEN 'Balance' THEN 'Balance' WHEN 'PyG' THEN 'PyG' WHEN 'PN' THEN 'PN' ELSE 'Other' END AS account_type,
                    ISNULL(p.criterio, CONCAT('Account ', n.gl_account_number, ' (not in PGC)')) AS account_description,
                    NULL, 1, NULL,
                    1, 1,
                    NULL, p.seccion, NULL,
                    CASE p.naturaleza WHEN 'Deudor' THEN 'D' WHEN 'Acreedor' THEN 'C' ELSE 'V' END,
                    p.epigrafe, p.subepigrafe,
                    GETUTCDATE(), NULL, GETUTCDATE(),
                    NULL, NULL, NULL,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM norm n
                LEFT JOIN dbo.pgc_estructura p
                ON n.padded BETWEEN p.cuenta_inicio AND p.cuenta_fin;
            """)
            conn.commit()

            print("Chart of Accounts rebuilt successfully.")
            print("STAGING load complete via Stored Procedures.")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error loading staging via SPs: {str(e)}")
    ''' 

    


    
    '''   
    def bulk_insert_files(self, conn, je_file: str, jel_file: str, tb_file: str):
        cursor = conn.cursor()
        try:
            print("Cleaning STAGING...")
            
            # Limpieza normal
            cursor.execute("DELETE FROM staging.journal_entry_lines WHERE dataset_version_id = ?", (self.dataset_version_id,))
            cursor.execute("DELETE FROM staging.journal_entries WHERE dataset_version_id = ?", (self.dataset_version_id,))
            cursor.execute("DELETE FROM staging.trial_balance WHERE dataset_version_id = ?", (self.dataset_version_id,))
            cursor.execute("DELETE FROM staging.chart_of_accounts WHERE dataset_version_id = ?", (self.dataset_version_id,))
            conn.commit()

            # Usar un sufijo único para las tablas temporales en staging
            temp_suffix = str(self.dataset_version_id).replace('-', '_')
            raw_je_table = f"staging.raw_journal_entries_{temp_suffix}"
            raw_jel_table = f"staging.raw_journal_entry_lines_{temp_suffix}"
            raw_tb_table = f"staging.raw_trial_balance_{temp_suffix}"

            # Eliminar tablas si ya existen (por si quedaron de ejecución anterior)
            for table in [raw_je_table, raw_jel_table, raw_tb_table]:
                cursor.execute(f"IF OBJECT_ID('{table}') IS NOT NULL DROP TABLE {table}")
            
            # Crear tablas regulares en staging
            cursor.execute(f"""
                CREATE TABLE {raw_je_table} (
                    journal_entry_id NVARCHAR(25) NOT NULL,
                    journal_id NVARCHAR(25) NULL,
                    entry_date DATE NULL,
                    entry_time TIME(0) NULL,
                    posting_date DATE NULL,
                    reversal_date DATE NULL,
                    effective_date DATE NULL,
                    description NVARCHAR(500) NULL,
                    reference_number NVARCHAR(50) NULL,
                    source NVARCHAR(100) NULL,
                    entry_type NVARCHAR(50) NULL,
                    recurring_entry BIT NULL,
                    manual_entry BIT NULL,
                    adjustment_entry BIT NULL,
                    prepared_by NVARCHAR(100) NULL,
                    approved_by NVARCHAR(100) NULL,
                    approval_date DATE NULL,
                    entry_status NVARCHAR(20) NULL,
                    total_debit_amount DECIMAL(28,2) NULL,
                    total_credit_amount DECIMAL(28,2) NULL,
                    line_count INT NULL,
                    fiscal_year INT NULL,
                    period_number INT NULL,
                    user_defined_01 NVARCHAR(50) NULL,
                    user_defined_02 NVARCHAR(50) NULL,
                    user_defined_03 NVARCHAR(50) NULL
                )
            """)

            cursor.execute(f"""
                CREATE TABLE {raw_jel_table} (
                    journal_entry_id NVARCHAR(25) NOT NULL,
                    line_number INT NOT NULL,
                    gl_account_number NVARCHAR(25) NOT NULL,
                    amount DECIMAL(28,2) NOT NULL,
                    debit_credit_indicator CHAR(1) NOT NULL,
                    business_unit NVARCHAR(50) NULL,
                    cost_center NVARCHAR(25) NULL,
                    department NVARCHAR(25) NULL,
                    project_code NVARCHAR(25) NULL,
                    location NVARCHAR(25) NULL,
                    line_description NVARCHAR(255) NULL,
                    reference_number NVARCHAR(50) NULL,
                    customer_id NVARCHAR(25) NULL,
                    vendor_id NVARCHAR(25) NULL,
                    product_id NVARCHAR(25) NULL,
                    user_defined_01 NVARCHAR(50) NULL,
                    user_defined_02 NVARCHAR(50) NULL,
                    user_defined_03 NVARCHAR(50) NULL,
                    reporting_account NVARCHAR(50) NULL,
                    business_category NVARCHAR(50) NULL
                )
            """)

            cursor.execute(f"""
                CREATE TABLE {raw_tb_table} (
                    gl_account_number NVARCHAR(25) NOT NULL,
                    reporting_account NVARCHAR(50) NULL,
                    fiscal_year INT NULL,
                    period_number INT NULL,
                    period_ending_balance DECIMAL(28,2) NOT NULL,
                    period_activity_debit DECIMAL(28,2) NULL,
                    period_activity_credit DECIMAL(28,2) NULL,
                    period_beginning_balance DECIMAL(28,2) NULL,
                    period_ending_date DATE NULL,
                    business_unit NVARCHAR(50) NULL,
                    cost_center NVARCHAR(25) NULL,
                    department NVARCHAR(25) NULL,
                    user_defined_01 NVARCHAR(50) NULL,
                    user_defined_02 NVARCHAR(50) NULL,
                    user_defined_03 NVARCHAR(50) NULL
                )
            """)

            print("BULK INSERT into staging raw tables ...")
            for table, file in [(raw_je_table, je_file),
                                (raw_jel_table, jel_file),
                                (raw_tb_table, tb_file)]:
                cursor.execute(f"""
                    BULK INSERT {table}
                    FROM '{file}'
                    WITH (
                        DATA_SOURCE = 'cloud_knowledge_dev',
                        FIELDTERMINATOR = ',',
                        ROWTERMINATOR = '0x0d0a',
                        FIRSTROW = 2,
                        DATAFILETYPE = 'char',
                        CODEPAGE = '65001',
                        KEEPNULLS,
                        TABLOCK
                    );
                """)

            conn.commit()

            # PGC requerido para nombres/atributos de cuentas
            self.ensure_pgc_estructura_exists(conn)

            # 1) COA primero (para FKs de lines/TB)
            print("Inserting STAGING.chart_of_accounts ...")
            cursor.execute(f"""
                WITH acc AS (
                    SELECT DISTINCT gl_account_number FROM {raw_jel_table}
                    UNION
                    SELECT DISTINCT gl_account_number FROM {raw_tb_table}
                ),
                norm AS (
                    SELECT 
                        a.gl_account_number,
                        LEFT(RIGHT(REPLICATE('0',11) + REPLACE(a.gl_account_number, ' ', ''), 11), 11) AS padded
                    FROM acc a
                )
                INSERT INTO staging.chart_of_accounts (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number,
                    gl_account_name, account_type, account_description,
                    parent_account_number, account_level, account_hierarchy,
                    is_active, posting_account,
                    financial_statement_line_item, financial_statement_section, report_sequence,
                    normal_balance, account_category, account_subcategory,
                    account_creation_date, account_closure_date, effective_date,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    ?, ?, ?, ?,
                    ?, ?,
                    n.gl_account_number,
                    ISNULL(p.descripcion, CONCAT('Account ', n.gl_account_number)) AS gl_account_name,
                    CASE p.estado WHEN 'Balance' THEN 'Balance' WHEN 'PyG' THEN 'PyG' WHEN 'PN' THEN 'PN' ELSE 'Other' END AS account_type,
                    ISNULL(p.criterio, CONCAT('Account ', n.gl_account_number, ' (not in PGC)')) AS account_description,
                    NULL, 1, NULL,
                    1, 1,
                    NULL, p.seccion, NULL,
                    CASE p.naturaleza WHEN 'Deudor' THEN 'D' WHEN 'Acreedor' THEN 'C' ELSE 'V' END,
                    p.epigrafe, p.subepigrafe,
                    GETUTCDATE(), NULL, GETUTCDATE(),
                    NULL, NULL, NULL,
                    ?, ?, NEWID()
                FROM norm n
                LEFT JOIN dbo.pgc_estructura p
                ON n.padded BETWEEN p.cuenta_inicio AND p.cuenta_fin;
            """, (self.tenant_id, self.workspace_id, self.project_id, self.entity_id,
                self.dataset_id, self.dataset_version_id,
                self.platform_user_id, self.platform_user_id))

            # 2) JE
            print("Inserting STAGING.journal_entries ...")
            cursor.execute(f"""
                INSERT INTO staging.journal_entries (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id, journal_id, entry_date, entry_time,
                    posting_date, reversal_date, effective_date, description,
                    reference_number, source, entry_type,
                    recurring_entry, manual_entry, adjustment_entry, prepared_by, approved_by,
                    approval_date, entry_status, total_debit_amount, total_credit_amount,
                    line_count, fiscal_year, period_number,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    r.je_id, r.journal_id, r.entry_date, r.entry_time,
                    r.posting_date, r.reversal_date, r.effective_date, r.description,
                    r.reference_number, r.source, r.entry_type,
                    r.recurring_entry, r.manual_entry, r.adjustment_entry, r.prepared_by, r.approved_by,
                    r.approval_date, r.entry_status, r.total_debit_amount, r.total_credit_amount,
                    r.line_count,
                    ISNULL(r.fiscal_year, {self.fiscal_year}) AS fiscal_year,
                    ISNULL(r.period_number, CASE WHEN r.posting_date IS NOT NULL THEN MONTH(r.posting_date) ELSE 1 END) AS period_number,
                    r.user_defined_01, r.user_defined_02, r.user_defined_03,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM (
                    SELECT
                        journal_entry_id AS je_id,
                        journal_id, entry_date, entry_time,
                        posting_date, reversal_date, effective_date, description,
                        reference_number, source, entry_type,
                        recurring_entry, manual_entry, adjustment_entry, prepared_by, approved_by,
                        approval_date, entry_status, total_debit_amount, total_credit_amount,
                        line_count, fiscal_year, period_number,
                        user_defined_01, user_defined_02, user_defined_03
                    FROM {raw_je_table}
                ) r
            """)

            # 3) JEL (con business_category si viene)
            print("Inserting STAGING.journal_entry_lines ...")
            cursor.execute(f"""
                INSERT INTO staging.journal_entry_lines (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id, reporting_account, line_number,
                    gl_account_number, business_category,
                    amount, debit_credit_indicator,
                    business_unit, cost_center, department, project_code, location,
                    line_description, reference_number, customer_id, vendor_id, product_id,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    r.journal_entry_id, r.reporting_account, r.line_number,
                    r.gl_account_number, r.business_category,
                    r.amount, r.debit_credit_indicator,
                    r.business_unit, r.cost_center, r.department, r.project_code, r.location,
                    r.line_description, r.reference_number, r.customer_id, r.vendor_id, r.product_id,
                    r.user_defined_01, r.user_defined_02, r.user_defined_03,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM {raw_jel_table} r
            """)

            # 4) TB
            print("Inserting STAGING.trial_balance ...")
            cursor.execute(f"""
                INSERT INTO staging.trial_balance (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number,
                    fiscal_year, period_number,
                    reporting_account,
                    period_ending_balance, period_activity_debit, period_activity_credit,
                    period_beginning_balance, period_ending_date,
                    business_unit, cost_center, department,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, updated_by, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    r.gl_account_number,
                    ISNULL(r.fiscal_year, {self.fiscal_year}),
                    ISNULL(r.period_number, CASE WHEN r.period_ending_date IS NOT NULL THEN MONTH(r.period_ending_date) ELSE 1 END),
                    r.reporting_account,
                    r.period_ending_balance, r.period_activity_debit, r.period_activity_credit,
                    r.period_beginning_balance,
                    ISNULL(r.period_ending_date, '{self.period_ending_date}'),
                    r.business_unit, r.cost_center, r.department,
                    r.user_defined_01, r.user_defined_02, r.user_defined_03,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM {raw_tb_table} r
            """)

            conn.commit()
            
            # Limpiar tablas temporales
            print("Cleaning up temporary tables...")
            for table in [raw_je_table, raw_jel_table, raw_tb_table]:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
            
            print("✓ STAGING loaded")

        except Exception as e:
            conn.rollback()
            # Intentar limpiar tablas temporales en caso de error
            try:
                temp_suffix = str(self.dataset_version_id).replace('-', '_')
                for table in [f"staging.raw_journal_entries_{temp_suffix}",
                            f"staging.raw_journal_entry_lines_{temp_suffix}",
                            f"staging.raw_trial_balance_{temp_suffix}"]:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                conn.commit()
            except:
                pass
            raise Exception(f"Error loading staging: {str(e)}")
    '''            

    # ----------------------------------------------------------------------
    # Validación simple de coherencia
    # ----------------------------------------------------------------------
    def validate_data_coherence(self, conn) -> Tuple[bool, List[str]]:
        """Validate data coherence in staging tables"""
        cursor = conn.cursor()
        errors = []

        # Check journal_entry_id not null
        cursor.execute("""
            SELECT COUNT(*) FROM staging.journal_entries
            WHERE dataset_version_id = ?
            AND (journal_entry_id IS NULL OR LEN(TRIM(journal_entry_id)) = 0)
        """, (self.dataset_version_id,))
        invalid_je_count = cursor.fetchone()[0]
        if invalid_je_count > 0:
            errors.append(f"{invalid_je_count} journal entries with null/empty journal_entry_id")

        # Check journal_entry_lines required fields including debit_credit_indicator
        cursor.execute("""
            SELECT COUNT(*) FROM staging.journal_entry_lines
            WHERE dataset_version_id = ?
            AND (journal_entry_id IS NULL OR LEN(TRIM(journal_entry_id)) = 0
                OR gl_account_number IS NULL OR LEN(TRIM(gl_account_number)) = 0
                OR amount IS NULL
                OR debit_credit_indicator IS NULL
                OR LEN(TRIM(debit_credit_indicator)) = 0
                OR debit_credit_indicator NOT IN ('D', 'H'))
        """, (self.dataset_version_id,))
        invalid_jel_count = cursor.fetchone()[0]
        if invalid_jel_count > 0:
            errors.append(f"{invalid_jel_count} journal entry lines with invalid required fields")

        # Check trial_balance required fields
        cursor.execute("""
            SELECT COUNT(*) FROM staging.trial_balance
            WHERE dataset_version_id = ?
            AND (gl_account_number IS NULL OR LEN(TRIM(gl_account_number)) = 0
                OR period_ending_balance IS NULL
                OR period_beginning_balance IS NULL)
        """, (self.dataset_version_id,))
        invalid_tb_count = cursor.fetchone()[0]
        if invalid_tb_count > 0:
            errors.append(f"{invalid_tb_count} trial balance records with invalid required fields")
        
        '''
        cursor.execute("""
            SELECT COUNT(*) FROM staging.chart_of_accounts c
            LEFT JOIN (
                SELECT gl_account_number FROM staging.journal_entry_lines
                WHERE dataset_version_id = ?
                UNION
                SELECT gl_account_number FROM staging.trial_balance
                WHERE dataset_version_id = ?
            ) t ON c.gl_account_number = t.gl_account_number
            WHERE c.dataset_version_id = ?
            AND t.gl_account_number IS NULL
        """, (self.dataset_version_id, self.dataset_version_id, self.dataset_version_id))
        orphan_coa_count = cursor.fetchone()[0]
        if orphan_coa_count > 0:
            errors.append(f"{orphan_coa_count} chart_of_accounts records not referenced by any JEL or TB")
        '''

        return len(errors) == 0, errors
    
    
    # ----------------------------------------------------------------------
    # Busca líneas "huérfanas" (journal_entry_id en lines que no existe en entries)
    # ----------------------------------------------------------------------
    def validate_referential_integrity(self, conn) -> Tuple[bool, Dict[str, Any]]:
        """Validate that all journal_entry_lines reference existing journal_entries"""
        cursor = conn.cursor()
        
        # Find orphaned journal_entry_lines (IDs in lines but not in entries)
        cursor.execute("""
            SELECT DISTINCT jel.journal_entry_id, COUNT(*) as line_count
            FROM staging.journal_entry_lines jel
            LEFT JOIN staging.journal_entries je 
            ON je.dataset_version_id = jel.dataset_version_id
            AND je.journal_entry_id = jel.journal_entry_id
            WHERE jel.dataset_version_id = ?
            AND je.journal_entry_id IS NULL
            GROUP BY jel.journal_entry_id
            ORDER BY line_count DESC
        """, (self.dataset_version_id,))
        
        orphaned = cursor.fetchall()
        
        if orphaned:
            orphaned_dict = {row[0]: row[1] for row in orphaned}
            return False, {
                'orphaned_count': len(orphaned),
                'orphaned_ids': orphaned_dict,
                'total_orphaned_lines': sum(orphaned_dict.values())
            }
        
        return True, {}
    
    
    # ----------------------------------------------------------------------
    # Valida la Totalidad (sin mapeo)
    # ----------------------------------------------------------------------
    def validate_totality(self, conn) -> Tuple[bool, pd.DataFrame]:
        """Validate that journal_entry_lines totals match trial_balance movements (without mapping)"""
        cursor = conn.cursor()

        # Get net movements from journal_entry_lines by account
        cursor.execute("""
            SELECT
                gl_account_number,
                SUM(amount) as net_movement
            FROM staging.journal_entry_lines
            WHERE dataset_version_id = ?
            GROUP BY gl_account_number
        """, (self.dataset_version_id,))
        jel_totals = {row[0]: row[1] for row in cursor.fetchall()}

        # Get expected movements from trial_balance
        cursor.execute("""
            SELECT
                gl_account_number,
                ISNULL(period_beginning_balance, 0) as beginning_balance,
                ISNULL(period_ending_balance, 0) as ending_balance,
                ISNULL(period_ending_balance, 0) - ISNULL(period_beginning_balance, 0) as expected_movement
            FROM staging.trial_balance
            WHERE dataset_version_id = ?
        """, (self.dataset_version_id,))
        tb_movements = {row[0]: {'beginning': row[1], 'ending': row[2], 'expected': row[3]}
                    for row in cursor.fetchall()}

        # Create list for all accounts
        all_accounts = set(list(tb_movements.keys()) + list(jel_totals.keys()))
        totality_data = []

        # Compare movements for all accounts
        for account in all_accounts:
            expected = tb_movements.get(account, {}).get('expected', 0)
            actual = jel_totals.get(account, 0)
            beginning = tb_movements.get(account, {}).get('beginning', 0)
            ending = tb_movements.get(account, {}).get('ending', 0)

            # For P&L accounts (6-7), compare against ending balance instead of movement
            if str(account).startswith(('6', '7')):
                diff_value = actual - ending
            else:
                diff_value = actual - expected

            note = ''
            if account not in tb_movements:
                note = 'Account not in trial_balance'
            elif account not in jel_totals:
                note = 'Account not in journal_entry_lines'

            totality_data.append({
                'account': account,
                'expected_movement': expected,
                'actual_movement': actual,
                'difference': diff_value,
                'beginning_balance': beginning,
                'ending_balance': ending,
                'note': note
            })

        # Create DataFrame
        df_totality = pd.DataFrame(totality_data)
        df_totality = df_totality.sort_values('account')

        # Check if there are significant differences
        has_errors = (df_totality['difference'].abs() > 0.01).any()

        return not has_errors, df_totality
    
    
    # ----------------------------------------------------------------------
    # Valida la Totalidad (con mapeo)
    # ----------------------------------------------------------------------
    def validate_totality_with_mapping(self, conn) -> Tuple[bool, pd.DataFrame]:
        """Validate that journal_entry_lines totals match trial_balance movements using reporting_account"""
        cursor = conn.cursor()

        # Get net movements from journal_entry_lines by reporting_account
        cursor.execute("""
            SELECT
                tb.reporting_account,
                SUM(jel.amount) as net_movement
            FROM staging.journal_entry_lines jel
            INNER JOIN (
                SELECT DISTINCT 
                    tenant_id, workspace_id, project_id, entity_id, 
                    dataset_id, dataset_version_id,
                    gl_account_number, reporting_account
                FROM staging.trial_balance
                WHERE dataset_version_id = ?
                AND reporting_account IS NOT NULL
            ) tb ON tb.dataset_version_id = jel.dataset_version_id
                AND tb.gl_account_number = jel.gl_account_number
            WHERE jel.dataset_version_id = ?
            GROUP BY tb.reporting_account
        """, (self.dataset_version_id, self.dataset_version_id))
        jel_totals = {row[0]: row[1] for row in cursor.fetchall()}

        # Get expected movements from trial_balance grouped by reporting_account
        cursor.execute("""
            SELECT
                reporting_account,
                SUM(ISNULL(period_beginning_balance, 0)) as beginning_balance,
                SUM(ISNULL(period_ending_balance, 0)) as ending_balance,
                SUM(ISNULL(period_ending_balance, 0) - ISNULL(period_beginning_balance, 0)) as expected_movement
            FROM staging.trial_balance
            WHERE dataset_version_id = ?
            AND reporting_account IS NOT NULL
            GROUP BY reporting_account
        """, (self.dataset_version_id,))
        tb_movements = {row[0]: {'beginning': row[1], 'ending': row[2], 'expected': row[3]}
                    for row in cursor.fetchall()}

        # Create list for all reporting accounts
        all_accounts = set(list(tb_movements.keys()) + list(jel_totals.keys()))
        totality_data = []

        # Compare movements for all accounts
        for reporting_account in all_accounts:
            expected = tb_movements.get(reporting_account, {}).get('expected', 0)
            actual = jel_totals.get(reporting_account, 0)
            beginning = tb_movements.get(reporting_account, {}).get('beginning', 0)
            ending = tb_movements.get(reporting_account, {}).get('ending', 0)

            # For P&L reporting accounts (starting with 6-7), compare against ending balance
            if str(reporting_account).startswith(('6', '7')):
                diff_value = actual - ending
            else:
                diff_value = actual - expected

            note = ''
            if reporting_account not in tb_movements:
                note = 'Reporting account not in trial_balance'
            elif reporting_account not in jel_totals:
                note = 'Reporting account not in journal_entry_lines'

            totality_data.append({
                'reporting_account': reporting_account,
                'expected_movement': expected,
                'actual_movement': actual,
                'difference': diff_value,
                'beginning_balance': beginning,
                'ending_balance': ending,
                'note': note
            })

        # Create DataFrame
        df_totality = pd.DataFrame(totality_data)
        df_totality = df_totality.sort_values('reporting_account')

        # Check if there are significant differences
        has_errors = (df_totality['difference'].abs() > 0.01).any()

        return not has_errors, df_totality
    
    
    # ----------------------------------------------------------------------
    # Validación de completitud del mapeo
    # ----------------------------------------------------------------------
    def check_mapping_completeness(self, conn) -> Tuple[bool, List[str]]:
        """Check that all accounts have reporting account mappings"""
        cursor = conn.cursor()
        
        # Get unique accounts from journal_entry_lines
        cursor.execute("""
            SELECT DISTINCT gl_account_number
            FROM staging.journal_entry_lines
            WHERE dataset_version_id = ?
            AND gl_account_number IS NOT NULL
        """, (self.dataset_version_id,))
        jel_accounts = set(row[0] for row in cursor.fetchall())
        
        # Get accounts with reporting mappings
        cursor.execute("""
            SELECT DISTINCT gl_account_number
            FROM staging.trial_balance
            WHERE dataset_version_id = ?
            AND reporting_account IS NOT NULL
        """, (self.dataset_version_id,))
        mapped_accounts = set(row[0] for row in cursor.fetchall())
        
        # Find unmapped accounts
        unmapped = list(jel_accounts - mapped_accounts)
        
        return len(unmapped) == 0, unmapped
    
    
    # ----------------------------------------------------------------------
    # Limpieza del staging
    # ----------------------------------------------------------------------
    def clean_staging_tables(self, conn):
        """Clean all staging tables for this dataset_version"""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM staging.journal_entry_lines WHERE dataset_version_id = ?", (self.dataset_version_id,))
        cursor.execute("DELETE FROM staging.journal_entries WHERE dataset_version_id = ?", (self.dataset_version_id,))
        cursor.execute("DELETE FROM staging.trial_balance WHERE dataset_version_id = ?", (self.dataset_version_id,))
        cursor.execute("DELETE FROM staging.chart_of_accounts WHERE dataset_version_id = ?", (self.dataset_version_id,))
        conn.commit()
    
    
    # ----------------------------------------------------------------------
    # Actualiza estadísticas
    # ----------------------------------------------------------------------
    def update_dataset_version_stats(self, conn):
        """Update dataset version statistics after loading"""
        cursor = conn.cursor()
        try:
            # Count total records loaded
            cursor.execute(f"""
                SELECT
                    (SELECT COUNT(*) FROM ads.journal_entries WHERE dataset_version_id = {self.dataset_version_id}) +
                    (SELECT COUNT(*) FROM ads.journal_entry_lines WHERE dataset_version_id = {self.dataset_version_id}) +
                    (SELECT COUNT(*) FROM ads.trial_balance WHERE dataset_version_id = {self.dataset_version_id}) +
                    (SELECT COUNT(*) FROM ads.chart_of_accounts WHERE dataset_version_id = {self.dataset_version_id}) as total_records
            """)
            total_records = cursor.fetchone()[0]
            
            # Update dataset_version with statistics
            cursor.execute(f"""
                UPDATE workspace.dataset_version
                SET record_count = ?, updated_at = GETUTCDATE()
                WHERE id = ?
            """, (total_records, self.dataset_version_id))
            conn.commit()
        except Exception as e:
            raise Exception(f"Error updating dataset version stats: {str(e)}")
    
    # ----------------------------------------------------------------------
    # Carga a ADS (manteniendo entry_type y copiando business_category ORIGINAL)
    # ----------------------------------------------------------------------
    def load_to_ads(self, conn):
        cursor = conn.cursor()
        try:
            print(f"Cleaning ADS for dataset_version_id {self.dataset_version_id}...")
            cursor.execute(f"DELETE FROM analytics.entry_type WHERE dataset_version_id = {self.dataset_version_id}")
            cursor.execute(f"DELETE FROM analytics.account_combination WHERE dataset_version_id = {self.dataset_version_id}")
            cursor.execute(f"DELETE FROM ads.journal_entry_lines WHERE dataset_version_id = {self.dataset_version_id}")
            cursor.execute(f"DELETE FROM ads.journal_entries WHERE dataset_version_id = {self.dataset_version_id}")
            cursor.execute(f"DELETE FROM ads.trial_balance WHERE dataset_version_id = {self.dataset_version_id}")
            cursor.execute(f"DELETE FROM ads.chart_of_accounts WHERE dataset_version_id = {self.dataset_version_id}")
            conn.commit()

            # COA
            cursor.execute(f"""
                INSERT INTO ads.chart_of_accounts (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number, gl_account_name, account_type, account_description,
                    parent_account_number, account_level, account_hierarchy, is_active, posting_account,
                    financial_statement_line_item, financial_statement_section, report_sequence,
                    normal_balance, account_category, account_subcategory,
                    account_creation_date, account_closure_date, effective_date,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, created_at, updated_by, updated_at, batch_id
                )
                SELECT
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number, gl_account_name, account_type, account_description,
                    parent_account_number, account_level, account_hierarchy, is_active, posting_account,
                    financial_statement_line_item, financial_statement_section, report_sequence,
                    normal_balance, account_category, account_subcategory,
                    account_creation_date, account_closure_date, effective_date,
                    user_defined_01, user_defined_02, user_defined_03,
                    {self.platform_user_id}, GETUTCDATE(), {self.platform_user_id}, GETUTCDATE(), batch_id
                FROM staging.chart_of_accounts
                WHERE dataset_version_id = {self.dataset_version_id}
            """)
            conn.commit()

            # JE (INCLUYE entry_type)
            cursor.execute(f"""
                INSERT INTO ads.journal_entries (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id, journal_id, entry_date, entry_time,
                    posting_date, reversal_date, effective_date, description,
                    reference_number, source, entry_type,
                    recurring_entry, manual_entry, adjustment_entry, prepared_by, approved_by,
                    approval_date, entry_status, total_debit_amount, total_credit_amount,
                    line_count, fiscal_year, period_number,
                    user_defined_01, user_defined_02, user_defined_03, 
                    created_by, created_at, updated_by, updated_at, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    journal_entry_id, journal_id, entry_date, entry_time,
                    posting_date, reversal_date, effective_date, description,
                    reference_number, source, entry_type,
                    recurring_entry, manual_entry, adjustment_entry, prepared_by, approved_by,
                    approval_date, entry_status, total_debit_amount, total_credit_amount,
                    line_count, fiscal_year, period_number,
                    user_defined_01, user_defined_02, user_defined_03,
                    {self.platform_user_id}, GETUTCDATE(), {self.platform_user_id}, GETUTCDATE(), batch_id
                FROM staging.journal_entries
                WHERE dataset_version_id = {self.dataset_version_id}
            """)
            conn.commit()

            # JEL (COPIA business_category ORIGINAL de staging)
            cursor.execute(f"""
                INSERT INTO ads.journal_entry_lines (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id, line_number, gl_account_number,
                    amount, debit_credit_indicator,
                    business_unit, cost_center, department, project_code, location,
                    line_description, reference_number, customer_id, vendor_id, product_id,
                    user_defined_01, user_defined_02, user_defined_03,
                    business_category,
                    created_by, created_at, updated_by, updated_at, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    journal_entry_id, line_number, gl_account_number,
                    amount, debit_credit_indicator,
                    business_unit, cost_center, department, project_code, location,
                    line_description, reference_number, customer_id, vendor_id, product_id,
                    user_defined_01, user_defined_02, user_defined_03,
                    business_category,  -- valor ORIGINAL de staging
                    {self.platform_user_id}, GETUTCDATE(), {self.platform_user_id}, GETUTCDATE(), batch_id
                FROM staging.journal_entry_lines
                WHERE dataset_version_id = {self.dataset_version_id}
            """)
            conn.commit()

            # TB
            cursor.execute(f"""
                INSERT INTO ads.trial_balance (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    gl_account_number, reporting_account, fiscal_year, period_number,
                    period_ending_balance, period_activity_debit, period_activity_credit,
                    period_beginning_balance, period_ending_date,
                    business_unit, cost_center, department,
                    user_defined_01, user_defined_02, user_defined_03,
                    created_by, created_at, updated_by, updated_at, batch_id
                )
                SELECT
                    {self.tenant_id}, {self.workspace_id}, {self.project_id}, {self.entity_id},
                    {self.dataset_id}, {self.dataset_version_id},
                    gl_account_number, reporting_account, fiscal_year, period_number,
                    period_ending_balance, period_activity_debit, period_activity_credit,
                    period_beginning_balance, period_ending_date,
                    business_unit, cost_center, department,
                    user_defined_01, user_defined_02, user_defined_03,
                    {self.platform_user_id}, GETUTCDATE(), {self.platform_user_id}, GETUTCDATE(), batch_id
                FROM staging.trial_balance
                WHERE dataset_version_id = {self.dataset_version_id}
            """)
            conn.commit()

            print("✓ ADS loaded")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error loading data to ADS: {str(e)}")

    # ----------------------------------------------------------------------
    # ANALYTICS
    # ----------------------------------------------------------------------
    def upsert_analytics_account_combination(self, conn, uses_mapping: bool = False):
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM analytics.account_combination WHERE dataset_version_id = {self.dataset_version_id}")

            if uses_mapping:
                bitmask_sql = """
                    CASE WHEN LEFT(CAST(ISNULL(tb.reporting_account, jel.gl_account_number) AS VARCHAR), 3) IN ('700','701','702','703','704','705') THEN 1 ELSE 0 END
                  + CASE WHEN LEFT(CAST(ISNULL(tb.reporting_account, jel.gl_account_number) AS VARCHAR), 3) = '430' THEN 2 ELSE 0 END
                  + CASE WHEN CAST(ISNULL(tb.reporting_account, jel.gl_account_number) AS VARCHAR) = '572' THEN 4 ELSE 0 END
                  + CASE WHEN CAST(ISNULL(tb.reporting_account, jel.gl_account_number) AS VARCHAR) = '570' THEN 8 ELSE 0 END
                """
                join_tb = f"""
                    LEFT JOIN (
                        SELECT DISTINCT tenant_id, workspace_id, project_id, entity_id, dataset_id, dataset_version_id,
                                        gl_account_number, reporting_account
                        FROM staging.trial_balance
                        WHERE dataset_version_id = {self.dataset_version_id}
                    ) tb
                      ON tb.tenant_id = jel.tenant_id
                     AND tb.workspace_id = jel.workspace_id
                     AND tb.project_id = jel.project_id
                     AND tb.entity_id = jel.entity_id
                     AND tb.dataset_id = jel.dataset_id
                     AND tb.dataset_version_id = jel.dataset_version_id
                     AND tb.gl_account_number = jel.gl_account_number
                """
                comb_expr = f"""
                    SELECT STRING_AGG(val, ' | ') WITHIN GROUP (ORDER BY val)
                    FROM (
                        SELECT DISTINCT LEFT(CAST(ISNULL(tb2.reporting_account, jel2.gl_account_number) AS VARCHAR), 3) AS val
                        FROM staging.journal_entry_lines jel2
                        LEFT JOIN (
                            SELECT DISTINCT tenant_id, workspace_id, project_id, entity_id, dataset_id, dataset_version_id,
                                            gl_account_number, reporting_account
                            FROM staging.trial_balance
                            WHERE dataset_version_id = {self.dataset_version_id}
                        ) tb2
                          ON tb2.tenant_id = jel2.tenant_id
                         AND tb2.workspace_id = jel2.workspace_id
                         AND tb2.project_id = jel2.project_id
                         AND tb2.entity_id = jel2.entity_id
                         AND tb2.dataset_id = jel2.dataset_id
                         AND tb2.dataset_version_id = jel2.dataset_version_id
                         AND tb2.gl_account_number = jel2.gl_account_number
                        WHERE jel2.dataset_version_id = jel.dataset_version_id
                          AND jel2.journal_entry_id = jel.journal_entry_id
                          AND jel2.gl_account_number IS NOT NULL
                    ) x
                """
            else:
                bitmask_sql = """
                    CASE WHEN LEFT(CAST(jel.gl_account_number AS VARCHAR), 3) IN ('700','701','702','703','704','705') THEN 1 ELSE 0 END
                  + CASE WHEN LEFT(CAST(jel.gl_account_number AS VARCHAR), 3) = '430' THEN 2 ELSE 0 END
                  + CASE WHEN CAST(jel.gl_account_number AS VARCHAR) = '572' THEN 4 ELSE 0 END
                  + CASE WHEN CAST(jel.gl_account_number AS VARCHAR) = '570' THEN 8 ELSE 0 END
                """
                join_tb = ""
                comb_expr = """
                    SELECT STRING_AGG(val, ' | ') WITHIN GROUP (ORDER BY val)
                    FROM (
                        SELECT DISTINCT LEFT(CAST(jel2.gl_account_number AS VARCHAR), 3) AS val
                        FROM staging.journal_entry_lines jel2
                        WHERE jel2.dataset_version_id = jel.dataset_version_id
                          AND jel2.journal_entry_id = jel.journal_entry_id
                          AND jel2.gl_account_number IS NOT NULL
                    ) x
                """

            cursor.execute(f"""
                INSERT INTO analytics.account_combination (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id,
                    bitmask, account_combination,
                    created_by, updated_by, batch_id
                )
                SELECT
                    jel.tenant_id, jel.workspace_id, jel.project_id, jel.entity_id,
                    jel.dataset_id, jel.dataset_version_id,
                    jel.journal_entry_id,
                    SUM({bitmask_sql}) AS bitmask,
                    ({comb_expr}) AS account_combination,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM staging.journal_entry_lines jel
                {join_tb}
                WHERE jel.dataset_version_id = {self.dataset_version_id}
                  AND jel.gl_account_number IS NOT NULL
                GROUP BY jel.tenant_id, jel.workspace_id, jel.project_id, jel.entity_id,
                         jel.dataset_id, jel.dataset_version_id, jel.journal_entry_id
            """)
            conn.commit()
            print("✓ analytics.account_combination loaded")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error inserting analytics.account_combination: {str(e)}")

    def insert_analytics_entry_type(self, conn):
        """
        Inserta business_category a nivel de línea en analytics.entry_type.
        *** SIEMPRE CALCULADO *** (no usa staging).
        - Calcula con CASE usando ads.chart_of_accounts + ads.journal_entry_lines.line_description.
        - FK -> ADS.journal_entry_lines.
        """
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM analytics.entry_type WHERE dataset_version_id = {self.dataset_version_id}")

            business_category_case = """
                CASE 
                    WHEN LOWER(ISNULL(coa.gl_account_name, a.line_description)) LIKE '%ventas de mercader%' 
                         AND a.debit_credit_indicator = 'C' THEN 'Ventas'
                    WHEN LOWER(ISNULL(coa.gl_account_name, a.line_description)) LIKE '%clientes%' 
                         AND a.debit_credit_indicator = 'D' THEN 'Clientes'
                    WHEN LOWER(ISNULL(coa.gl_account_name, a.line_description)) LIKE '%tesorería%' 
                         AND a.debit_credit_indicator = 'D' THEN 'Tesorería'
                    ELSE 'Otros' 
                END
            """

            cursor.execute(f"""
                INSERT INTO analytics.entry_type (
                    tenant_id, workspace_id, project_id, entity_id,
                    dataset_id, dataset_version_id,
                    journal_entry_id, line_number,
                    business_category,
                    created_by, updated_by, batch_id
                )
                SELECT
                    a.tenant_id, a.workspace_id, a.project_id, a.entity_id,
                    a.dataset_id, a.dataset_version_id,
                    a.journal_entry_id, a.line_number,
                    {business_category_case} AS business_category,
                    {self.platform_user_id}, {self.platform_user_id}, NEWID()
                FROM ads.journal_entry_lines a
                LEFT JOIN ads.chart_of_accounts coa
                  ON coa.dataset_version_id = a.dataset_version_id
                 AND coa.gl_account_number = a.gl_account_number
                WHERE a.dataset_version_id = {self.dataset_version_id}
            """)
            conn.commit()
            print("✓ analytics.entry_type loaded")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error inserting analytics.entry_type: {str(e)}")

    # ----------------------------------------------------------------------
    # Dependencias (proyecto/dataset/dataset_version)
    # ----------------------------------------------------------------------
    def ensure_dataset_version_exists(self, conn):
        cursor = conn.cursor()
        try:
            # 1. VERIFICAR/CREAR WORKSPACE - SOLO POR ID (PK)
            print(f"Checking workspace: tenant_id={self.tenant_id}, workspace_id={self.workspace_id}")
            
            # La PK es solo sobre ID, no sobre tenant_id + id
            cursor.execute("""
                SELECT id, tenant_id, short_name, name 
                FROM tenant.workspace 
                WHERE id = ?
            """, (self.workspace_id,))
            
            workspace_row = cursor.fetchone()
            
            if workspace_row is None:
                print(f"Workspace {self.workspace_id} not found, creating...")
                
                # Verificar si ya existe un workspace principal para este tenant
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM tenant.workspace 
                    WHERE tenant_id = ? AND is_main = 1
                """, (self.tenant_id,))
                
                has_main_workspace = cursor.fetchone()[0] > 0
                
                cursor.execute("""
                    INSERT INTO tenant.workspace (
                        id, tenant_id, is_main, workspace_state_id,
                        short_name, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (
                    self.workspace_id, 
                    self.tenant_id,
                    0 if has_main_workspace else 1,
                    1,
                    f'WS{self.workspace_id}',
                    f'Workspace {self.workspace_id}',
                    'Auto-created workspace for accounting data',
                    self.platform_user_id, 
                    self.platform_user_id
                ))
                conn.commit()
                print(f"✓ Created workspace {self.workspace_id}")
            else:
                # El workspace existe, verificar que sea del tenant correcto
                existing_tenant_id = workspace_row[1]
                if existing_tenant_id != self.tenant_id:
                    raise Exception(
                        f"Workspace {self.workspace_id} already exists but belongs to tenant {existing_tenant_id}, "
                        f"not tenant {self.tenant_id}. Use a different workspace_id."
                    )
                print(f"✓ Workspace {self.workspace_id} already exists: {workspace_row[2]} - {workspace_row[3]}")
            
            # 2. VERIFICAR/CREAR ENTITY - BUSCAR POR CLAVE COMPUESTA
            cursor.execute("""
                SELECT id FROM workspace.entity 
                WHERE id = ?
            """, (self.entity_id,))
            
            entity_row = cursor.fetchone()
            
            if entity_row is None:
                cursor.execute("""
                    INSERT INTO workspace.entity (
                        id, tenant_id, workspace_id, is_active,
                        code, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (
                    self.entity_id,
                    self.tenant_id,
                    self.workspace_id,
                    1,
                    f'ENT{self.entity_id}',
                    f'Entity {self.entity_id}',
                    'Auto-created entity for accounting data',
                    self.platform_user_id,
                    self.platform_user_id
                ))
                conn.commit()
                print(f"✓ Created entity {self.entity_id}")
            else:
                print(f"✓ Entity {self.entity_id} already exists")
            
            # 3. VERIFICAR/CREAR OFFICE - BUSCAR POR ID
            cursor.execute("""
                SELECT id FROM workspace.office 
                WHERE id = 1
            """, ())
            
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO workspace.office (
                        id, tenant_id, workspace_id, is_active,
                        code, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (1, ?, ?, 1, 'OFF001', 'Main Office', 'Default office', 
                            ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (self.tenant_id, self.workspace_id, self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created office")
            else:
                print(f"✓ Office already exists")
            
            # 4. VERIFICAR/CREAR DEPARTMENT - BUSCAR POR ID
            cursor.execute("""
                SELECT id FROM workspace.department 
                WHERE id = 1
            """, ())
            
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO workspace.department (
                        id, tenant_id, workspace_id, is_active,
                        code, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (1, ?, ?, 1, 'DEPT001', 'Main Department', 'Default department',
                            ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (self.tenant_id, self.workspace_id, self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created department")
            else:
                print(f"✓ Department already exists")
            
            # 5. VERIFICAR/CREAR SERVICE - BUSCAR POR ID
            cursor.execute("""
                SELECT id FROM workspace.service 
                WHERE id = 1
            """, ())
            
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO workspace.service (
                        id, tenant_id, workspace_id, is_active,
                        service_category_id, code, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (1, ?, ?, 1, 1, 'SRV001', 'Accounting Service', 'Default service',
                            ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (self.tenant_id, self.workspace_id, self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created service")
            else:
                print(f"✓ Service already exists")
            
            # 6. VERIFICAR/CREAR PROJECT_STATE - BUSCAR POR ID
            cursor.execute("""
                SELECT id FROM workspace.project_state 
                WHERE id = 1
            """, ())
            
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO workspace.project_state (
                        id, tenant_id, workspace_id, is_active,
                        project_state_category_id, code, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (1, ?, ?, 1, 1, 'ACTIVE', 'Active', 'Active project state',
                            ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (self.tenant_id, self.workspace_id, self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created project_state")
            else:
                print(f"✓ Project_state already exists")
            
            # 7. VERIFICAR/CREAR PROJECT - BUSCAR POR ID
            cursor.execute("""
                SELECT tenant_id, workspace_id 
                FROM workspace.project 
                WHERE id = ?
            """, (self.project_id,))
            project_row = cursor.fetchone()
            
            if project_row is None:
                cursor.execute("""
                    INSERT INTO workspace.project (
                        id, tenant_id, workspace_id, code, name, description,
                        project_state_id, project_analysis_state_id,
                        main_entity_id, service_id, office_id, department_id,
                        start_date, end_date, fs_date,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (
                    self.project_id, self.tenant_id, self.workspace_id, 
                    f'ACC{self.project_id}',
                    'Accounting Project', 
                    'Project for accounting data analysis',
                    1, 1, self.entity_id, 1, 1, 1, 
                    '2024-01-01', '2024-12-31', '2024-12-31',
                    self.platform_user_id, self.platform_user_id
                ))
                conn.commit()
                print(f"✓ Created project {self.project_id}")
                project_tenant_id, project_workspace_id = self.tenant_id, self.workspace_id
            else:
                project_tenant_id, project_workspace_id = project_row[0], project_row[1]
                print(f"✓ Project {self.project_id} already exists")

            self.tenant_id = project_tenant_id
            self.workspace_id = project_workspace_id

            # 8. VERIFICAR/CREAR PROJECT_ANALYSIS_ENTITY
            cursor.execute("""
                SELECT id FROM workspace.project_analysis_entity
                WHERE project_id = ? AND entity_id = ?
            """, (self.project_id, self.entity_id))
            
            if cursor.fetchone() is None:
                cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM workspace.project_analysis_entity")
                next_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO workspace.project_analysis_entity (
                        id, tenant_id, workspace_id, is_active, project_id, entity_id,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (next_id, project_tenant_id, project_workspace_id, 1, self.project_id,
                    self.entity_id, self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created project_analysis_entity")
            else:
                print(f"✓ Project_analysis_entity already exists")

            # 9. VERIFICAR/CREAR DATASET - BUSCAR POR ID
            cursor.execute("SELECT id FROM workspace.dataset WHERE id = ?", (self.dataset_id,))
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO workspace.dataset (
                        id, tenant_id, workspace_id, project_id, entity_id,
                        dataset_state_id, dataset_type_id, name, description,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (self.dataset_id, project_tenant_id, project_workspace_id, self.project_id,
                    self.entity_id, 1, 1, 'Accounting Dataset', 'Dataset for accounting data import',
                    self.platform_user_id, self.platform_user_id))
                conn.commit()
                print(f"✓ Created dataset {self.dataset_id}")
            else:
                print(f"✓ Dataset {self.dataset_id} already exists")

            # 10. VERIFICAR/CREAR DATASET_VERSION - BUSCAR POR ID
            cursor.execute("SELECT id FROM workspace.dataset_version WHERE id = ?", (self.dataset_version_id,))
            if cursor.fetchone() is None:
                cursor.execute("""
                    SELECT MAX(version_number) FROM workspace.dataset_version
                    WHERE tenant_id = ? AND workspace_id = ? AND project_id = ?
                    AND entity_id = ? AND dataset_id = ?
                """, (project_tenant_id, project_workspace_id, self.project_id, self.entity_id, self.dataset_id))
                result = cursor.fetchone()
                max_version = result[0] if result[0] is not None else 0
                new_version_number = max_version + 1
                
                if max_version > 0:
                    cursor.execute("""
                        UPDATE workspace.dataset_version
                        SET is_published_to_analytics = 0
                        WHERE tenant_id = ? AND workspace_id = ? AND project_id = ?
                        AND entity_id = ? AND dataset_id = ?
                    """, (project_tenant_id, project_workspace_id, self.project_id, self.entity_id, self.dataset_id))
                    conn.commit()
                
                cursor.execute("""
                    INSERT INTO workspace.dataset_version (
                        id, tenant_id, workspace_id, project_id, entity_id, dataset_id,
                        version_number, dataset_version_state_id, name, description,
                        file_count, record_count, total_file_size_bytes, is_published_to_analytics,
                        created_by, created_at, updated_by, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?, GETUTCDATE())
                """, (
                    self.dataset_version_id, project_tenant_id, project_workspace_id,
                    self.project_id, self.entity_id, self.dataset_id, new_version_number, 1,
                    f'Accounting Data v{new_version_number}',
                    f'Dataset version {new_version_number} for accounting data import',
                    3, 0, 0, 1, self.platform_user_id, self.platform_user_id
                ))
                conn.commit()
                print(f"✓ Created dataset_version {self.dataset_version_id} (v{new_version_number})")
            else:
                print(f"✓ Dataset_version {self.dataset_version_id} already exists")
            
            print("✓ All dependencies verified/created successfully")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error ensuring dataset version exists: {str(e)}")

    # ----------------------------------------------------------------------
    # Proceso principal
    # ----------------------------------------------------------------------
    def process_data_load(self, je_file: str, jel_file: str, tb_file: str, needs_mapping: bool = None):
        if needs_mapping is None:
            needs_mapping = self.uses_mapping_default

        print("=" * 60)
        print("Starting data load process (staging → ads → analytics)")
        print(f"Mode: {'WITH MAPPING' if needs_mapping else 'WITHOUT MAPPING'}")
        print(f"Dataset Version ID: {self.dataset_version_id}")
        print("=" * 60)
        
        conn = None
        totality_df = None
        
        try:
            conn = pyodbc.connect(get_connection_string())

            # Phase 1: Ensure dependencies
            t0 = time.time()
            self.ensure_dataset_version_exists(conn)
            print(f"\n✓ Phase 1 - Ensure dependencies: {time.time() - t0:.2f}s")

            # Phase 2: Load STAGING from CSV files
            t1 = time.time()
            self.bulk_insert_files(conn, je_file, jel_file, tb_file)
            print(f"✓ Phase 2 - Load STAGING: {time.time() - t1:.2f}s")

            # Phase 3: Validate STAGING data
            t2 = time.time()
            
            # Coherence validation
            ok, errs = self.validate_data_coherence(conn)
            if not ok:
                self.clean_staging_tables(conn)
                raise Exception(f"Coherence validation failed: {errs}")
            
            # Referential integrity validation
            ref_valid, ref_info = self.validate_referential_integrity(conn)
            if not ref_valid:
                self.clean_staging_tables(conn)
                error_msg = f"Referential integrity validation failed:\n"
                error_msg += f"  - {ref_info['orphaned_count']} journal_entry_ids in lines without matching entries\n"
                error_msg += f"  - {ref_info['total_orphaned_lines']} total orphaned lines\n"
                error_msg += f"  - First 10 orphaned IDs: {list(ref_info['orphaned_ids'].keys())[:10]}"
                raise Exception(error_msg)
            
            # Totality validation
            if needs_mapping:
                # Check mapping completeness first
                mapping_ok, unmapped = self.check_mapping_completeness(conn)
                if not mapping_ok:
                    print(f"\n⚠ Warning: {len(unmapped)} accounts without reporting_account mapping")
                    print(f"Unmapped accounts (first 10): {unmapped[:10]}")
                    self.clean_staging_tables(conn)
                    return {
                        'success': False, 
                        'unmapped_accounts': unmapped,
                        'totality_df': None
                    }
                totality_ok, totality_df = self.validate_totality_with_mapping(conn)
            else:
                totality_ok, totality_df = self.validate_totality(conn)
            
            if not totality_ok:
                diff_count = (totality_df['difference'].abs() > 0.01).sum()
                print(f"\n⚠ Warning: Totality validation found differences in {diff_count} accounts")
            
            print(f"✓ Phase 3 - Validate STAGING: {time.time() - t2:.2f}s")

            # Phase 4: Load ADS
            t3 = time.time()
            self.load_to_ads(conn)
            print(f"✓ Phase 4 - Load ADS: {time.time() - t3:.2f}s")

            # Phase 5: Load ANALYTICS
            t4 = time.time()
            self.upsert_analytics_account_combination(conn, uses_mapping=needs_mapping)
            self.insert_analytics_entry_type(conn)
            print(f"✓ Phase 5 - Load ANALYTICS: {time.time() - t4:.2f}s")

            # Phase 6: Update stats and cleanup
            t5 = time.time()
            self.update_dataset_version_stats(conn)
            self.clean_staging_tables(conn)
            print(f"✓ Phase 6 - Stats & cleanup: {time.time() - t5:.2f}s")

            print("\n" + "=" * 60)
            print(f"✓ Process completed successfully in {time.time() - t0:.2f}s")
            print("=" * 60)
            
            return {
                "success": True,
                "totality_df": totality_df
            }

        except Exception as e:
            print(f"\n✗ Process failed: {e}")
            if conn:
                conn.rollback()
                try:
                    self.clean_staging_tables(conn)
                except:
                    pass
            return {
                "success": False, 
                "error": str(e),
                "totality_df": totality_df
            }
        finally:
            if conn:
                conn.close()


def main():
    """Main function for command-line execution"""
    # Parámetros de ejemplo para testing
    loader = AccountingDataLoader(
        workspace_id=101,
        project_id=101,
        entity_id=101,
        fiscal_year=2024,
        period_ending_date='2024-12-31',
        dataset_version_id=201
    )

    # Archivos CSV
    je_file = "libro-diario-resultados/je/journal_entries_Redur.csv"
    jel_file = "libro-diario-resultados/je/journal_entry_lines_Redur.csv"
    tb_file = "libro-diario-resultados/sys/trial_balance_Redur.csv"

    # ¿Usar mapping de reporting_account para bitmask/combination?
    needs_mapping = False

    result = loader.process_data_load(je_file, jel_file, tb_file, needs_mapping)

    if result["success"]:
        print("\nProcess completed successfully")
        
        # Export totality DataFrame to CSV if available
        if result.get('totality_df') is not None:
            output_file = 'totality_validation_report.csv'
            result['totality_df'].to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\nTotality validation report exported to: {output_file}")            
        return 0
    else:
        print("\nProcess failed")
        if 'unmapped_accounts' in result:
            print(f"Unmapped accounts: {len(result['unmapped_accounts'])}")
            print(f"First 10: {result['unmapped_accounts'][:10]}")
        elif 'error' in result:
            print(f"Error: {result['error']}")
        
        # Export totality DataFrame even if process failed
        if result.get('totality_df') is not None:
            output_file = 'totality_validation_report_FAILED.csv'
            result['totality_df'].to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\nTotality validation report exported to: {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

