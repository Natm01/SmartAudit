# Integración Frontend - Importar Archivos

## Flujo completo de importación con ejecución automática del SP

Cuando el usuario presiona "Importar archivos", el sistema debe:
1. Subir el archivo de Journal Entry (JE)
2. Subir el archivo de Trial Balance (TB)
3. El backend ejecutará automáticamente el SP `sp_insert_audit_test_exec_je_analysis` cuando ambos archivos estén listos

## Paso 1: Obtener datos del usuario

Antes de mostrar el formulario de importación, hacer llamada a:

```typescript
const userResponse = await fetch(`${config.portalApiUrl}/api/v1/users/me`);
const userData = await userResponse.json();

// Extraer los datos necesarios:
const auth_user_id = userData.user_id;          // ID del usuario
const tenant_id = userData.tenant_id;            // ID del tenant
const workspace_id = userData.workspace_id;      // ID del workspace
// La lista de proyectos para el dropdown está en userData
```

## Paso 2: Formulario de Importación

El formulario (ImportForm) debe capturar:

```typescript
interface ImportFormData {
  // Del dropdown de proyectos
  project_id: number;

  // Fechas del período
  period_beginning_date: string;  // YYYY-MM-DD
  period_ending_date: string;     // YYYY-MM-DD
  fiscal_year: number;

  // Archivos
  je_file: File;  // Archivo de Journal Entry
  tb_file: File;  // Archivo de Trial Balance (Sumas y Saldos)

  // Opcional
  language_code?: string;  // Default: "es-ES"
}
```

## Paso 3: Enviar archivos al backend

Cuando el usuario presiona "Importar", hacer **DOS llamadas** al endpoint `/smau-proto/api/import/upload`:

### 3.1 Primera llamada - Journal Entry (JE)

```typescript
const formDataJE = new FormData();

// Archivo
formDataJE.append('file', formData.je_file);

// Tipo de test
formDataJE.append('test_type', 'libro_diario_import');

// Datos del usuario (de /api/v1/users/me)
formDataJE.append('auth_user_id', auth_user_id.toString());
formDataJE.append('tenant_id', tenant_id.toString());
formDataJE.append('workspace_id', workspace_id.toString());

// Datos del formulario
formDataJE.append('project_id', formData.project_id.toString());
formDataJE.append('period_beginning_date', formData.period_beginning_date);
formDataJE.append('period_ending_date', formData.period_ending_date);
formDataJE.append('fiscal_year', formData.fiscal_year.toString());

// Opcional
formDataJE.append('language_code', formData.language_code || 'es-ES');

// NO enviar parent_execution_id para JE

const responseJE = await fetch(`${config.apiUrl}/smau-proto/api/import/upload`, {
  method: 'POST',
  body: formDataJE
});

const resultJE = await responseJE.json();
const je_execution_id = resultJE.execution_id;  // Guardar este ID!
```

### 3.2 Segunda llamada - Trial Balance (TB)

**IMPORTANTE:** Enviar el `parent_execution_id` con el ID del JE

```typescript
const formDataTB = new FormData();

// Archivo
formDataTB.append('file', formData.tb_file);

// Tipo de test
formDataTB.append('test_type', 'sumas_saldos_import');

// Datos del usuario (de /api/v1/users/me)
formDataTB.append('auth_user_id', auth_user_id.toString());
formDataTB.append('tenant_id', tenant_id.toString());
formDataTB.append('workspace_id', workspace_id.toString());

// Datos del formulario
formDataTB.append('project_id', formData.project_id.toString());
formDataTB.append('period_beginning_date', formData.period_beginning_date);
formDataTB.append('period_ending_date', formData.period_ending_date);
formDataTB.append('fiscal_year', formData.fiscal_year.toString());

// Opcional
formDataTB.append('language_code', formData.language_code || 'es-ES');

// ⭐ IMPORTANTE: Vincular con el JE usando parent_execution_id
formDataTB.append('parent_execution_id', je_execution_id);

const responseTB = await fetch(`${config.apiUrl}/smau-proto/api/import/upload`, {
  method: 'POST',
  body: formDataTB
});

const resultTB = await responseTB.json();
```

## Paso 4: Verificar el resultado

La respuesta del segundo upload (TB) incluirá información sobre el SP:

```typescript
// Si el SP se ejecutó exitosamente:
{
  "execution_id": "abc-123-ss",
  "file_name": "balanza.xlsx",
  "message": "File uploaded successfully | audit_test_exec creado (ID: 12345)"
}

// Si hubo error en el SP:
{
  "execution_id": "abc-123-ss",
  "file_name": "balanza.xlsx",
  "message": "File uploaded successfully | SP ejecutado con error: VALIDATION_ERROR"
}

// Si aún no se ejecutó (falta el JE o está en background):
{
  "execution_id": "abc-123-ss",
  "file_name": "balanza.xlsx",
  "message": "File uploaded successfully"
}
```

## Ejemplo completo

```typescript
async function importarArchivos(formData: ImportFormData) {
  try {
    // 1. Obtener datos del usuario
    const userResponse = await fetch(`${config.portalApiUrl}/api/v1/users/me`);
    const userData = await userResponse.json();

    const auth_user_id = userData.user_id;
    const tenant_id = userData.tenant_id;
    const workspace_id = userData.workspace_id;

    // 2. Subir Journal Entry
    const formDataJE = new FormData();
    formDataJE.append('file', formData.je_file);
    formDataJE.append('test_type', 'libro_diario_import');
    formDataJE.append('auth_user_id', auth_user_id.toString());
    formDataJE.append('tenant_id', tenant_id.toString());
    formDataJE.append('workspace_id', workspace_id.toString());
    formDataJE.append('project_id', formData.project_id.toString());
    formDataJE.append('period_beginning_date', formData.period_beginning_date);
    formDataJE.append('period_ending_date', formData.period_ending_date);
    formDataJE.append('fiscal_year', formData.fiscal_year.toString());
    formDataJE.append('language_code', 'es-ES');

    const responseJE = await fetch(
      `${config.apiUrl}/smau-proto/api/import/upload`,
      { method: 'POST', body: formDataJE }
    );
    const resultJE = await responseJE.json();

    if (!responseJE.ok) {
      throw new Error(`Error subiendo JE: ${resultJE.detail}`);
    }

    const je_execution_id = resultJE.execution_id;
    console.log('✅ Journal Entry subido:', je_execution_id);

    // 3. Subir Trial Balance
    const formDataTB = new FormData();
    formDataTB.append('file', formData.tb_file);
    formDataTB.append('test_type', 'sumas_saldos_import');
    formDataTB.append('auth_user_id', auth_user_id.toString());
    formDataTB.append('tenant_id', tenant_id.toString());
    formDataTB.append('workspace_id', workspace_id.toString());
    formDataTB.append('project_id', formData.project_id.toString());
    formDataTB.append('period_beginning_date', formData.period_beginning_date);
    formDataTB.append('period_ending_date', formData.period_ending_date);
    formDataTB.append('fiscal_year', formData.fiscal_year.toString());
    formDataTB.append('language_code', 'es-ES');
    formDataTB.append('parent_execution_id', je_execution_id);  // ⭐ Vincula con JE

    const responseTB = await fetch(
      `${config.apiUrl}/smau-proto/api/import/upload`,
      { method: 'POST', body: formDataTB }
    );
    const resultTB = await responseTB.json();

    if (!responseTB.ok) {
      throw new Error(`Error subiendo TB: ${resultTB.detail}`);
    }

    console.log('✅ Trial Balance subido:', resultTB.execution_id);
    console.log('📋 Mensaje:', resultTB.message);

    // Verificar si el SP se ejecutó
    if (resultTB.message.includes('audit_test_exec creado')) {
      // Extraer el ID del mensaje
      const match = resultTB.message.match(/ID: (\d+)/);
      const audit_test_id = match ? match[1] : null;
      console.log('✅ SP ejecutado, audit_test_exec.id:', audit_test_id);
    }

    return {
      success: true,
      je_execution_id,
      tb_execution_id: resultTB.execution_id,
      message: resultTB.message
    };

  } catch (error) {
    console.error('❌ Error en importación:', error);
    throw error;
  }
}
```

## Notas importantes

1. **Orden de los uploads:** Primero JE, luego TB. Esto es importante para la coordinación.

2. **Parent execution ID:** El TB debe incluir `parent_execution_id` con el ID del JE para que el backend sepa que están relacionados.

3. **Formato de fechas:** Las fechas deben estar en formato `YYYY-MM-DD` (ej: "2025-01-01").

4. **IDs de ejecución:** El sistema genera IDs automáticos:
   - JE: ID aleatorio (ej: "abc-123")
   - TB: ID derivado del JE con sufijo "-ss" (ej: "abc-123-ss")

5. **Ejecución del SP:** El SP se ejecuta automáticamente cuando:
   - Ambos archivos están subidos completamente
   - Todos los datos necesarios están presentes
   - Los archivos no están en proceso de upload en background

6. **Logs:** El backend loggeará todo el proceso, puedes verificar en los logs si el SP se ejecutó correctamente.

## Troubleshooting

### El SP no se ejecuta

Verifica que estás enviando todos los campos requeridos:
- `auth_user_id`, `tenant_id`, `workspace_id`
- `project_id`
- `period_beginning_date`, `period_ending_date`, `fiscal_year`

### Error "TB no tiene parent_execution_id"

Asegúrate de pasar el `parent_execution_id` en el segundo upload (TB) con el `execution_id` del primer upload (JE).

### Quiero ver si el SP se ejecutó

Puedes consultar los logs del backend o usar el script de consulta:
```bash
cd api
python scripts/query_audit_test_exec.py --project 4112
```
