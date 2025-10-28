# Almacenamiento de Resultados Validados

## Descripción

Este módulo permite guardar los resultados validados de Libro Diario y Sumas y Saldos en un contenedor específico de Azure Blob Storage llamado `libro-diario-resultados`.

## Funcionalidad

### ¿Cuándo se guardan los resultados?

Los resultados **SOLO se guardan si TODAS las validaciones pasaron correctamente**:

1. **Libro Diario**: Todas las 4 fases de validación deben pasar
   - Fase 1: Validaciones de Formato
   - Fase 2: Validaciones de Identificadores
   - Fase 3: Validaciones Temporales
   - Fase 4: Validaciones de Integridad

2. **Sumas y Saldos**: La validación de formato debe pasar
   - Fase 1: Validaciones de Formato

### Estructura de Archivos

Los archivos se guardan con la siguiente estructura de carpetas:

```
libro-diario-resultados/
  └── {project_id}/
      └── {execution_id}/
          ├── sys/
          │   └── {execution_id}-sys.csv
          └── je/
              ├── {execution_id}-je-cabecera.csv
              └── {execution_id}-je-detalle.csv
```

### Archivos Generados

#### 1. Sumas y Saldos (`{execution_id}-sys.csv`)

Contiene todas las columnas definidas en `config/trial_balance_table_mapping.json`:

- `gl_account_number` (requerido)
- `period_beginning_balance`
- `period_ending_balance` (requerido)
- `business_unit`
- `cost_center`
- `department`
- `period_activity_credit`
- `period_activity_debit`
- `reporting_account`
- `user_defined_01`
- `user_defined_02`
- `user_defined_03`

#### 2. Libro Diario - Cabecera (`{execution_id}-je-cabecera.csv`)

Contiene las columnas de cabecera definidas en `config/journal_entries_table_mapping.json`:

- `journal_entry_id` (requerido)
- `posting_date` (requerido)
- `entry_date`
- `entry_time`
- `entry_type`
- `fiscal_year`
- `journal_id`
- `line_count`
- `description`
- `period_number`
- `prepared_by`
- `manual_entry`
- `recurring_entry`
- `reference_number`
- `reversal_date`
- `source`
- `total_credit_amount`
- `total_debit_amount`
- `entry_status`
- `effective_date`
- `document_number`
- `adjustment_entry`
- `approval_date`
- `approved_by`

**Nota**: El archivo de cabecera contiene un registro único por `journal_entry_id`.

#### 3. Libro Diario - Detalle (`{execution_id}-je-detalle.csv`)

Contiene las columnas de detalle definidas en `config/journal_entries_table_mapping.json`:

- `journal_entry_id` (para vincular con cabecera)
- `line_number`
- `gl_account_number` (requerido)
- `line_description`
- `debit_credit_indicator`
- `amount`
- `debit_amount`
- `credit_amount`
- `customer_id`
- `business_category`
- `business_unit`
- `cost_center`
- `department`
- `location`
- `product_id`
- `project_code`
- `reporting_account`
- `user_defined_01`
- `account_combination`
- `user_defined_02`
- `user_defined_03`
- `vendor_id`

**Nota**: El archivo de detalle contiene todas las líneas del asiento contable.

## API Endpoints

### 1. Guardar Resultados Validados

**POST** `/smau-proto/api/import/save-results/{execution_id}`

Guarda los resultados validados en el contenedor `libro-diario-resultados`.

**Request Body:**
```json
{
  "project_id": "12345"
}
```

**Response (200 OK):**
```json
{
  "execution_id": "abc-123",
  "message": "Guardado de resultados iniciado",
  "status": "processing"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "No se pueden guardar resultados: Libro Diario: Validaciones fallidas (1 fases)"
}
```

### 2. Verificar Estado de Guardado

**GET** `/smau-proto/api/import/save-results/{execution_id}/status`

Verifica si los resultados pueden ser guardados.

**Response (200 OK):**
```json
{
  "execution_id": "abc-123",
  "can_save": true,
  "validation_status": {
    "journal_entries": {
      "exists": true,
      "validated": true,
      "passed": true,
      "summary": {
        "total_phases": 4,
        "completed_phases": 4,
        "passed_phases": 4,
        "failed_phases": 0,
        "all_passed": true
      }
    },
    "trial_balance": {
      "exists": true,
      "validated": true,
      "passed": true,
      "summary": {
        "total_phases": 1,
        "completed_phases": 1,
        "passed_phases": 1,
        "failed_phases": 0,
        "all_passed": true
      }
    }
  },
  "message": "Resultados pueden ser guardados"
}
```

### 3. Obtener Archivos Guardados

**GET** `/smau-proto/api/import/save-results/{execution_id}/files`

Obtiene las rutas de los archivos guardados.

**Response (200 OK):**
```json
{
  "journal_header": "azure://libro-diario-resultados/12345/abc-123/je/abc-123-je-cabecera.csv",
  "journal_detail": "azure://libro-diario-resultados/12345/abc-123/je/abc-123-je-detalle.csv",
  "trial_balance": "azure://libro-diario-resultados/12345/abc-123/sys/abc-123-sys.csv"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "No se encontraron resultados guardados para esta ejecución"
}
```

## Flujo de Uso Completo

### 1. Upload y Procesamiento

```
1. Upload Libro Diario → execution_id = "ld-001"
2. Upload Sumas y Saldos → execution_id = "ld-001" (mismo)
3. Validación Libro Diario
4. Mapeo Libro Diario (automático)
5. Mapeo Libro Diario (manual si es necesario)
6. Validación de Reglas Contables (4 fases)
7. Mapeo Sumas y Saldos (automático)
8. Mapeo Sumas y Saldos (manual si es necesario)
9. Validación Sumas y Saldos (fase 1)
```

### 2. Verificar Estado de Validaciones

```bash
GET /smau-proto/api/import/save-results/ld-001/status
```

### 3. Guardar Resultados (si todas las validaciones pasaron)

```bash
POST /smau-proto/api/import/save-results/ld-001
Content-Type: application/json

{
  "project_id": "12345"
}
```

### 4. Verificar Archivos Guardados

```bash
GET /smau-proto/api/import/save-results/ld-001/files
```

## Manejo de Errores

### Errores Comunes

1. **Validaciones no completadas**
   ```json
   {
     "detail": "No se pueden guardar resultados: Libro Diario: No se encontraron resultados de validaciones"
   }
   ```

2. **Validaciones fallidas**
   ```json
   {
     "detail": "No se pueden guardar resultados: Libro Diario: Validaciones fallidas (2 fases)"
   }
   ```

3. **Archivos no encontrados**
   ```json
   {
     "detail": "No se pueden guardar resultados: No hay archivos procesados para guardar"
   }
   ```

## Arquitectura

### Componentes

1. **ResultsStorageService** (`services/results_storage_service.py`)
   - Verifica que todas las validaciones pasaron
   - Lee las configuraciones de columnas
   - Descarga archivos CSV de Azure
   - Filtra columnas según configuración
   - Sube archivos a contenedor de resultados

2. **ResultsStorageRouter** (`routes/results_storage.py`)
   - Endpoints HTTP para guardar resultados
   - Background tasks para procesamiento asíncrono
   - Actualización de estado en execution

### Dependencias

- **Azure Blob Storage**: Almacenamiento de archivos
- **Pandas**: Procesamiento de CSV
- **FastAPI**: Framework web
- **Configuraciones JSON**:
  - `config/journal_entries_table_mapping.json`
  - `config/trial_balance_table_mapping.json`

## Configuración

### Variables de Entorno Requeridas

```env
AZURE_STORAGE_CONNECTION_STRING=<connection_string>
```

### Contenedores de Azure Blob Storage

- `libro-diario-resultados`: Contenedor para resultados validados (se crea automáticamente)
- `mapeos`: Contenedor con archivos mapeados (fuente de datos)

## Testing

### Probar con curl

```bash
# 1. Verificar estado
curl -X GET "http://localhost:8000/smau-proto/api/import/save-results/ld-001/status"

# 2. Guardar resultados
curl -X POST "http://localhost:8000/smau-proto/api/import/save-results/ld-001" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "12345"}'

# 3. Obtener archivos guardados
curl -X GET "http://localhost:8000/smau-proto/api/import/save-results/ld-001/files"
```

### Probar con Python

```python
import requests

# Verificar estado
response = requests.get("http://localhost:8000/smau-proto/api/import/save-results/ld-001/status")
print(response.json())

# Guardar resultados
response = requests.post(
    "http://localhost:8000/smau-proto/api/import/save-results/ld-001",
    json={"project_id": "12345"}
)
print(response.json())

# Obtener archivos guardados
response = requests.get("http://localhost:8000/smau-proto/api/import/save-results/ld-001/files")
print(response.json())
```

## Logs

El servicio genera logs detallados:

```
INFO - Starting background task to save results for execution ld-001
INFO - All validations passed for execution ld-001. Starting to save results...
INFO - Processing Libro Diario files...
INFO - Read journal entries CSV with 1234 rows
INFO - Created header file with 123 rows and 24 columns
INFO - Created detail file with 1234 rows and 21 columns
INFO - Processing Sumas y Saldos file...
INFO - Uploaded to results: azure://libro-diario-resultados/12345/ld-001/je/ld-001-je-cabecera.csv
INFO - Uploaded to results: azure://libro-diario-resultados/12345/ld-001/je/ld-001-je-detalle.csv
INFO - Uploaded to results: azure://libro-diario-resultados/12345/ld-001/sys/ld-001-sys.csv
INFO - Successfully saved 3 files to results container
```

## Notas Importantes

1. **Solo columnas existentes**: El servicio solo incluye columnas que existen tanto en la configuración como en los datos reales.

2. **Limpieza de temporales**: Los archivos temporales se limpian automáticamente después del procesamiento.

3. **Sobrescritura**: Si ya existen archivos en las mismas rutas, serán sobrescritos.

4. **Procesamiento asíncrono**: El guardado se ejecuta en background, por lo que la respuesta es inmediata.

5. **Validación estricta**: No se guardan resultados parciales. O se guardan todos los archivos o ninguno.
