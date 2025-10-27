# Audit Test Execution - Documentación y Ejemplos

## Descripción

Este endpoint permite crear una nueva ejecución de prueba de auditoría ejecutando el procedimiento almacenado `sp_insert_audit_test_exec_je_analysis`.

## Endpoint

```
POST /smau-proto/api/audit-test/exec
```

## Request Body

### Modelo: AuditTestExecRequest

```json
{
  "auth_user_id": 123,
  "tenant_id": 456,
  "workspace_id": 789,
  "project_id": 101112,

  "period_beginning_date": "2024-01-01",
  "period_ending_date": "2024-12-31",
  "fiscal_year": 2024,

  "je_original_file_name": "Libro_Diario_2024.csv",
  "je_file_name": "libro_diario_2024.csv",
  "je_file_size_bytes": 1048576,
  "je_file_type_code": "CSV",
  "je_file_data_structure_type_code": "TABULAR",
  "je_file_extension": "csv",

  "tb_original_file_name": "Balanza_Sumas_Saldos_2024.xlsx",
  "tb_file_name": "balanza_sumas_saldos_2024.xlsx",
  "tb_file_size_bytes": 524288,
  "tb_file_type_code": "XLS",
  "tb_file_data_structure_type_code": "TABULAR",
  "tb_file_extension": "xlsx",

  "external_gid": null,
  "correlation_id": "correlation-123-abc",
  "language_code": "es-ES"
}
```

## Response Body

### Modelo: AuditTestExecResponse

#### Éxito

```json
{
  "new_id": 987654,
  "has_error": false,
  "error_code": null,
  "error_message": null,
  "error_title": null,
  "error_severity": null,
  "error_category": null
}
```

#### Error de Negocio

```json
{
  "new_id": null,
  "has_error": true,
  "error_code": "VALIDATION_ERROR",
  "error_message": "El período fiscal no es válido",
  "error_title": "Error de Validación",
  "error_severity": "MEDIUM",
  "error_category": "VALIDATION"
}
```

## Parámetros de Entrada

### Parámetros de Usuario y Contexto

| Campo | Tipo | Obligatorio | Descripción | Origen |
|-------|------|-------------|-------------|--------|
| `auth_user_id` | int | Sí | ID del usuario autenticado | `/api/v1/users/me` |
| `tenant_id` | int | Sí | ID del tenant | `/api/v1/users/me` |
| `workspace_id` | int | Sí | ID del workspace | `/api/v1/users/me` |
| `project_id` | int | Sí | ID del proyecto | `/api/v1/users/me` |

### Parámetros Globales

| Campo | Tipo | Obligatorio | Descripción | Origen |
|-------|------|-------------|-------------|--------|
| `period_beginning_date` | string (YYYY-MM-DD) | Sí | Fecha de inicio del período | Frontend |
| `period_ending_date` | string (YYYY-MM-DD) | Sí | Fecha de fin del período | Frontend |
| `fiscal_year` | int | Sí | Año fiscal | Frontend |

### Parámetros de Journal Entry

| Campo | Tipo | Obligatorio | Descripción | Origen |
|-------|------|-------------|-------------|--------|
| `je_original_file_name` | string | Sí | Nombre original del archivo | Metadatos del archivo |
| `je_file_name` | string | Sí | Nombre normalizado del archivo | Metadatos del archivo |
| `je_file_size_bytes` | int | Sí | Tamaño del archivo en bytes | Metadatos del archivo |
| `je_file_type_code` | string | No | Tipo de archivo (CSV, XLS) | Metadatos del archivo (default: CSV) |
| `je_file_data_structure_type_code` | string | No | Estructura de datos (TABULAR, HEADER_AND_LINES) | Metadatos del archivo (default: TABULAR) |
| `je_file_extension` | string | No | Extensión del archivo | Metadatos del archivo (default: csv) |

### Parámetros de Trial Balance

| Campo | Tipo | Obligatorio | Descripción | Origen |
|-------|------|-------------|-------------|--------|
| `tb_original_file_name` | string | Sí | Nombre original del archivo | Metadatos del archivo |
| `tb_file_name` | string | Sí | Nombre normalizado del archivo | Metadatos del archivo |
| `tb_file_size_bytes` | int | Sí | Tamaño del archivo en bytes | Metadatos del archivo |
| `tb_file_type_code` | string | No | Tipo de archivo (CSV, XLS) | Metadatos del archivo (default: CSV) |
| `tb_file_data_structure_type_code` | string | No | Estructura de datos (TABULAR, HEADER_AND_LINES) | Metadatos del archivo (default: TABULAR) |
| `tb_file_extension` | string | No | Extensión del archivo | Metadatos del archivo (default: csv) |

### Parámetros Opcionales

| Campo | Tipo | Obligatorio | Descripción | Origen |
|-------|------|-------------|-------------|--------|
| `external_gid` | string (UUID) | No | GUID externo | Por ahora NULL |
| `correlation_id` | string | No | ID de correlación para trazabilidad | Sistema |
| `language_code` | string | No | Código de idioma (default: es-ES) | Validación previa |

## Parámetros de Salida

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `new_id` | int | ID del registro creado en `workspace.audit_test_exec` |
| `has_error` | boolean | Indica si hubo algún error |
| `error_code` | string | Código del error (si aplica) |
| `error_message` | string | Mensaje descriptivo del error (si aplica) |
| `error_title` | string | Título del error (si aplica) |
| `error_severity` | string | Severidad del error: LOW, MEDIUM, HIGH (si aplica) |
| `error_category` | string | Categoría del error: VALIDATION, DATABASE, SYSTEM (si aplica) |

## Ejemplo de Uso con Python

```python
import requests
import json

# URL del endpoint
url = "https://api.grantthornton.es/smau-proto/api/audit-test/exec"

# Datos de ejemplo
payload = {
    "auth_user_id": 123,
    "tenant_id": 456,
    "workspace_id": 789,
    "project_id": 101112,

    "period_beginning_date": "2024-01-01",
    "period_ending_date": "2024-12-31",
    "fiscal_year": 2024,

    "je_original_file_name": "Libro_Diario_2024.csv",
    "je_file_name": "libro_diario_2024.csv",
    "je_file_size_bytes": 1048576,
    "je_file_type_code": "CSV",
    "je_file_data_structure_type_code": "TABULAR",
    "je_file_extension": "csv",

    "tb_original_file_name": "Balanza_Sumas_Saldos_2024.xlsx",
    "tb_file_name": "balanza_sumas_saldos_2024.xlsx",
    "tb_file_size_bytes": 524288,
    "tb_file_type_code": "XLS",
    "tb_file_data_structure_type_code": "TABULAR",
    "tb_file_extension": "xlsx",

    "correlation_id": "correlation-123-abc",
    "language_code": "es-ES"
}

# Headers
headers = {
    "Content-Type": "application/json"
}

# Realizar la petición
response = requests.post(url, json=payload, headers=headers)

# Procesar la respuesta
if response.status_code == 200:
    result = response.json()
    if result["has_error"]:
        print(f"Error: {result['error_code']} - {result['error_message']}")
    else:
        print(f"Audit test execution creado exitosamente. ID: {result['new_id']}")
else:
    print(f"Error HTTP: {response.status_code}")
    print(response.text)
```

## Ejemplo de Uso con JavaScript/TypeScript

```typescript
const createAuditTestExecution = async () => {
  const url = "https://api.grantthornton.es/smau-proto/api/audit-test/exec";

  const payload = {
    auth_user_id: 123,
    tenant_id: 456,
    workspace_id: 789,
    project_id: 101112,

    period_beginning_date: "2024-01-01",
    period_ending_date: "2024-12-31",
    fiscal_year: 2024,

    je_original_file_name: "Libro_Diario_2024.csv",
    je_file_name: "libro_diario_2024.csv",
    je_file_size_bytes: 1048576,
    je_file_type_code: "CSV",
    je_file_data_structure_type_code: "TABULAR",
    je_file_extension: "csv",

    tb_original_file_name: "Balanza_Sumas_Saldos_2024.xlsx",
    tb_file_name: "balanza_sumas_saldos_2024.xlsx",
    tb_file_size_bytes: 524288,
    tb_file_type_code: "XLS",
    tb_file_data_structure_type_code: "TABULAR",
    tb_file_extension: "xlsx",

    correlation_id: "correlation-123-abc",
    language_code: "es-ES"
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (result.has_error) {
      console.error(`Error: ${result.error_code} - ${result.error_message}`);
    } else {
      console.log(`Audit test execution creado exitosamente. ID: ${result.new_id}`);
    }
  } catch (error) {
    console.error("Error al crear audit test execution:", error);
  }
};
```

## Flujo de Integración

1. **Obtener datos del usuario** desde `/api/v1/users/me`:
   - `auth_user_id`
   - `tenant_id`
   - `workspace_id`
   - `project_id`

2. **Recopilar datos del formulario** (Frontend):
   - `period_beginning_date`
   - `period_ending_date`
   - `fiscal_year`

3. **Extraer metadatos de los archivos cargados**:
   - Journal Entry: nombre original, nombre normalizado, tamaño, tipo, extensión
   - Trial Balance: nombre original, nombre normalizado, tamaño, tipo, extensión

4. **Ejecutar la petición** POST a `/smau-proto/api/audit-test/exec`

5. **Procesar la respuesta**:
   - Si `has_error` es `false`: Guardar el `new_id` para futuras referencias
   - Si `has_error` es `true`: Mostrar el error al usuario

## Notas Importantes

- El parámetro `storage_relative_path` se construye automáticamente con el formato: `tenants/{tenant_id}/workspaces/{workspace_id}/`
- Las fechas deben estar en formato ISO 8601: `YYYY-MM-DD`
- La fecha de inicio debe ser anterior a la fecha de fin
- Los valores de `file_type_code` pueden ser: `CSV`, `XLS`, `XLSX`
- Los valores de `file_data_structure_type_code` pueden ser: `TABULAR`, `HEADER_AND_LINES`

## Códigos de Error Comunes

| Código | Descripción | Severidad | Categoría |
|--------|-------------|-----------|-----------|
| `VALIDATION_ERROR` | Error de validación de datos | MEDIUM | VALIDATION |
| `DB_ERROR` | Error de base de datos | HIGH | DATABASE |
| `UNEXPECTED_ERROR` | Error inesperado del sistema | HIGH | SYSTEM |

## Health Check

Para verificar que el servicio está activo:

```
GET /smau-proto/api/audit-test/health
```

Respuesta:
```json
{
  "status": "healthy",
  "service": "audit-test",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```
