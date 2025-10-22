# Endpoint de Ejecución de Auditoría

## Descripción General

Este endpoint permite crear una nueva ejecución de análisis de asientos contables (Journal Entries) y ejecutar el stored procedure de Azure SQL Database para registrar todos los datos necesarios.

### 🔐 Autenticación con Azure SQL

El servicio soporta **dos métodos de autenticación**:

1. **Managed Identity** (Recomendado para Producción) ⭐
   - Sin credenciales hardcodeadas
   - Autenticación mediante Azure AD
   - Rotación automática de tokens
   - Mayor seguridad

2. **SQL Authentication** (Desarrollo Local)
   - Usuario y contraseña tradicional
   - Útil para desarrollo local
   - Requiere manejo de secretos

> **Recomendación:** Usa **Managed Identity** en todos los entornos de Azure (producción, staging, QA). Solo usa SQL Authentication para desarrollo local.

## Endpoint Principal

### POST `/smau-proto/api/audit/executions`

Crea una nueva ejecución de análisis de auditoría.

**URL Completa:**
```
POST https://devapi.grantthornton.es/smau-proto/api/audit/executions
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "tenant_id": 100,
  "workspace_id": 100,
  "project_id": 1150,
  "auth_user_id": 1186,
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "fiscal_year": 2024,
  "period_beginning_date": "2024-01-01",
  "period_ending_date": "2024-12-31",
  "journal_entry_file": {
    "original_file_name": "Libro Diario 2024.xlsx",
    "file_name": "libro_diario_2024.xlsx",
    "file_extension": "xlsx",
    "file_size_bytes": 2048576,
    "file_type_code": "XLSX",
    "file_data_structure_type_code": "TABULAR"
  },
  "trial_balance_file": {
    "original_file_name": "Sumas y Saldos 2024.xlsx",
    "file_name": "sumas_saldos_2024.xlsx",
    "file_extension": "xlsx",
    "file_size_bytes": 1024768,
    "file_type_code": "XLSX",
    "file_data_structure_type_code": "TABULAR"
  },
  "storage_relative_path": "tenants/100/workspaces/100/",
  "language_code": "es-ES",
  "correlation_id": "req-12345",
  "external_gid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response 201 (Éxito):**
```json
{
  "success": true,
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "audit_test_exec_id": 12345,
  "message": "Ejecución de auditoría creada exitosamente",
  "timestamp": "2024-10-22T10:30:45.123456Z"
}
```

**Response 200 (Error de negocio):**
```json
{
  "success": false,
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "audit_test_exec_id": null,
  "message": "Error al crear la ejecución de auditoría",
  "error_code": "VALIDATION_ERROR",
  "error_message": "El proyecto no existe o no está activo",
  "error_title": "Error de validación",
  "error_severity": "MEDIUM",
  "error_category": "BUSINESS_LOGIC",
  "timestamp": "2024-10-22T10:30:45.123456Z"
}
```

**Response 500 (Error del sistema):**
```json
{
  "detail": {
    "error_code": "CONFIG_ERROR",
    "error_message": "Variables de entorno faltantes: AZURE_SQL_SERVER, AZURE_SQL_DATABASE",
    "error_title": "Error de configuración",
    "error_category": "CONFIGURATION"
  }
}
```

---

## Campos del Request

### Identificadores de Proyecto

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| `tenant_id` | integer | Sí | ID del tenant | 100 |
| `workspace_id` | integer | Sí | ID del workspace | 100 |
| `project_id` | integer | Sí | ID del proyecto (del JSON users-me-projects) | 1150 |
| `auth_user_id` | integer | Sí | ID del usuario autenticado | 1186 |

### Información del Período Fiscal

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| `fiscal_year` | integer | Sí | Año fiscal (2000-2100) | 2024 |
| `period_beginning_date` | date | Sí | Fecha de inicio del período | "2024-01-01" |
| `period_ending_date` | date | Sí | Fecha de fin del período (debe ser posterior a la fecha de inicio) | "2024-12-31" |

### Execution ID

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|-----------|-------------|---------|
| `execution_id` | string (UUID) | No* | ID único de la ejecución. Si no se proporciona, se genera automáticamente | "550e8400-e29b-41d4-a716-446655440000" |

### Metadatos del Archivo Libro Diario (journal_entry_file)

| Campo | Tipo | Requerido | Descripción | Valores Permitidos |
|-------|------|-----------|-------------|-------------------|
| `original_file_name` | string | Sí | Nombre original del archivo subido | "Libro Diario 2024.xlsx" |
| `file_name` | string | Sí | Nombre normalizado para almacenamiento | "libro_diario_2024.xlsx" |
| `file_extension` | string | Sí | Extensión del archivo | csv, xlsx, xls, txt |
| `file_size_bytes` | integer | Sí | Tamaño del archivo en bytes (≥ 0) | 2048576 |
| `file_type_code` | string | No | Tipo de archivo (default: CSV) | CSV, XLS, XLSX, TXT |
| `file_data_structure_type_code` | string | No | Estructura de datos (default: TABULAR) | TABULAR, HEADER_AND_LINES |

### Metadatos del Archivo Sumas y Saldos (trial_balance_file)

Los mismos campos que `journal_entry_file` pero para el archivo de Sumas y Saldos.

### Parámetros Opcionales

| Campo | Tipo | Requerido | Descripción | Default |
|-------|------|-----------|-------------|---------|
| `storage_relative_path` | string | No | Ruta relativa en Azure Storage. Si no se proporciona, se genera automáticamente | "tenants/{tenant_id}/workspaces/{workspace_id}/" |
| `language_code` | string | No | Código de idioma | "es-ES" |
| `correlation_id` | string | No | ID de correlación para logs | null |
| `external_gid` | string | No | GUID externo para tracking | null |

---

## Endpoints Adicionales

### GET `/smau-proto/api/audit/executions/{execution_id}`

Obtiene información de una ejecución específica.

**Nota:** Este endpoint está en desarrollo. Actualmente retorna un placeholder.

### GET `/smau-proto/api/audit/test-connection`

Prueba la conexión a Azure SQL Database.

**Response 200 (Éxito):**
```json
{
  "success": true,
  "message": "Conexión exitosa a Azure SQL Database",
  "database": "smau-dev-sqldb",
  "timestamp": "2024-10-22T10:30:45.123456Z"
}
```

**Response 503 (Error de conexión):**
```json
{
  "success": false,
  "message": "Error al conectar: [ODBC Driver error message]",
  "timestamp": "2024-10-22T10:30:45.123456Z"
}
```

---

## Integración con el Front-End

### Flujo Completo

1. **Usuario selecciona proyecto** del dropdown (datos vienen del JSON `users-me-projects.json`)
2. **Usuario sube archivos** (Libro Diario y Sumas y Saldos)
3. **Front-end recopila metadatos** de los archivos:
   - Nombre original
   - Nombre normalizado
   - Extensión
   - Tamaño en bytes
4. **Front-end genera execution_id** (UUID v4)
5. **Front-end envía POST request** al endpoint `/smau-proto/api/audit/executions`
6. **Backend valida datos** y ejecuta stored procedure
7. **Backend retorna respuesta** con éxito o errores
8. **Front-end muestra resultado** al usuario

### Ejemplo de Código JavaScript

```javascript
// 1. Obtener datos del proyecto seleccionado
const selectedProject = projectsData.find(p => p.project_id === selectedProjectId);

// 2. Generar execution ID
const executionId = crypto.randomUUID();

// 3. Obtener metadatos de archivos
const journalEntryFile = {
  original_file_name: jeFile.name,
  file_name: normalizeFileName(jeFile.name),
  file_extension: getFileExtension(jeFile.name),
  file_size_bytes: jeFile.size,
  file_type_code: getFileTypeCode(jeFile.name),
  file_data_structure_type_code: "TABULAR"
};

const trialBalanceFile = {
  original_file_name: tbFile.name,
  file_name: normalizeFileName(tbFile.name),
  file_extension: getFileExtension(tbFile.name),
  file_size_bytes: tbFile.size,
  file_type_code: getFileTypeCode(tbFile.name),
  file_data_structure_type_code: "TABULAR"
};

// 4. Preparar request body
const requestBody = {
  tenant_id: selectedProject.tenant_id,
  workspace_id: selectedProject.workspace_id,
  project_id: selectedProject.project_id,
  auth_user_id: currentUser.user_id,
  execution_id: executionId,
  fiscal_year: parseInt(fiscalYear),
  period_beginning_date: periodStartDate, // "YYYY-MM-DD"
  period_ending_date: periodEndDate,      // "YYYY-MM-DD"
  journal_entry_file: journalEntryFile,
  trial_balance_file: trialBalanceFile,
  language_code: "es-ES"
};

// 5. Enviar request
const response = await fetch(
  'https://devapi.grantthornton.es/smau-proto/api/audit/executions',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  }
);

// 6. Procesar respuesta
const result = await response.json();

if (response.ok && result.success) {
  console.log('Ejecución creada:', result.audit_test_exec_id);
  // Redirigir o mostrar mensaje de éxito
} else {
  console.error('Error:', result.error_message);
  // Mostrar error al usuario
}
```

### Funciones Helper

```javascript
function normalizeFileName(fileName) {
  return fileName
    .toLowerCase()
    .replace(/\s+/g, '_')
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function getFileExtension(fileName) {
  return fileName.split('.').pop().toLowerCase();
}

function getFileTypeCode(fileName) {
  const ext = getFileExtension(fileName);
  const mapping = {
    'csv': 'CSV',
    'xlsx': 'XLSX',
    'xls': 'XLS',
    'txt': 'TXT'
  };
  return mapping[ext] || 'CSV';
}
```

---

## Configuración del Entorno

### Variables de Entorno Requeridas

El servicio soporta **dos métodos de autenticación** con Azure SQL:

#### OPCIÓN 1: Managed Identity (Recomendado para Producción en Azure)

**Ventajas:**
- ✅ Sin credenciales en código o configuración
- ✅ Rotación automática de tokens de acceso
- ✅ Integración nativa con Azure AD
- ✅ Más seguro y recomendado por Microsoft
- ✅ Funciona en Azure Container Apps, Azure VM, Azure Functions, etc.

**Configuración en `.env`:**
```bash
# Método de autenticación
AZURE_SQL_AUTH_METHOD=managed_identity

# Azure SQL
AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
AZURE_SQL_DATABASE=smau-dev-sqldb

# Opcional: Client ID de Managed Identity (si usas User-assigned)
# AZURE_MANAGED_IDENTITY_CLIENT_ID=your-client-id

# General
ENVIRONMENT=production
PORT=8001
```

**Pasos para configurar Managed Identity:**

1. **Habilitar Managed Identity en Azure Container Apps:**
   - Azure Portal → Tu Container App → Identity
   - System assigned → Status: **On**
   - Copia el **Object (principal) ID**

2. **Dar permisos en Azure SQL Database:**
   ```sql
   -- Conéctate como admin a Azure SQL
   -- Reemplaza [nombre-container-app] con el nombre de tu Container App

   CREATE USER [nombre-container-app] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [nombre-container-app];
   ALTER ROLE db_datawriter ADD MEMBER [nombre-container-app];
   GRANT EXECUTE ON SCHEMA::workspace TO [nombre-container-app];
   ```

3. **Configurar variables de entorno en Azure Container Apps:**
   - Azure Portal → Tu Container App → Configuration → Environment variables
   - Agrega:
     - `AZURE_SQL_AUTH_METHOD` = `managed_identity`
     - `AZURE_SQL_SERVER` = `tu-servidor.database.windows.net`
     - `AZURE_SQL_DATABASE` = `tu-database`
   - **NO agregues** `AZURE_SQL_USERNAME` ni `AZURE_SQL_PASSWORD`

4. **Probar la conexión:**
   ```bash
   curl -X GET https://tu-api.azurecontainerapps.io/smau-proto/api/audit/test-connection
   ```

---

#### OPCIÓN 2: SQL Authentication (Para Desarrollo Local)

**Usar solo para desarrollo local o cuando Managed Identity no esté disponible.**

**Configuración en `.env`:**
```bash
# Método de autenticación
AZURE_SQL_AUTH_METHOD=sql_auth

# Azure SQL
AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
AZURE_SQL_DATABASE=smau-dev-sqldb
AZURE_SQL_USERNAME=tu_usuario
AZURE_SQL_PASSWORD=tu_password

# General
ENVIRONMENT=development
PORT=8001
```

**Pasos para desarrollo local:**

1. **Configurar firewall en Azure SQL:**
   - Azure Portal → SQL Server → Networking
   - Add your client IPv4 address

2. **Dar permisos al usuario:**
   ```sql
   GRANT EXECUTE ON SCHEMA::workspace TO [tu_usuario];
   ```

---

#### Desarrollo Local con Managed Identity (Opcional)

Puedes probar Managed Identity localmente usando Azure CLI:

1. **Instalar Azure CLI:**
   ```bash
   # Windows: https://aka.ms/installazurecliwindows
   # macOS: brew install azure-cli
   # Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login:**
   ```bash
   az login
   ```

3. **Configurar `.env`:**
   ```bash
   AZURE_SQL_AUTH_METHOD=managed_identity
   AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
   AZURE_SQL_DATABASE=smau-dev-sqldb
   ```

4. **Dar permisos a tu usuario Azure AD en SQL:**
   ```sql
   CREATE USER [tu-email@dominio.com] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [tu-email@dominio.com];
   ALTER ROLE db_datawriter ADD MEMBER [tu-email@dominio.com];
   GRANT EXECUTE ON SCHEMA::workspace TO [tu-email@dominio.com];
   ```

`DefaultAzureCredential` usará automáticamente tus credenciales de Azure CLI.

---

Ver el archivo `.env.example` para más detalles y ejemplos.

### Instalación de Dependencias

#### Python
```bash
pip install -r requirements.txt
```

#### ODBC Driver (Linux/Ubuntu)
```bash
# Instalar ODBC Driver 18 for SQL Server
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

#### ODBC Driver (macOS)
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

#### ODBC Driver (Windows)
Descargar e instalar desde:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

---

## Stored Procedure Ejecutado

El endpoint ejecuta el siguiente stored procedure:

```sql
workspace.sp_insert_audit_test_exec_je_analysis
```

**Parámetros de entrada:**
- `@auth_user_id` - ID del usuario
- `@tenant_id` - ID del tenant
- `@workspace_id` - ID del workspace
- `@project_id` - ID del proyecto
- `@external_gid` - GUID externo (opcional)
- `@period_beginning_date` - Fecha inicio
- `@period_ending_date` - Fecha fin
- `@fiscal_year` - Año fiscal
- `@storage_relative_path` - Ruta de almacenamiento
- `@je_*` - Parámetros del archivo Journal Entry
- `@tb_*` - Parámetros del archivo Trial Balance
- `@correlation_id` - ID de correlación (opcional)
- `@language_code` - Código de idioma

**Parámetros de salida:**
- `@new_id` - ID de la ejecución creada en la BD
- `@has_error` - Flag de error
- `@error_code` - Código de error
- `@error_message` - Mensaje de error
- `@error_title` - Título del error
- `@error_severity` - Severidad del error
- `@error_category` - Categoría del error

---

## Testing

### Probar conexión a Azure SQL

```bash
curl -X GET https://devapi.grantthornton.es/smau-proto/api/audit/test-connection
```

### Crear una ejecución de prueba

```bash
curl -X POST https://devapi.grantthornton.es/smau-proto/api/audit/executions \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 100,
    "workspace_id": 100,
    "project_id": 1150,
    "auth_user_id": 1186,
    "fiscal_year": 2024,
    "period_beginning_date": "2024-01-01",
    "period_ending_date": "2024-12-31",
    "journal_entry_file": {
      "original_file_name": "test.xlsx",
      "file_name": "test.xlsx",
      "file_extension": "xlsx",
      "file_size_bytes": 1024
    },
    "trial_balance_file": {
      "original_file_name": "test2.xlsx",
      "file_name": "test2.xlsx",
      "file_extension": "xlsx",
      "file_size_bytes": 1024
    }
  }'
```

---

## Documentación Interactiva

Una vez que la API esté ejecutándose, puedes acceder a la documentación interactiva en:

- **Swagger UI:** https://devapi.grantthornton.es/smau-proto/docs
- **ReDoc:** https://devapi.grantthornton.es/smau-proto/redoc

---

## Solución de Problemas

### Error: "Variables de entorno faltantes: AZURE_SQL_SERVER, AZURE_SQL_DATABASE"

**Causa:** Variables básicas de Azure SQL no configuradas.

**Solución:**
1. Verifica que el archivo `.env` existe en el directorio `api/`
2. Verifica que `AZURE_SQL_SERVER` y `AZURE_SQL_DATABASE` están configuradas
3. Reinicia la aplicación

### Error: "Para SQL Authentication se requieren: AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD"

**Causa:** Configuraste `AZURE_SQL_AUTH_METHOD=sql_auth` pero falta usuario/contraseña.

**Solución:**
1. Agrega `AZURE_SQL_USERNAME` y `AZURE_SQL_PASSWORD` al `.env`
2. O cambia a Managed Identity: `AZURE_SQL_AUTH_METHOD=managed_identity`

### Error: "No se pudo conectar a Azure SQL Database"

**Causa:** Problemas de conectividad con Azure SQL.

**Soluciones:**

**Para Managed Identity:**
1. Verifica que Managed Identity está habilitada en Container Apps
2. Verifica que el usuario de Managed Identity existe en Azure SQL:
   ```sql
   SELECT name, type_desc, authentication_type_desc
   FROM sys.database_principals
   WHERE name = '[nombre-container-app]';
   ```
3. Verifica los permisos:
   ```sql
   SELECT p.name as user_name, r.name as role_name
   FROM sys.database_role_members rm
   JOIN sys.database_principals p ON rm.member_principal_id = p.principal_id
   JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
   WHERE p.name = '[nombre-container-app]';
   ```
4. Verifica que Azure AD admin está configurado en SQL Server

**Para SQL Authentication:**
1. Verifica que el servidor y credenciales son correctos
2. Verifica las reglas de firewall en Azure Portal
3. Verifica que el usuario tiene los permisos correctos
4. Prueba la conexión con el endpoint `/test-connection`

**General:**
1. Verifica que el ODBC Driver está instalado
2. Verifica la conectividad de red
3. Revisa los logs de la aplicación para más detalles

### Error: "ODBC Driver not found"

**Causa:** El driver ODBC no está instalado.

**Solución:** Instala el ODBC Driver 18 for SQL Server (ver sección de instalación)

### Error: "No se pudo obtener access token de Managed Identity"

**Causa:** La Managed Identity no está funcionando correctamente.

**Soluciones:**
1. **En Azure Container Apps:**
   - Verifica que System-assigned identity está habilitada
   - Reinicia el Container App después de habilitar la identity
   - Espera 1-2 minutos para que la identity se propague

2. **En desarrollo local con Azure CLI:**
   - Ejecuta `az login` nuevamente
   - Verifica que estás logueado: `az account show`
   - Verifica que tienes permisos en la suscripción

3. **Si usas User-assigned Managed Identity:**
   - Verifica que `AZURE_MANAGED_IDENTITY_CLIENT_ID` está configurado correctamente
   - Verifica que la identity está asignada a tu Container App

4. **Logs detallados:**
   - Revisa los logs de la aplicación: `LOG_LEVEL=DEBUG`
   - Busca mensajes específicos sobre el error del token

---

## Soporte

Para reportar problemas o solicitar ayuda:
- Crear un issue en el repositorio
- Contactar al equipo de desarrollo
