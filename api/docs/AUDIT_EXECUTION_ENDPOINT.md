# Endpoint de Ejecución de Auditoría

## Descripción General

Este endpoint permite crear una nueva ejecución de análisis de asientos contables (Journal Entries) y ejecutar el stored procedure de Azure SQL Database para registrar todos los datos necesarios.

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

Crea un archivo `.env` en el directorio `api/` con las siguientes variables:

```bash
# Azure SQL Database
AZURE_SQL_SERVER=smau-dev-sql.database.windows.net
AZURE_SQL_DATABASE=smau-dev-sqldb
AZURE_SQL_USERNAME=tu_usuario
AZURE_SQL_PASSWORD=tu_password
AZURE_SQL_DRIVER=ODBC Driver 18 for SQL Server

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# General
ENVIRONMENT=development
PORT=8001
LOG_LEVEL=INFO
```

Ver el archivo `.env.example` para más detalles.

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

### Error: "Variables de entorno faltantes"

**Causa:** Las variables de entorno de Azure SQL no están configuradas.

**Solución:**
1. Verifica que el archivo `.env` existe en el directorio `api/`
2. Verifica que todas las variables requeridas están configuradas
3. Reinicia la aplicación

### Error: "No se pudo conectar a Azure SQL Database"

**Causa:** Problemas de conectividad con Azure SQL.

**Soluciones:**
1. Verifica que el servidor y credenciales son correctos
2. Verifica las reglas de firewall en Azure Portal
3. Verifica que el ODBC Driver está instalado
4. Prueba la conexión con el endpoint `/test-connection`

### Error: "ODBC Driver not found"

**Causa:** El driver ODBC no está instalado.

**Solución:** Instala el ODBC Driver 18 for SQL Server (ver sección de instalación)

---

## Soporte

Para reportar problemas o solicitar ayuda:
- Crear un issue en el repositorio
- Contactar al equipo de desarrollo
