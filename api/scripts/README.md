# Scripts de Consulta

## query_audit_test_exec.py

Script para consultar los registros guardados en la tabla `workspace.audit_test_exec`.

### Uso

#### 1. Ver los últimos 10 registros (default)
```bash
cd api
python scripts/query_audit_test_exec.py
```

#### 2. Ver los últimos N registros
```bash
python scripts/query_audit_test_exec.py --limit 20
```

#### 3. Consultar un registro específico por ID
```bash
python scripts/query_audit_test_exec.py --id 12345
```

#### 4. Ver registros de un proyecto específico
```bash
python scripts/query_audit_test_exec.py --project 4112
```

#### 5. Ver últimos 5 registros de un proyecto
```bash
python scripts/query_audit_test_exec.py --project 4112 --limit 5
```

### Ejemplos de salida

#### Listado de registros:
```
====================================================================================================
CONSULTANDO REGISTROS DE workspace.audit_test_exec
====================================================================================================

✅ Se encontraron 3 registro(s)

====================================================================================================
REGISTRO #1 - ID: 12345
====================================================================================================
📋 INFORMACIÓN GENERAL:
   - ID: 12345
   - Tenant ID: 100
   - Workspace ID: 100
   - Project ID: 4112
   - External GID: NULL

📅 PERÍODO:
   - Fecha inicio: 2025-01-01
   - Fecha fin: 2025-12-31
   - Año fiscal: 2025

💾 STORAGE:
   - Path relativo: tenants/100/workspaces/100/

📄 JOURNAL ENTRY (JE):
   - Tipo: CSV
   - Estructura: TABULAR
   - Nombre original: Libro_Diario_FLASH_BOUTIQUES_2025.csv
   - Nombre sistema: libro_diario_flash_boutiques_2025.csv
   - Extensión: csv
   - Tamaño: 3,548,576 bytes (3.38 MB)

📊 TRIAL BALANCE (TB):
   - Tipo: XLS
   - Estructura: TABULAR
   - Nombre original: Balanza_Sumas_Saldos_FLASH_BOUTIQUES_2025.xlsx
   - Nombre sistema: balanza_sumas_saldos_flash_boutiques_2025.xlsx
   - Extensión: xlsx
   - Tamaño: 1,248,576 bytes (1.19 MB)

👤 AUDITORÍA:
   - Creado el: 2025-10-27 10:30:00
   - Creado por (user_id): 1186
```

### Requisitos

- Python 3.11+
- pyodbc
- Conexión a la base de datos configurada en `db/connection.py`

### Notas

- El script usa la misma conexión que la API (`db/connection.py`)
- Todos los queries usan `autocommit=True` para evitar bloqueos
- Los tamaños de archivos se muestran en bytes y MB para facilitar la lectura
