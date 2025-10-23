# Configuración de Azure SQL Database con Managed Identity

Esta documentación explica cómo funciona la conexión a Azure SQL Database y el registro de auditoría en SmartAudit.

## Arquitectura

SmartAudit utiliza **Azure SQL Database** para registrar auditorías de las importaciones de datos. La conexión se realiza mediante **Managed Identity** en producción y **Azure CLI** en desarrollo local, eliminando la necesidad de gestionar credenciales.

### Componentes

1. **AzureSqlConnection** (`api/services/database/azure_sql_connection.py`)
   - Gestiona la conexión a Azure SQL Database
   - Detecta automáticamente el entorno (local vs Azure)
   - Soporta tres modos de conexión:
     - Managed Identity (producción en Azure)
     - Azure CLI (desarrollo local)
     - Connection String (fallback/legacy)

2. **AuditService** (`api/services/audit_service.py`)
   - Registra las importaciones en la base de datos
   - Llama al stored procedure `workspace.sp_insert_audit_test_exec_je_analysis`
   - Maneja datos de Journal Entry (Libro Diario) y Trial Balance (Sumas y Saldos)

3. **Upload Route** (`api/routes/upload.py`)
   - Integra el registro de auditoría en el flujo de upload
   - Registra automáticamente cuando se suben archivos

## Flujo de Registro de Auditoría

### 1. Upload de Journal Entry (Libro Diario)

```
Usuario → POST /smau-proto/api/import/upload
         ├─ file: archivo CSV/XLSX
         ├─ test_type: "libro_diario_import"
         ├─ project_id: ID del proyecto
         └─ period: "2024-12"

         ↓

Upload exitoso → Registro en Azure SQL
         ├─ Je data: nombre, tamaño, extensión
         ├─ TB data: NULL (aún no se ha subido)
         └─ Retorna: audit_id
```

### 2. Upload de Trial Balance (Sumas y Saldos)

```
Usuario → POST /smau-proto/api/import/upload
         ├─ file: archivo CSV/XLSX
         ├─ test_type: "sumas_saldos_import"
         ├─ project_id: ID del proyecto
         ├─ period: "2024-12"
         └─ parent_execution_id: ID del Journal Entry

         ↓

Upload exitoso → Obtiene datos del padre
         ├─ Busca execution del Journal Entry
         ├─ Combina datos de ambos archivos
         └─ Registra en Azure SQL con JE + TB
```

## Configuración

### Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
# Azure SQL Database
AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
AZURE_SQL_DATABASE=smau-dev-sqldb

# IDs de contexto
AZURE_SQL_TENANT_ID=101
AZURE_SQL_WORKSPACE_ID=101
AZURE_SQL_DEFAULT_USER_ID=1

# Habilitar auditoría
AZURE_SQL_AUDIT_ENABLED=true
```

### Desarrollo Local

#### Opción 1: Con Azure CLI (Recomendado)

```bash
# 1. Instalar Azure CLI
# https://learn.microsoft.com/cli/azure/install-azure-cli

# 2. Autenticarse
az login

# 3. Configurar variables de entorno (sin connection string)
export AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
export AZURE_SQL_DATABASE=smau-dev-sqldb
export AZURE_SQL_AUDIT_ENABLED=true

# 4. Ejecutar la aplicación
cd api
python -m uvicorn main:app --reload
```

La aplicación detectará automáticamente que estás en local y usará las credenciales de Azure CLI.

#### Opción 2: Con Connection String (Fallback)

```bash
# Configurar connection string en .env
AZURE_SQL_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=smau-dev-sql.database.windows.net;DATABASE=smau-dev-sqldb;UID=user;PWD=password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;

# Ejecutar la aplicación
cd api
python -m uvicorn main:app --reload
```

### Producción en Azure

#### 1. Configurar Managed Identity

En Azure Container Apps o Azure Functions:

```bash
# Habilitar Managed Identity (System Assigned)
az containerapp identity assign \
  --name smau-api \
  --resource-group smau-rg
```

#### 2. Configurar permisos en Azure SQL

Conectarse a Azure SQL y ejecutar:

```sql
-- Crear usuario para Managed Identity
CREATE USER [smau-api] FROM EXTERNAL PROVIDER;

-- Dar permisos de lectura/escritura
ALTER ROLE db_datareader ADD MEMBER [smau-api];
ALTER ROLE db_datawriter ADD MEMBER [smau-api];

-- Dar permisos para ejecutar stored procedures en el schema workspace
GRANT EXECUTE ON SCHEMA::workspace TO [smau-api];
```

#### 3. Configurar variables de entorno en Container App

```bash
az containerapp update \
  --name smau-api \
  --resource-group smau-rg \
  --set-env-vars \
    AZURE_SQL_SERVER=smau-dev-sql.database.windows.net \
    AZURE_SQL_DATABASE=smau-dev-sqldb \
    AZURE_SQL_TENANT_ID=101 \
    AZURE_SQL_WORKSPACE_ID=101 \
    AZURE_SQL_DEFAULT_USER_ID=1 \
    AZURE_SQL_AUDIT_ENABLED=true
```

## Stored Procedure

El stored procedure esperado en Azure SQL Database:

```sql
CREATE OR ALTER PROCEDURE [workspace].[sp_insert_audit_test_exec_je_analysis]
    @auth_user_id BIGINT,
    @tenant_id BIGINT,
    @workspace_id BIGINT,
    @project_id BIGINT,
    @external_gid UNIQUEIDENTIFIER = NULL,

    -- global parameters
    @period_beginning_date DATE,
    @period_ending_date DATE,
    @fiscal_year INT,
    @storage_relative_path NVARCHAR(1000),

    -- journal entry params
    @je_file_type_code NVARCHAR(50) = 'CSV',
    @je_file_data_structure_type_code NVARCHAR(50) = 'TABULAR',
    @je_original_file_name NVARCHAR(255),
    @je_file_name NVARCHAR(255),
    @je_file_extension VARCHAR(60) = 'csv',
    @je_file_size_bytes BIGINT,

    -- trial balance params
    @tb_file_type_code NVARCHAR(50) = 'CSV',
    @tb_file_data_structure_type_code NVARCHAR(50) = 'TABULAR',
    @tb_original_file_name NVARCHAR(255),
    @tb_file_name NVARCHAR(255),
    @tb_file_extension VARCHAR(60) = 'csv',
    @tb_file_size_bytes BIGINT,

    -- variables opcionales adicionales
    @correlation_id NVARCHAR(100) = NULL,
    @language_code NVARCHAR(10) = 'es-ES',

    -- output parameters
    @new_id BIGINT OUTPUT,
    @has_error BIT OUTPUT,
    @error_code NVARCHAR(50) OUTPUT,
    @error_message NVARCHAR(MAX) OUTPUT,
    @error_title NVARCHAR(255) OUTPUT,
    @error_severity NVARCHAR(20) OUTPUT,
    @error_category NVARCHAR(50) OUTPUT
AS
BEGIN
    -- Implementación del stored procedure
    -- Debe crear el registro de auditoría y retornar @new_id
END
```

## Pruebas

### Probar conexión

```python
from services.audit_service import get_audit_service

audit_service = get_audit_service()

# Probar conexión
if audit_service.test_connection():
    print("✓ Conexión exitosa a Azure SQL")
else:
    print("✗ Error en conexión a Azure SQL")
```

### Probar registro de auditoría

```python
from services.audit_service import get_audit_service

audit_service = get_audit_service()

# Registrar una importación de prueba
audit_id = audit_service.register_import_execution(
    project_id=101,
    period="2024-12",
    je_original_file_name="libro_diario.csv",
    je_file_name="abc123_libro_diario_Je",
    je_file_extension="csv",
    je_file_size_bytes=150000
)

if audit_id:
    print(f"✓ Auditoría registrada con ID: {audit_id}")
else:
    print("✗ Error registrando auditoría")
```

## Modo de Detección Automática

La clase `AzureSqlConnection` detecta automáticamente el entorno:

| Entorno | Detección | Método de Autenticación |
|---------|-----------|------------------------|
| Azure Container Apps | `CONTAINER_APP_NAME` presente | Managed Identity |
| Azure Functions | `WEBSITE_INSTANCE_ID` presente | Managed Identity |
| Local con Azure CLI | `az account show` funciona | Azure CLI Credential |
| Local sin Azure CLI | Connection string configurado | Connection String |

## Troubleshooting

### Error: "Error obteniendo token con Azure CLI"

**Solución:** Ejecutar `az login` para autenticarse.

### Error: "Login failed for user"

**Solución:** Verificar que la Managed Identity tenga permisos en Azure SQL.

```sql
-- Verificar permisos
SELECT
    dp.name AS UserName,
    dp.type_desc AS UserType,
    drm.role_principal_id,
    drp.name AS RoleName
FROM sys.database_principals dp
LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
LEFT JOIN sys.database_principals drp ON drm.role_principal_id = drp.principal_id
WHERE dp.name = 'smau-api';
```

### Error: "Could not find stored procedure"

**Solución:** Verificar que el stored procedure existe:

```sql
SELECT *
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_SCHEMA = 'workspace'
  AND ROUTINE_NAME = 'sp_insert_audit_test_exec_je_analysis';
```

### Error: "ODBC Driver not found"

**Solución:** Instalar ODBC Driver 18 for SQL Server.

**Ubuntu/Debian:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

**Windows:**
Descargar de: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

## Seguridad

### Mejores Prácticas

1. **Nunca** hardcodear credenciales en el código
2. **Siempre** usar Managed Identity en producción
3. **Rotar** las credenciales periódicamente si usas connection strings
4. **Limitar** los permisos de la Managed Identity al mínimo necesario
5. **Auditar** los accesos a la base de datos regularmente

### Principio de Mínimo Privilegio

La Managed Identity solo debe tener permisos para:
- Leer/escribir en las tablas de auditoría
- Ejecutar stored procedures en el schema `workspace`

```sql
-- NO dar permisos de db_owner
-- SÍ dar permisos específicos
GRANT EXECUTE ON SCHEMA::workspace TO [smau-api];
GRANT SELECT, INSERT ON workspace.audit_test_exec TO [smau-api];
```

## Logs y Monitoreo

Los logs de conexión y auditoría se escriben en el logger estándar de Python:

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Mensajes de log importantes:
- `✓ Auditoría registrada con ID: {audit_id}` - Registro exitoso
- `⚠️ Error registrando auditoría: {error}` - Error no crítico
- `Conexión a Azure SQL inicializada correctamente` - Inicialización exitosa
- `Azure SQL no configurado` - Variables de entorno faltantes

## Referencias

- [Azure SQL Database - Managed Identity](https://learn.microsoft.com/azure/azure-sql/database/authentication-aad-configure)
- [Azure Identity SDK](https://learn.microsoft.com/python/api/overview/azure/identity-readme)
- [ODBC Driver for SQL Server](https://learn.microsoft.com/sql/connect/odbc/microsoft-odbc-driver-for-sql-server)
- [Container Apps - Managed Identity](https://learn.microsoft.com/azure/container-apps/managed-identity)
