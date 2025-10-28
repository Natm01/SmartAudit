// src/services/importService.js - COMPLETO Y CORREGIDO
import api from './api';

/**
 * ImportService - Servicio completo con Libro Diario y Sumas y Saldos
 */
class ImportService {
  constructor() {
    this.requestCache = new Map();
    this.activePolling = new Set();
    this.activePolling = new Set();
  }

  // ===========================================
  // SUBIDA DE ARCHIVOS
  // ===========================================

  async uploadLibroDiarioYSumas(
    libroDiarioFiles,
    sumasSaldosFile,
    projectId,
    period,
    additionalParams = {}  // Nuevo: parámetros adicionales del usuario
  ) {
    try {
      if (!libroDiarioFiles || libroDiarioFiles.length === 0) {
        return { success: false, error: 'Debe adjuntar al menos un archivo de Libro Diario' };
      }

      const testType = 'libro_diario_import';

      const primaryResult = await this._uploadPrimaryLibroDiario(
        libroDiarioFiles[0],
        projectId,
        period,
        testType,
        additionalParams  // Pasar parámetros adicionales
      );
      if (!primaryResult.success) return primaryResult;

      const executionIdLD = primaryResult.executionId;

      const additionalResults = await this._uploadAdditionalLibroDiarioFiles(
        libroDiarioFiles.slice(1),
        executionIdLD,
        projectId,
        period,
        testType,
        additionalParams  // Pasar parámetros adicionales
      );

      let sumasResult = null;
      if (sumasSaldosFile) {
        sumasResult = await this._uploadSumasSaldos(
          sumasSaldosFile,
          executionIdLD,
          projectId,
          period,
          additionalParams  // Pasar parámetros adicionales
        );
      }

      return {
        success: true,
        executionId: executionIdLD,
        executionIdSS: sumasResult?.executionId || null,
        primaryFile: primaryResult.data,
        additionalFiles: additionalResults,
        sumasUpload: sumasResult,
        summary: {
          libroDiarioFiles: libroDiarioFiles.length,
          sumasSaldosFile: sumasSaldosFile ? 1 : 0,
          totalFiles: libroDiarioFiles.length + (sumasSaldosFile ? 1 : 0)
        }
      };
    } catch (err) {
      return { success: false, error: err.message || 'Error en la subida de archivos' };
    }
  }

  async _uploadPrimaryLibroDiario(file, projectId, period, testType, additionalParams = {}) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', projectId);
      formData.append('period', period);
      formData.append('test_type', testType);

      // Agregar parámetros adicionales para el SP
      if (additionalParams.auth_user_id) {
        formData.append('auth_user_id', additionalParams.auth_user_id.toString());
      }
      if (additionalParams.tenant_id) {
        formData.append('tenant_id', additionalParams.tenant_id.toString());
      }
      if (additionalParams.workspace_id) {
        formData.append('workspace_id', additionalParams.workspace_id.toString());
      }
      if (additionalParams.fiscal_year) {
        formData.append('fiscal_year', additionalParams.fiscal_year.toString());
      }
      if (additionalParams.period_beginning_date) {
        formData.append('period_beginning_date', additionalParams.period_beginning_date);
      }
      if (additionalParams.period_ending_date) {
        formData.append('period_ending_date', additionalParams.period_ending_date);
      }
      if (additionalParams.language_code) {
        formData.append('language_code', additionalParams.language_code);
      }

      const response = await api.post('/api/import/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Si el backend devuelve sp_params, mostrarlos en consola
      if (response?.data?.sp_params) {
        console.log('================================================================================');
        console.log('📋 PARÁMETROS PARA EL SP sp_insert_audit_test_exec_je_analysis:');
        console.log('================================================================================');
        console.log('👤 Usuario y Contexto:', response.data.sp_params.usuario_y_contexto);
        console.log('📅 Período:', response.data.sp_params.periodo);
        console.log('💾 Storage:', response.data.sp_params.storage);

        // Mostrar datos del archivo subido ahora o datos completos si el SP se ejecutó
        if (response.data.sp_params.archivo_subido_ahora) {
          console.log('📄 Archivo subido ahora:', response.data.sp_params.archivo_subido_ahora);
          console.log('⏳ Estado:', response.data.sp_params.estado);
        }

        if (response.data.sp_params.journal_entry) {
          console.log('📄 Journal Entry (JE):', response.data.sp_params.journal_entry);
        }

        if (response.data.sp_params.trial_balance) {
          console.log('📊 Trial Balance (TB):', response.data.sp_params.trial_balance);
        }

        console.log('🔧 Opcionales:', response.data.sp_params.opcionales);

        if (response.data.sp_params.resultado_sp) {
          console.log('✅ Resultado del SP:', response.data.sp_params.resultado_sp);
        }

        console.log('================================================================================');
      }

      return {
        success: true,
        executionId: response?.data?.execution_id,
        data: response?.data
      };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al subir archivo principal'
      };
    }
  }

  async _uploadAdditionalLibroDiarioFiles(files, parentExecutionId, projectId, period, testType, additionalParams = {}) {
    const results = [];
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);
        formData.append('period', period);
        formData.append('test_type', testType);
        formData.append('parent_execution_id', parentExecutionId);

        // Agregar parámetros adicionales para el SP
        if (additionalParams.auth_user_id) {
          formData.append('auth_user_id', additionalParams.auth_user_id.toString());
        }
        if (additionalParams.tenant_id) {
          formData.append('tenant_id', additionalParams.tenant_id.toString());
        }
        if (additionalParams.workspace_id) {
          formData.append('workspace_id', additionalParams.workspace_id.toString());
        }
        if (additionalParams.fiscal_year) {
          formData.append('fiscal_year', additionalParams.fiscal_year.toString());
        }
        if (additionalParams.period_beginning_date) {
          formData.append('period_beginning_date', additionalParams.period_beginning_date);
        }
        if (additionalParams.period_ending_date) {
          formData.append('period_ending_date', additionalParams.period_ending_date);
        }
        if (additionalParams.language_code) {
          formData.append('language_code', additionalParams.language_code);
        }

        const response = await api.post('/api/import/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        results.push({ success: true, data: response?.data });
      } catch (error) {
        results.push({
          success: false,
          error: error?.response?.data?.detail || error?.message
        });
      }
    }
    return results;
  }

  async _uploadSumasSaldos(file, parentExecutionId, projectId, period, additionalParams = {}) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', projectId);
      formData.append('period', period);
      formData.append('test_type', 'sumas_saldos');
      formData.append('parent_execution_id', parentExecutionId);

      // Agregar parámetros adicionales para el SP
      if (additionalParams.auth_user_id) {
        formData.append('auth_user_id', additionalParams.auth_user_id.toString());
      }
      if (additionalParams.tenant_id) {
        formData.append('tenant_id', additionalParams.tenant_id.toString());
      }
      if (additionalParams.workspace_id) {
        formData.append('workspace_id', additionalParams.workspace_id.toString());
      }
      if (additionalParams.fiscal_year) {
        formData.append('fiscal_year', additionalParams.fiscal_year.toString());
      }
      if (additionalParams.period_beginning_date) {
        formData.append('period_beginning_date', additionalParams.period_beginning_date);
      }
      if (additionalParams.period_ending_date) {
        formData.append('period_ending_date', additionalParams.period_ending_date);
      }
      if (additionalParams.language_code) {
        formData.append('language_code', additionalParams.language_code);
      }

      const response = await api.post('/api/import/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Si el backend devuelve sp_params, mostrarlos en consola
      if (response?.data?.sp_params) {
        console.log('================================================================================');
        console.log('📋 PARÁMETROS PARA EL SP sp_insert_audit_test_exec_je_analysis:');
        console.log('================================================================================');
        console.log('👤 Usuario y Contexto:', response.data.sp_params.usuario_y_contexto);
        console.log('📅 Período:', response.data.sp_params.periodo);
        console.log('💾 Storage:', response.data.sp_params.storage);

        // Mostrar datos del archivo subido ahora o datos completos si el SP se ejecutó
        if (response.data.sp_params.archivo_subido_ahora) {
          console.log('📄 Archivo subido ahora:', response.data.sp_params.archivo_subido_ahora);
          console.log('⏳ Estado:', response.data.sp_params.estado);
        }

        if (response.data.sp_params.journal_entry) {
          console.log('📄 Journal Entry (JE):', response.data.sp_params.journal_entry);
        }

        if (response.data.sp_params.trial_balance) {
          console.log('📊 Trial Balance (TB):', response.data.sp_params.trial_balance);
        }

        console.log('🔧 Opcionales:', response.data.sp_params.opcionales);

        if (response.data.sp_params.resultado_sp) {
          console.log('✅ Resultado del SP:', response.data.sp_params.resultado_sp);
        }

        console.log('================================================================================');
      }

      return {
        success: true,
        executionId: response?.data?.execution_id,
        data: response?.data
      };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al subir Sumas y Saldos'
      };
    }
  }

  // ===========================================
  // VALIDACIÓN
  // ===========================================

  async startValidation(executionId) {
    try {
      const response = await api.post(`/api/import/validate/${encodeURIComponent(executionId)}`);
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar validación'
      };
    }
  }

  async getValidationStatus(executionId) {
    try {
      const response = await api.get(`/api/import/validate/${encodeURIComponent(executionId)}/status`);
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Validación no encontrada' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener estado'
      };
    }
  }

  async pollValidationStatus(executionId, options = {}) {
    const {
      intervalMs = 2000,
      timeoutMs = 180000,
      onProgress = null
    } = options;

    const pollingKey = `validation_${executionId}`;
    if (this.activePolling.has(pollingKey)) {
      return { success: false, error: 'Ya hay un polling activo para esta validación' };
    }

    this.activePolling.add(pollingKey);
    const startTime = Date.now();

    try {
      while (true) {
        const statusResult = await this.getValidationStatus(executionId);

        if (statusResult.success) {
          const status = statusResult.data?.status?.toLowerCase();

          if (onProgress) {
            onProgress(statusResult.data);
          }

          if (status === 'completed' || status === 'success') {
            const success = statusResult.data?.validation_result?.is_valid !== false;
            return { success, finalStatus: status, data: statusResult.data };
          } else if (['error', 'failed'].includes(status)) {
            return { success: false, finalStatus: status, data: statusResult.data };
          }
        } else if (statusResult.statusCode && statusResult.statusCode !== 404) {
          return { success: false, finalStatus: 'error', error: statusResult.error };
        }

        if (Date.now() - startTime > timeoutMs) {
          return {
            success: false,
            finalStatus: 'timeout',
            error: 'La validación tardó demasiado tiempo'
          };
        }

        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    } finally {
      this.activePolling.delete(pollingKey);
    }
  }

  // ===========================================
  // CONVERSIÓN
  // ===========================================

  async startConversion(executionId) {
    try {
      const response = await api.post(`/api/import/convert/${encodeURIComponent(executionId)}`);
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar conversión'
      };
    }
  }

  async getConversionStatus(executionId) {
    try {
      const response = await api.get(`/api/import/convert/${encodeURIComponent(executionId)}/status`);
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Conversión no encontrada' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message
      };
    }
  }

  async pollConversionStatus(executionId, options = {}) {
    const {
      intervalMs = 2000,
      timeoutMs = 300000,
      onProgress = null
    } = options;

    const pollingKey = `conversion_${executionId}`;
    if (this.activePolling.has(pollingKey)) {
      return { success: false, error: 'Ya hay un polling activo para esta conversión' };
    }

    this.activePolling.add(pollingKey);
    const startTime = Date.now();

    try {
      while (true) {
        const statusResult = await this.getConversionStatus(executionId);

        if (statusResult.success) {
          const status = statusResult.data?.status?.toLowerCase();

          if (onProgress) {
            onProgress(statusResult.data);
          }

          if (status === 'completed' || status === 'conversion_completed') {
            return { success: true, finalStatus: status, data: statusResult.data };
          } else if (['error', 'failed'].includes(status)) {
            return { success: false, finalStatus: status, data: statusResult.data };
          }
        } else if (statusResult.statusCode && statusResult.statusCode !== 404) {
          return { success: false, finalStatus: 'error', error: statusResult.error };
        }

        if (Date.now() - startTime > timeoutMs) {
          return {
            success: false,
            finalStatus: 'timeout',
            error: 'La conversión tardó demasiado tiempo'
          };
        }

        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    } finally {
      this.activePolling.delete(pollingKey);
    }
  }

  // ===========================================
  // MAPEO (LIBRO DIARIO)
  // ===========================================

  async startAutomaticMapeo(executionId, erpHint = 'sap') {
    try {
      const cacheKey = `mapeo_start_${executionId}_${erpHint || 'none'}`;
      if (this.requestCache.has(cacheKey)) {
        return this.requestCache.get(cacheKey);
      }

      const params = erpHint ? { erp_hint: erpHint } : {};
      const response = await api.post(
        `/api/import/mapeo/${encodeURIComponent(executionId)}`,
        null,
        { params }
      );

      const result = { success: true, data: response?.data };
      this.requestCache.set(cacheKey, result);
      return result;
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar mapeo'
      };
    }
  }

  async getMapeoStatus(executionId) {
    try {
      const response = await api.get(`/api/import/mapeo/${encodeURIComponent(executionId)}/status`);
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener estado de mapeo'
      };
    }
  }

  async getFieldsMapping(executionId) {
    try {
      const cacheKey = `fields_mapping_${executionId}`;
      if (this.requestCache.has(cacheKey)) {
        return this.requestCache.get(cacheKey);
      }

      const response = await api.get(`/api/import/mapeo/${encodeURIComponent(executionId)}/fields-mapping`);

      const normalized = {
        mapped_fields: response?.data?.mapped_fields || {},
        unmapped_fields: response?.data?.unmapped_fields || [],
        confidence: response?.data?.confidence || {},
        total_mapped: response?.data?.total_mapped || 0,
        total_unmapped: response?.data?.total_unmapped || 0,
      };

      const result = { success: true, data: normalized };
      this.requestCache.set(cacheKey, result);
      return result;
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener mapeo de campos'
      };
    }
  }

  async getUnmappedFields(executionId) {
    try {
      const response = await api.get(
        `/api/import/mapeo/${encodeURIComponent(executionId)}/unmapped`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener campos no mapeados'
      };
    }
  }

  async applyManualMapping(executionId, mappings = []) {
    try {
      const body = { mappings };
      const response = await api.post(
        `/api/import/mapeo/${encodeURIComponent(executionId)}/apply-manual-mapping`,
        body
      );

      this.requestCache.delete(`fields_mapping_${executionId}`);
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al aplicar mapeo manual'
      };
    }
  }

  // ===========================================
  // MAPEO (SUMAS Y SALDOS) - CORREGIDO
  // ===========================================

  async startSumasSaldosMapeo(executionId) {
    try {
      const response = await api.post(
        `/api/import/mapeo-sumas-saldos/${encodeURIComponent(executionId)}`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar mapeo de Sumas y Saldos'
      };
    }
  }

  async getSumasSaldosMapeoStatus(executionId) {
    try {
      const response = await api.get(
        `/api/import/mapeo-sumas-saldos/${encodeURIComponent(executionId)}/status`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener estado de mapeo'
      };
    }
  }

  // CORREGIDO: El endpoint correcto es /unmapped-fields
  async getSumasSaldosUnmappedFields(executionId) {
    try {
      const response = await api.get(
        `/api/import/mapeo-sumas-saldos/${encodeURIComponent(executionId)}/unmapped-fields`
      );
      
      // El backend devuelve los campos con estructura correcta
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener campos no mapeados'
      };
    }
  }

  async applySumasSaldosManualMapping(executionId, mappings = []) {
    try {
      const body = { mappings };
      const response = await api.post(
        `/api/import/mapeo-sumas-saldos/${encodeURIComponent(executionId)}/apply-manual-mapping`,
        body
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al aplicar mapeo manual'
      };
    }
  }

  // NUEVO: Preview de Sumas y Saldos
  async getSumasSaldosPreview(executionId) {
    try {
      const response = await api.get(
        `/api/import/preview-sumas-saldos/${encodeURIComponent(executionId)}`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener preview de Sumas y Saldos'
      };
    }
  }

  // ===========================================
  // VALIDACIÃ“N COORDINADA
  // ===========================================

  async validateCoordinatedFiles(executionId) {
    try {
      const coordinated = await this.getCoordinatedExecutions(executionId);
      if (!coordinated.success) {
        return { success: false, error: 'No se pudieron obtener archivos coordinados' };
      }

      const results = {
        libroDiario: { attempted: false, success: false, finalStatus: null, error: null },
        sumasSaldos: { attempted: false, success: false, finalStatus: null, error: null },
      };

      // Libro Diario - SOLO VALIDACIÃ“N
      if (coordinated.data.libroDiario) {
        results.libroDiario.attempted = true;
        const ldId = coordinated.data.libroDiario.executionId;

        const startResult = await this.startValidation(ldId);
        if (!startResult.success) {
          results.libroDiario.error = startResult.error;
        } else {
          const pollResult = await this.pollValidationStatus(ldId, {
            intervalMs: 2000,
            timeoutMs: 180000
          });
          results.libroDiario.success = pollResult.success;
          results.libroDiario.finalStatus = pollResult.finalStatus;
          results.libroDiario.error = pollResult.error || null;
        }
      }

      // Sumas y Saldos - SOLO VALIDACIÃ“N
      if (coordinated.data.sumasSaldos) {
        results.sumasSaldos.attempted = true;
        const ssId = coordinated.data.sumasSaldos.executionId;

        const startResult = await this.startValidation(ssId);
        if (!startResult.success) {
          results.sumasSaldos.error = startResult.error;
        } else {
          const pollResult = await this.pollValidationStatus(ssId, {
            intervalMs: 2000,
            timeoutMs: 180000
          });
          results.sumasSaldos.success = pollResult.success;
          results.sumasSaldos.finalStatus = pollResult.finalStatus;
          results.sumasSaldos.error = pollResult.error || null;
        }
      }

      const overallSuccess =
        results.libroDiario.success &&
        (!results.sumasSaldos.attempted || results.sumasSaldos.success);

      const summary = {
        filesAttempted: (results.libroDiario.attempted ? 1 : 0) + (results.sumasSaldos.attempted ? 1 : 0),
        filesSuccessful: (results.libroDiario.success ? 1 : 0) + (results.sumasSaldos.success ? 1 : 0),
      };

      return { success: overallSuccess, results, summary };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // ===========================================
  // PROCESO COMPLETO PASO A PASO
  // ===========================================

  async runCompleteValidationConversionMapeo(executionId) {
    try {
      console.log('ðŸš€ Iniciando proceso completo para:', executionId);

      // PASO 1: Validación coordinada
      const validationResult = await this.validateCoordinatedFiles(executionId);
      if (!validationResult.success) {
        throw new Error(validationResult.error || 'Validación falló');
      }

      if (!validationResult.results.libroDiario.success) {
        throw new Error(validationResult.results.libroDiario.error || 'Validación de Libro Diario falló');
      }

      console.log('Validación completada');

      // PASO 2: Conversión (solo Libro Diario)
      console.log('ðŸ”„ Iniciando conversión...');

      await new Promise(resolve => setTimeout(resolve, 2000));

      const conversionStart = await this.startConversion(executionId);
      if (!conversionStart.success) {
        throw new Error(conversionStart.error || 'Error al iniciar conversión');
      }

      const conversionResult = await this.pollConversionStatus(executionId, {
        intervalMs: 2000,
        timeoutMs: 300000
      });

      if (!conversionResult.success) {
        throw new Error(conversionResult.error || 'Conversión falló');
      }

      console.log('Conversión completada');

      // PASO 3: Mapeo automÃ¡tico de Libro Diario
      console.log('ðŸ—ºï¸ Iniciando mapeo de Libro Diario...');

      const mapeoStart = await this.startAutomaticMapeo(executionId, 'sap');
      if (!mapeoStart.success) {
        throw new Error(mapeoStart.error || 'Error al iniciar mapeo');
      }

      let mapeoCompleted = false;
      let attempts = 0;
      const maxAttempts = 30;

      while (!mapeoCompleted && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000));

        const mapeoStatus = await this.getMapeoStatus(executionId);
        if (mapeoStatus.success) {
          const status = mapeoStatus.data?.status?.toLowerCase();
          if (status === 'completed' || status === 'mapeo_completed') {
            mapeoCompleted = true;
            console.log('Mapeo de Libro Diario completado');
            break;
          } else if (status === 'failed' || status === 'error') {
            throw new Error(mapeoStatus.data?.error || 'Mapeo falló');
          }
        }

        attempts++;
      }

      if (!mapeoCompleted) {
        throw new Error('Mapeo tardó demasiado tiempo');
      }

      // PASO 4: Mapeo de Sumas y Saldos (si existe)
      const coordinated = await this.getCoordinatedExecutions(executionId);
      if (coordinated.success && coordinated.data.sumasSaldos) {
        console.log('ðŸ—ºï¸ Iniciando mapeo de Sumas y Saldos...');
        
        const ssMapeoStart = await this.startSumasSaldosMapeo(coordinated.data.sumasSaldos.executionId);

        if (ssMapeoStart.success) {
          let ssMapeoCompleted = false;
          let ssAttempts = 0;
          const maxSSAttempts = 30;

          while (!ssMapeoCompleted && ssAttempts < maxSSAttempts) {
            await new Promise(resolve => setTimeout(resolve, 2000));

            const ssStatus = await this.getSumasSaldosMapeoStatus(coordinated.data.sumasSaldos.executionId);
            if (ssStatus.success) {
              const status = ssStatus.data?.status?.toLowerCase();
              if (status === 'completed') {
                ssMapeoCompleted = true;
                console.log('Mapeo de Sumas y Saldos completado');
                break;
              } else if (status === 'failed' || status === 'error') {
                console.warn('Mapeo de Sumas y Saldos falló:', ssStatus.data?.error);
                break;
              }
            }
            ssAttempts++;
          }

          if (!ssMapeoCompleted) {
            console.warn('Mapeo de Sumas y Saldos no se completó en el tiempo esperado');
          }
        }
      }

      return {
        success: true,
        validationResult,
        conversionResult,
        message: 'Proceso completo exitoso'
      };

    } catch (error) {
      console.error('Error en proceso completo:', error);
      return {
        success: false,
        error: error.message || 'Error en el proceso completo'
      };
    }
  }

  // ===========================================
  // UTILIDADES Y ESTADO
  // ===========================================

  async getExecutionStatus(executionId) {
    try {
      const response = await api.get(`/api/import/status/${encodeURIComponent(executionId)}`);
      return { success: true, execution: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message
      };
    }
  }

  async getCoordinatedExecutions(executionId) {
    try {
      const ldId = executionId.endsWith('-ss') ? executionId.replace('-ss', '') : executionId;
      const ssId = executionId.endsWith('-ss') ? executionId : `${executionId}-ss`;

      const [ldResult, ssResult] = await Promise.allSettled([
        this.getExecutionStatus(ldId),
        this.getExecutionStatus(ssId)
      ]);

      const coordinated = {};

      if (ldResult.status === 'fulfilled' && ldResult.value.success) {
        coordinated.libroDiario = {
          executionId: ldId,
          ...ldResult.value.execution
        };
      }

      if (ssResult.status === 'fulfilled' && ssResult.value.success) {
        coordinated.sumasSaldos = {
          executionId: ssId,
          ...ssResult.value.execution
        };
      }

      return { success: true, data: coordinated };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Error al obtener executions coordinadas'
      };
    }
  }

  async getImportHistory() {
    return { success: true, executions: [] };
  }

  downloadFile(filename) {
    const link = document.createElement('a');
    link.href = `/api/import/download/${encodeURIComponent(filename)}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  // ... (mantén todos los métodos existentes) ...

  // ===========================================
  // VALIDATION RULES (Nuevo)
  // ===========================================

  /**
   * Inicia el proceso de validation rules
   * @param {string} executionId - ID de la ejecución
   * @param {string} period - Período en formato YYYY-MM
   * @returns {Promise<Object>}
   */
  async startValidationRules(executionId, period) {
    try {
      const response = await api.post(
        `/api/import/validate-rules/${encodeURIComponent(executionId)}`,
        { period }
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar validation rules'
      };
    }
  }

  /**
   * Obtiene el estado completo de validation rules
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async getValidationRulesStatus(executionId) {
    try {
      const response = await api.get(
        `/api/import/validate-rules/${encodeURIComponent(executionId)}/status`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Validation rules no encontrada' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener estado'
      };
    }
  }

  /**
   * Obtiene el resumen simplificado por fases (para la UI)
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async getValidationRulesSummary(executionId) {
    try {
      const response = await api.get(
        `/api/import/validate-rules/${encodeURIComponent(executionId)}/summary`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Summary no encontrado' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener summary'
      };
    }
  }

  /**
   * Polling para obtener el progreso de validation rules en tiempo real
   * @param {string} executionId - ID de la ejecución
   * @param {Object} options - Opciones de polling
   * @returns {Promise<Object>}
   */
  async pollValidationRulesProgress(executionId, options = {}) {
    const {
      intervalMs = 2000,
      timeoutMs = 300000, // 5 minutos
      onProgress = null
    } = options;

    const pollingKey = `validation_rules_${executionId}`;
    if (this.activePolling.has(pollingKey)) {
      return { success: false, error: 'Ya hay un polling activo para esta validation' };
    }

    this.activePolling.add(pollingKey);
    const startTime = Date.now();

    try {
      while (true) {
        // Obtener el summary (más ligero que el status completo)
        const summaryResult = await this.getValidationRulesSummary(executionId);

        if (!summaryResult.success) {
          if (summaryResult.statusCode === 404) {
            // Aún no hay resultados, continuar esperando
            if (onProgress) {
              onProgress({
                status: 'processing',
                phases: [
                  { phase: 1, status: 'pending' },
                  { phase: 2, status: 'pending' },
                  { phase: 3, status: 'pending' },
                  { phase: 4, status: 'pending' }
                ],
                progress: { completed: 0, total: 4 }
              });
            }
          } else {
            throw new Error(summaryResult.error);
          }
        } else {
          const summary = summaryResult.data;

          // Notificar progreso
          if (onProgress) {
            onProgress(summary);
          }

          // Verificar si ya completó todas las fases
          if (summary.status === 'completed' || summary.status === 'failed') {
            this.activePolling.delete(pollingKey);
            return { success: true, data: summary };
          }

          // Verificar si el progreso está completo (4 de 4 fases)
          if (summary.progress && summary.progress.completed === summary.progress.total) {
            this.activePolling.delete(pollingKey);
            return { success: true, data: summary };
          }
        }

        // Timeout check
        if (Date.now() - startTime > timeoutMs) {
          this.activePolling.delete(pollingKey);
          throw new Error('Timeout esperando validation rules');
        }

        // Esperar antes de la siguiente consulta
        await new Promise(resolve => setTimeout(resolve, intervalMs));
      }
    } catch (error) {
      this.activePolling.delete(pollingKey);
      return {
        success: false,
        error: error.message || 'Error en polling de validation rules'
      };
    }
  }

  /**
   * Cancela el polling activo para validation rules
   * @param {string} executionId - ID de la ejecución
   */
  cancelValidationRulesPolling(executionId) {
    const pollingKey = `validation_rules_${executionId}`;
    this.activePolling.delete(pollingKey);
  }

  /**
   * Inicia el proceso de validación de Sumas y Saldos (solo Fase 1)
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async startSumasSaldosValidation(executionId) {
    try {
      const response = await api.post(
        `/api/import/validate-sumas-saldos/${encodeURIComponent(executionId)}`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al iniciar validación de Sumas y Saldos'
      };
    }
  }

  /**
   * Obtiene el estado completo de la validación de Sumas y Saldos
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async getSumasSaldosValidationStatus(executionId) {
    try {
      const response = await api.get(
        `/api/import/validate-sumas-saldos/${encodeURIComponent(executionId)}/status`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Validación de Sumas y Saldos no encontrada' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener estado'
      };
    }
  }

  /**
   * Obtiene el estado resumido de la validación de Sumas y Saldos
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async getSumasSaldosValidationSummary(executionId) {
    try {
      const response = await api.get(
        `/api/import/validate-sumas-saldos/${encodeURIComponent(executionId)}/summary`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      if (error?.response?.status === 404) {
        return { success: false, statusCode: 404, error: 'Validación no encontrada' };
      }
      return {
        success: false,
        statusCode: error?.response?.status,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener resumen'
      };
    }
  }

  /**
   * Realiza polling del progreso de validación de Sumas y Saldos
   * @param {string} executionId - ID de la ejecución
   * @param {Object} options - Opciones de polling
   * @returns {Promise<Object>}
   */
  async pollSumasSaldosValidationProgress(executionId, options = {}) {
    const {
      intervalMs = 2000,
      timeoutMs = 300000,
      onProgress = null
    } = options;

    const pollingKey = `sumas_saldos_validation_${executionId}`;
    
    // Marcar como polling activo
    this.activePolling.add(pollingKey);
    
    const startTime = Date.now();
    
    try {
      while (this.activePolling.has(pollingKey)) {
        // Verificar timeout
        if (Date.now() - startTime > timeoutMs) {
          this.activePolling.delete(pollingKey);
          return {
            success: false,
            error: 'Timeout esperando validación de Sumas y Saldos'
          };
        }

        // Obtener estado actual
        const statusResult = await this.getSumasSaldosValidationStatus(executionId);
        
        if (!statusResult.success) {
          if (statusResult.statusCode === 404) {
            // Aún no iniciado, seguir esperando
            await new Promise(resolve => setTimeout(resolve, intervalMs));
            continue;
          }
          throw new Error(statusResult.error);
        }

        const status = statusResult.data;

        // Llamar callback de progreso si existe
        if (onProgress) {
          // Obtener resumen con detalles de fases
          const summaryResult = await this.getSumasSaldosValidationSummary(executionId);
          if (summaryResult.success) {
            onProgress(summaryResult.data);
          }
        }

        // Verificar si completó
        if (status.status === 'completed') {
          this.activePolling.delete(pollingKey);
          return {
            success: true,
            data: status
          };
        }

        // Verificar si falló
        if (status.status === 'failed') {
          this.activePolling.delete(pollingKey);
          return {
            success: false,
            error: status.error || 'Validación de Sumas y Saldos falló'
          };
        }

        // Esperar antes del siguiente poll
        await new Promise(resolve => setTimeout(resolve, intervalMs));
      }

      // Si se canceló el polling
      return {
        success: false,
        error: 'Polling cancelado'
      };

    } catch (error) {
      this.activePolling.delete(pollingKey);
      console.error('Error in Sumas y Saldos validation polling:', error);
      return {
        success: false,
        error: error.message || 'Error en polling de validación de Sumas y Saldos'
      };
    }
  }

  /**
   * Cancela el polling activo para validación de Sumas y Saldos
   * @param {string} executionId - ID de la ejecución
   */
  cancelSumasSaldosValidationPolling(executionId) {
    const pollingKey = `sumas_saldos_validation_${executionId}`;
    this.activePolling.delete(pollingKey);
  }

  /**
   * Obtiene detalles de la Fase 1 de Sumas y Saldos
   * @param {string} executionId - ID de la ejecución
   * @returns {Promise<Object>}
   */
  async getSumasSaldosPhase1Details(executionId) {
    try {
      const response = await api.get(
        `/api/import/validate-sumas-saldos/${encodeURIComponent(executionId)}/phase/1`
      );
      return { success: true, data: response?.data };
    } catch (error) {
      return {
        success: false,
        error: error?.response?.data?.detail || error?.message || 'Error al obtener detalles de fase 1'
      };
    }
  }

}

export default new ImportService();