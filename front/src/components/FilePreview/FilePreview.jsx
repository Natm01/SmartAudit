// src/components/FilePreview/FilePreview.jsx
import React, { useEffect, useRef, useState } from 'react';
import FieldMapper from '../FieldMapper/FieldMapper';
import api from '../../services/api';

const FilePreview = ({ file, fileType, executionId, maxRows = 25, showMapperByDefault = true, onMappingApplied }) => {
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ NUEVO: Estado para mantener headers ORIGINALES del Excel
  const [originalHeaders, setOriginalHeaders] = useState([]);

  // ============================================
  // CLAVE UNIFICADA: Usar la MISMA que FieldMapper
  // ============================================
  const getStorageKey = () => `mapper_data_${executionId}_${fileType}`;

  // Inicializar showMappedPreview y fieldMappings desde sessionStorage
  const getInitialMappedPreviewState = () => {
    if (!executionId) return false;

    // CRÍTICO: Verificar el flag correcto según el tipo de archivo
    const storageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(storageKey);
    const wasApplied = mappingAppliedFlag === 'true';

    console.log(`🔍 getInitialMappedPreviewState (${fileType}):`, {
      storageKey,
      mappingAppliedFlag,
      wasApplied
    });

    return wasApplied;
  };

  const getInitialFieldMappings = () => {
    if (!executionId) return {};

    // CRÍTICO: Solo cargar mapeos si el mapeo fue aplicado
    const mappingAppliedStorageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(mappingAppliedStorageKey);

    console.log(`🔍 getInitialFieldMappings (${fileType}):`, {
      mappingAppliedStorageKey,
      mappingAppliedFlag,
      shouldLoadMappings: mappingAppliedFlag === 'true'
    });

    if (mappingAppliedFlag !== 'true') {
      console.log('⚠️ Mapeo NO fue aplicado explícitamente, NO cargar mapeos visuales');
      return {};
    }

    // ✅ CORREGIDO: Usar la MISMA clave que FieldMapper
    const mapperDataKey = getStorageKey();

    try {
      const saved = sessionStorage.getItem(mapperDataKey);
      if (saved) {
        const parsed = JSON.parse(saved);

        console.log(`💾 Leyendo desde clave correcta: ${mapperDataKey}`, parsed);

        let mappings = {};
        // FieldMapper guarda con estructura { mappings: {...}, confidences: {...}, ... }
        if (parsed.mappings) {
          mappings = parsed.mappings;
        } else {
          // Formato antiguo (solo por compatibilidad)
          mappings = parsed;
        }

        if (Object.keys(mappings).length > 0) {
          // Reconstruir mapeos en formato correcto para preview mapeado
          // Los mapeos guardados son {columnaExcel: campoBD}
          // Pero para el preview mapeado necesitamos {campoBD: campoBD}
          const reconstructedMappings = {};
          Object.entries(mappings).forEach(([excelCol, bdField]) => {
            if (bdField) {
              reconstructedMappings[bdField] = bdField;
            }
          });

          console.log('🎨 Inicializando fieldMappings desde sessionStorage:');
          console.log('   Clave usada:', mapperDataKey);
          console.log('   Mapeos originales:', mappings);
          console.log('   Mapeos reconstruidos:', reconstructedMappings);

          return reconstructedMappings;
        }
      }
    } catch (e) {
      console.error(`❌ Error al parsear mapeos desde ${mapperDataKey}:`, e);
    }

    return {};
  };

  const [fieldMappings, setFieldMappings] = useState(getInitialFieldMappings());
  const [showMappedNames, setShowMappedNames] = useState(getInitialMappedPreviewState());
  const [isMapperOpen, setIsMapperOpen] = useState(showMapperByDefault);
  const [showAppliedNotification, setShowAppliedNotification] = useState(false);

  const [showMappedPreview, setShowMappedPreview] = useState(getInitialMappedPreviewState());

  // Inicializar appliedMappingsRef desde sessionStorage
  const getInitialAppliedMappings = () => {
    if (!executionId) return {};

    // CRÍTICO: Verificar el flag correcto según el tipo de archivo
    const mappingAppliedStorageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(mappingAppliedStorageKey);

    console.log(`🔍 getInitialAppliedMappings (${fileType}):`, {
      mappingAppliedStorageKey,
      mappingAppliedFlag,
      shouldLoadApplied: mappingAppliedFlag === 'true'
    });

    if (mappingAppliedFlag !== 'true') {
      console.log('⚠️ Mapeo NO fue aplicado explícitamente, NO cargar appliedMappings');
      return {};
    }

    // ✅ CORREGIDO: Usar la MISMA clave que FieldMapper
    const mapperDataKey = getStorageKey();

    try {
      const saved = sessionStorage.getItem(mapperDataKey);
      if (saved) {
        const parsed = JSON.parse(saved);

        console.log(`💾 Leyendo appliedMappings desde clave correcta: ${mapperDataKey}`, parsed);

        let mappings = {};
        // FieldMapper guarda con estructura { mappings: {...}, confidences: {...}, ... }
        if (parsed.mappings) {
          mappings = parsed.mappings;
        } else {
          // Formato antiguo (solo por compatibilidad)
          mappings = parsed;
        }

        if (Object.keys(mappings).length > 0) {
          console.log('📌 Inicializando appliedMappingsRef desde sessionStorage:', mappings);
          return mappings;
        }
      }
    } catch (e) {
      console.error(`❌ Error al parsear appliedMappings desde ${mapperDataKey}:`, e);
    }

    return {};
  };

  const appliedMappingsRef = useRef(getInitialAppliedMappings());
  const isApplyingMappingRef = useRef(false);
  const initialMappingsLoadedRef = useRef(false);
  //  NUEVO: Flag para evitar recargas innecesarias
  const previewLoadedRef = useRef(false);

  const abortRef = useRef(false);
  const retryCountRef = useRef(0);
  const maxRetries = 10;
  const retryInterval = 2000;

  useEffect(() => { 
    abortRef.current = false; 
    retryCountRef.current = 0;
    return () => { abortRef.current = true; }; 
  }, []);

  const sanitizeCell = (v) => (v === null || v === undefined ? '' : (typeof v === 'object' ? JSON.stringify(v) : String(v)));

  const pickRowsLibroDiario = (payload) => {
    const rows = payload?.converted?.rows || payload?.converted?.data || payload?.converted ||
                 payload?.table?.rows || payload?.table || payload?.data || [];
    return Array.isArray(rows) ? rows : [];
  };

  const pickRowsSumasSaldos = (payload) => {
    const rows = payload?.preview_data || [];
    return Array.isArray(rows) ? rows : [];
  };

  const buildTable = (rowsObjArray) => {
    const headers = Array.from(rowsObjArray.reduce((acc, row) => {
      Object.keys(row || {}).forEach((k) => acc.add(k)); 
      return acc;
    }, new Set()));
    const table = rowsObjArray.map((r) => headers.map((h) => sanitizeCell(r?.[h])));
    return { headers, table };
  };

  //  ✅ CORREGIDO: Función que busca usando la clave CORRECTA
  const loadMappingsFromStorage = () => {
    if (!executionId) return false;

    console.log('💾 Buscando mapeos en sessionStorage con clave correcta...');

    // CRÍTICO: Verificar el flag correcto según el tipo de archivo
    const mappingAppliedStorageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(mappingAppliedStorageKey);
    const wasExplicitlyApplied = mappingAppliedFlag === 'true';

    console.log(`🔍 Mapeo explícitamente aplicado? (${fileType}):`, {
      mappingAppliedStorageKey,
      mappingAppliedFlag,
      wasExplicitlyApplied
    });

    // ✅ CORREGIDO: Usar la MISMA clave que FieldMapper
    const mapperDataKey = getStorageKey();

    try {
      const saved = sessionStorage.getItem(mapperDataKey);

      if (saved) {
        console.log(`💾 Datos encontrados en clave: ${mapperDataKey}`);

        const parsed = JSON.parse(saved);
        console.log(`💾 Contenido:`, parsed);

        let mappings = {};
        // FieldMapper guarda con estructura { mappings: {...}, confidences: {...}, ... }
        if (parsed.mappings) {
          mappings = parsed.mappings;
        } else {
          // Formato antiguo (solo por compatibilidad)
          mappings = parsed;
        }

        if (Object.keys(mappings).length > 0) {
          console.log(`✅ RESTAURANDO ${Object.keys(mappings).length} mapeos desde: ${mapperDataKey}`);

          // CRÍTICO: Solo marcar como aplicado si fue explícitamente aplicado
          if (wasExplicitlyApplied) {
            appliedMappingsRef.current = mappings;

            // Reconstruir mapeos para el preview mapeado
            // Los mapeos guardados son {columnaExcel: campoBD}
            // Pero para el preview mapeado necesitamos {campoBD: campoBD}
            const reconstructedMappings = {};
            Object.entries(mappings).forEach(([excelCol, bdField]) => {
              if (bdField) {
                reconstructedMappings[bdField] = bdField;
              }
            });

            setFieldMappings(reconstructedMappings);
            setShowMappedNames(true);
            setShowMappedPreview(true);
            console.log('✅ Preview mapeado activado (mapeo fue aplicado explícitamente con botón "Aplicar Mapeo")');
            console.log('   Mapeos reconstruidos:', reconstructedMappings);
          } else {
            // NO cargar los mapeos visuales si no fueron aplicados explícitamente
            // Los mapeos están en sessionStorage para FieldMapper, pero NO para el preview
            setFieldMappings({});  // NO cargar mapeos visuales
            setShowMappedNames(false);
            setShowMappedPreview(false);
            console.log('⚠️ Mapeos encontrados en sessionStorage pero NO aplicados explícitamente');
            console.log('   Preview permanece ORIGINAL hasta que usuario haga click en "Aplicar Mapeo"');
          }
          return wasExplicitlyApplied;
        }
      } else {
        console.log(`ℹ️ No se encontraron datos en clave: ${mapperDataKey}`);
      }
    } catch (e) {
      console.error(`❌ Error al parsear mapeos desde ${mapperDataKey}:`, e);
    }

    console.log('ℹ️ No se encontraron mapeos aplicados');
    return false;
  };

  const fetchPreviewOnce = async (forceOriginal = false) => {
    let url;

    if (fileType === 'sumas_saldos') {
      // CRÍTICO: Para Sumas y Saldos, usar endpoint correcto según forceOriginal
      if (!forceOriginal && showMappedPreview) {
        // Preview MAPEADO (usa sumas_saldos_csv_path)
        url = `/api/import/preview-sumas-saldos/${encodeURIComponent(executionId)}?_=${Date.now()}`;
        console.log('📄 Cargando preview MAPEADO de Sumas y Saldos');
      } else {
        // Preview ORIGINAL (usa sumas_saldos_raw_path)
        url = `/api/import/preview-sumas-saldos/${encodeURIComponent(executionId)}/original?_=${Date.now()}`;
        console.log('📄 Cargando preview ORIGINAL de Sumas y Saldos');
      }
    } else {
      // Si forceOriginal es true, siempre cargar el original
      if (!forceOriginal && showMappedPreview) {
        url = `/api/import/preview/${encodeURIComponent(executionId)}/mapped?_=${Date.now()}`;
        console.log('📄 Cargando preview MAPEADO');
      } else {
        url = `/api/import/preview/${encodeURIComponent(executionId)}?_=${Date.now()}`;
        console.log('📄 Cargando preview ORIGINAL');
      }
    }

    const resp = await api.get(url, {
      headers: { Accept: 'application/json, text/plain, */*' },
      transformResponse: [(data) => { 
        try { 
          return typeof data === 'string' ? JSON.parse(data) : data; 
        } catch { 
          return { data: [] }; 
        } 
      }],
      timeout: 30000
    });

    const payload = resp?.data || {};
    
    let rows;
    if (fileType === 'sumas_saldos') {
      rows = pickRowsSumasSaldos(payload);
    } else {
      rows = pickRowsLibroDiario(payload);
    }
    
    return buildTable(rows);
  };

  // ✅ NUEVA FUNCIÓN: Cargar headers ORIGINALES (siempre del archivo Excel)
  const fetchOriginalHeaders = async () => {
    if (!executionId) return [];

    try {
      console.log('📋 Cargando headers ORIGINALES del archivo Excel...');

      let url;
      if (fileType === 'sumas_saldos') {
        url = `/api/import/preview-sumas-saldos/${encodeURIComponent(executionId)}/original?_=${Date.now()}`;
      } else {
        url = `/api/import/preview/${encodeURIComponent(executionId)}?_=${Date.now()}`;
      }

      const resp = await api.get(url, {
        headers: { Accept: 'application/json, text/plain, */*' },
        transformResponse: [(data) => {
          try {
            return typeof data === 'string' ? JSON.parse(data) : data;
          } catch {
            return { data: [] };
          }
        }],
        timeout: 30000
      });

      const payload = resp?.data || {};

      let rows;
      if (fileType === 'sumas_saldos') {
        rows = pickRowsSumasSaldos(payload);
      } else {
        rows = pickRowsLibroDiario(payload);
      }

      const table = buildTable(rows);

      console.log('✅ Headers originales obtenidos:', table.headers);
      return table.headers;
    } catch (error) {
      console.error('❌ Error al cargar headers originales:', error);
      return [];
    }
  };

  const loadPreviewData = async () => {
    if (!executionId) return;

    try {
      setLoading(true);
      setError(null);

      let wasApplied = false;
      let loadedMappings = {};

      //  Si es la primera carga, intentar cargar mapeos
      if (!initialMappingsLoadedRef.current) {
        console.log('🔄 Primera carga - buscando mapeos...');
        wasApplied = loadMappingsFromStorage();

        // Obtener los mapeos cargados
        loadedMappings = { ...appliedMappingsRef.current };

        initialMappingsLoadedRef.current = true;

        console.log('📊 Estado después de cargar mapeos:', {
          wasApplied,
          loadedMappingsCount: Object.keys(loadedMappings).length,
          showMappedPreview
        });
      }

      // CRÍTICO: Determinar si debe cargar preview mapeado
      // Solo si appliedMappingsRef tiene contenido (significa que se aplicó mapeo)
      const hasMappingApplied = Object.keys(appliedMappingsRef.current).length > 0;
      const forceOriginal = !hasMappingApplied;

      console.log('📊 Estado antes de cargar preview:', {
        showMappedPreview,
        hasMappingApplied,
        forceOriginal,
        fieldMappingsCount: Object.keys(fieldMappings).length,
        appliedMappingsCount: Object.keys(appliedMappingsRef.current).length
      });

      console.log('🔍 forceOriginal:', forceOriginal, '(hasMappingApplied:', hasMappingApplied, ')');
      const t = await fetchPreviewOnce(forceOriginal);
      if (abortRef.current) return;

      if (t.headers.length === 0 || t.table.length === 0) {
        throw new Error('No se encontraron datos en el archivo procesado');
      }

      console.log('📊 Headers del preview:', t.headers);

      setPreviewData(t);

      // ✅ NUEVO: Cargar headers ORIGINALES (solo si no los tenemos ya)
      if (originalHeaders.length === 0) {
        console.log('📋 Primera carga - obteniendo headers originales...');
        const origHeaders = await fetchOriginalHeaders();
        if (origHeaders.length > 0) {
          setOriginalHeaders(origHeaders);
          console.log('✅ Headers originales guardados:', origHeaders);
        }
      }

      //  IMPORTANTE: Marcar que ya se cargó el preview
      previewLoadedRef.current = true;

      //  Solo reconstruir mapeos si el mapeo fue EXPLÍCITAMENTE aplicado
      // Verificar tanto el estado como appliedMappingsRef
      const shouldShowMapped = Object.keys(appliedMappingsRef.current).length > 0;

      console.log('🎨 Verificando si debe reconstruir mapeos:', {
        shouldShowMapped,
        showMappedPreview,
        willReconstruct: shouldShowMapped && showMappedPreview
      });

      if (shouldShowMapped && showMappedPreview) {
        console.log('🔄 Reconstruyendo mapeos visuales (mapeo aplicado explícitamente)...');
        const reconstructedMappings = {};

        t.headers.forEach(headerBD => {
          if (Object.values(appliedMappingsRef.current).includes(headerBD)) {
            reconstructedMappings[headerBD] = headerBD;
            console.log(`  ✓ ${headerBD}`);
          }
        });

        console.log(' Total reconstruido:', Object.keys(reconstructedMappings).length);
        console.log('🗺️ Mapeos reconstruidos:', reconstructedMappings);
        setFieldMappings(reconstructedMappings);
      } else {
        console.log('ℹ️ Preview original - mapeo no aplicado explícitamente');
        console.log('   shouldShowMapped:', shouldShowMapped);
        console.log('   showMappedPreview:', showMappedPreview);
      }

      retryCountRef.current = 0;
    } catch (e) {
      if (abortRef.current) return;
      
      const errorMessage = e?.response?.data?.detail || e?.message || 'Error al cargar el preview';
      
      if ((e?.response?.status === 404 || e?.response?.status === 400 || 
           errorMessage.includes('not found') || 
           errorMessage.includes('not generated yet') ||
           errorMessage.includes('No se encontraron datos')) 
          && retryCountRef.current < maxRetries) {
        
        retryCountRef.current++;
        console.log(`Preview attempt ${retryCountRef.current}/${maxRetries} failed, retrying...`);
        
        setError(`Preparando preview... (intento ${retryCountRef.current}/${maxRetries})`);
        
        setTimeout(() => {
          if (!abortRef.current) {
            loadPreviewData();
          }
        }, retryInterval);
        
        return;
      }
      
      setError(errorMessage);
    } finally { 
      if (!abortRef.current) setLoading(false); 
    }
  };

  useEffect(() => {
    console.log('🎨 Estado visual:', {
      showMappedPreview,
      mappingsCount: Object.keys(fieldMappings).length
    });
  }, [showMappedPreview, fieldMappings]);

  // 🆕 NUEVO: Notificar al padre cuando se carga el componente con mapeo ya aplicado
  useEffect(() => {
    // Solo ejecutar una vez al montar
    if (!executionId || !onMappingApplied) return;

    // Verificar si el mapeo fue aplicado (basado en el flag de sessionStorage)
    const storageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(storageKey);
    const wasApplied = mappingAppliedFlag === 'true';

    if (wasApplied) {
      console.log(`✅ FilePreview: Mapeo fue aplicado previamente, notificando al padre (${fileType})`);
      // Notificar al padre para que habilite el botón de validación
      onMappingApplied(true);
    } else {
      console.log(`ℹ️ FilePreview: Mapeo NO aplicado, NO notificar al padre (${fileType})`);
    }
  }, []); // Solo ejecutar al montar (dependencias vacías)

  //  MODIFICADO: Evitar recargas innecesarias
  useEffect(() => { 
    if (executionId) {
      //  Solo cargar si no se está aplicando mapeo Y no se ha cargado ya
      if (!isApplyingMappingRef.current && !previewLoadedRef.current) {
        setTimeout(() => {
          if (!abortRef.current) {
            loadPreviewData();
          }
        }, 1000);
      }
    }
  }, [executionId, fileType]); //  REMOVIDO: showMappedPreview de las dependencias

  //  NUEVO: useEffect separado solo para cuando cambia showMappedPreview DESPUÉS de cargar
  useEffect(() => {
    // Solo recargar si ya se cargó el preview inicial y cambia showMappedPreview
    if (previewLoadedRef.current && showMappedPreview && !isApplyingMappingRef.current) {
      console.log('🔄 showMappedPreview cambió - recargando preview mapeado...');
      loadPreviewData();
    }
  }, [showMappedPreview]);

  const handleMappingChange = async (newMap) => {
    console.log('📋 Mapeo aplicado:', newMap);

    isApplyingMappingRef.current = true;

    appliedMappingsRef.current = newMap || {};
    setFieldMappings(newMap || {});

    if (newMap && Object.keys(newMap).length > 0) {
      setShowMappedNames(true);
      setShowMappedPreview(true);
      retryCountRef.current = 0;

      setLoading(true);

      // Espera inicial para dar tiempo al backend
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Polling inteligente para verificar que el archivo esté disponible
      const maxRetries = 10;
      let retries = 0;
      let fileAvailable = false;

      while (retries < maxRetries && !fileAvailable) {
        try {
          const endpoint = fileType === 'sumas_saldos'
            ? `/api/import/preview-sumas-saldos/${encodeURIComponent(executionId)}`
            : `/api/import/preview-journal-entries/${encodeURIComponent(executionId)}`;

          const testPreview = await api.get(endpoint);

          if (testPreview.data?.preview_data?.length > 0) {
            fileAvailable = true;
            console.log(`✅ Archivo mapeado disponible después de ${retries} reintentos`);
          }
        } catch (e) {
          retries++;
          if (retries < maxRetries) {
            console.log(`⏳ Esperando disponibilidad del archivo... (intento ${retries}/${maxRetries})`);
            await new Promise(r => setTimeout(r, 500));
          }
        }
      }

      if (!fileAvailable) {
        console.warn('⚠️ Archivo no disponible después del timeout, intentando cargar de todos modos...');
      }

      isApplyingMappingRef.current = false;
      //  Resetear el flag para permitir la recarga
      previewLoadedRef.current = false;
      await loadPreviewData();

      // Notificar al padre que el mapeo fue aplicado
      if (onMappingApplied) {
        onMappingApplied(true);
      }

      // Guardar en sessionStorage que el mapeo fue aplicado
      try {
        // CORREGIDO: Guardar con sufijo correcto según tipo de archivo
        const storageKey = fileType === 'sumas_saldos'
          ? `mappingApplied_${executionId}-ss`  // Con sufijo -ss para Sumas y Saldos
          : `mappingApplied_${executionId}`;    // Sin sufijo para Libro Diario

        sessionStorage.setItem(storageKey, 'true');
        console.log(`✅ FilePreview: Guardado flag de mapeo aplicado: ${storageKey}`);
      } catch (error) {
        console.warn('Could not save mapping applied status:', error);
      }

      // NUEVO: Limpiar el estado de validación para permitir re-validar
      try {
        const validationStorageKey = `validation_${executionId}_${fileType}`;
        sessionStorage.removeItem(`${validationStorageKey}_phases`);
        sessionStorage.removeItem(`${validationStorageKey}_allCompleted`);
        sessionStorage.removeItem(`${validationStorageKey}_progressData`);
        sessionStorage.removeItem(`${validationStorageKey}_isExpanded`);
        sessionStorage.removeItem(`${validationStorageKey}_timestamp`);

        // Guardar un timestamp de cuando se aplicó el mapeo para que ValidationPhases lo detecte
        sessionStorage.setItem(`${validationStorageKey}_mappingAppliedAt`, Date.now().toString());

        console.log(`🧹 Estado de validación limpiado para permitir re-validar después de re-mapear`);
      } catch (error) {
        console.warn('Could not clear validation state:', error);
      }
    }

    setShowAppliedNotification(true);
    setTimeout(() => setShowAppliedNotification(false), 1800);
  };

  const getFileTypeLabel = () => (fileType === 'libro_diario' ? 'Libro Diario' : 'Sumas y Saldos (Excel)');
  const getMaxRowsLabel = () => (fileType === 'libro_diario' ? '25 primeras filas' : '10 primeras filas');

  if (!executionId) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
        <div className="text-gray-500">
          <p className="text-sm">Preview no disponible - ID de ejecución requerido</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showAppliedNotification && (
        <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Mapeo aplicado correctamente</span>
          </div>
          <p className="text-sm mt-1 opacity-90">Mostrando preview del archivo mapeado</p>
        </div>
      )}


      {previewData && (
        <FieldMapper
          originalFields={originalHeaders}
          executionId={executionId}
          fileType={fileType}
          isOpen={isMapperOpen}
          onToggle={() => setIsMapperOpen(!isMapperOpen)}
          onMappingChange={handleMappingChange}
        />
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Preview: {getFileTypeLabel()}
              {showMappedPreview && <span className="text-green-600 ml-2">(Mapeado)</span>}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {loading ? 'Cargando preview...' : `Mostrando ${getMaxRowsLabel()}`}
            </p>
          </div>
          
          {previewData && Object.keys(fieldMappings).length > 0 && !loading && (
            <button
              onClick={() => setShowMappedNames(!showMappedNames)}
              className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                showMappedNames 
                  ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
            >
              {showMappedNames ? '✓ Nombres BD' : 'Nombres Originales'}
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          {loading && (
            <div className="flex items-center justify-center p-12">
              <div className="flex flex-col items-center space-y-3">
                <svg className="animate-spin h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-sm text-gray-600">
                  {isApplyingMappingRef.current 
                    ? 'Aplicando mapeo y generando archivo...'
                    : retryCountRef.current > 0 
                      ? `Esperando... (${retryCountRef.current}/${maxRetries})`
                      : 'Cargando preview...'
                  }
                </p>
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="p-6 text-center">
              <div className="text-red-500 mb-3">
                <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <p className="text-sm text-red-600 mb-3">{error}</p>
              {retryCountRef.current >= maxRetries && (
                <button 
                  onClick={() => {
                    retryCountRef.current = 0;
                    previewLoadedRef.current = false;
                    loadPreviewData();
                  }}
                  className="mt-2 px-3 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700"
                >
                  Intentar de nuevo
                </button>
              )}
            </div>
          )}

          {previewData && !loading && (
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {previewData.headers
                    .map((h, originalIdx) => ({ header: h, originalIdx }))
                    .sort((a, b) => {
                      // Solo reordenar si el mapeo fue aplicado explícitamente
                      if (!showMappedPreview) return 0;
                      const aMapped = fieldMappings[a.header] ? 1 : 0;
                      const bMapped = fieldMappings[b.header] ? 1 : 0;
                      return bMapped - aMapped;
                    })
                    .map(({ header: h, originalIdx }) => {
                      // Solo mostrar como mapeado si el mapeo fue aplicado explícitamente
                      const mapped = showMappedPreview && fieldMappings[h];

                      // ✅ NUEVO: Buscar el nombre ORIGINAL del Excel (no del CSV mapeado)
                      // appliedMappingsRef.current = { "FECHA": "posting_date", ... }
                      // Si h = "posting_date", buscar "FECHA"
                      let originalName = h;
                      if (showMappedPreview && appliedMappingsRef.current) {
                        const entry = Object.entries(appliedMappingsRef.current).find(
                          ([_, bdField]) => bdField === h
                        );
                        if (entry) {
                          originalName = entry[0]; // El nombre original del Excel
                        }
                      }

                      return (
                        <th
                          key={h}
                          data-original-index={originalIdx}
                          className={`px-4 py-3 text-left text-xs font-semibold tracking-wider ${
                            mapped
                              ? 'text-blue-700 bg-blue-50'
                              : 'text-gray-700'
                          }`}
                        >
                          {mapped ? (
                            <div className="space-y-0.5">
                              <div className="text-blue-700 font-bold">{mapped}</div>
                              {originalName !== mapped && (
                                <div className="text-gray-500 font-normal text-[10px]">({originalName})</div>
                              )}
                            </div>
                          ) : (
                            h
                          )}
                        </th>
                      );
                    })}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {previewData.table.slice(0, fileType === 'libro_diario' ? 25 : 10).map((row, idx) => {
                  const sortedColumns = previewData.headers
                    .map((h, originalIdx) => ({ header: h, originalIdx }))
                    .sort((a, b) => {
                      // Solo reordenar si el mapeo fue aplicado explícitamente
                      if (!showMappedPreview) return 0;
                      const aMapped = fieldMappings[a.header] ? 1 : 0;
                      const bMapped = fieldMappings[b.header] ? 1 : 0;
                      return bMapped - aMapped;
                    });
                  
                  return (
                    <tr 
                      key={idx} 
                      className={`transition-colors ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      {sortedColumns.map(({ header, originalIdx }) => {
                        const cell = row[originalIdx];
                        // Solo mostrar como mapeado si el mapeo fue aplicado explícitamente
                        const isMapped = showMappedPreview && fieldMappings[header];

                        return (
                          <td
                            key={`${idx}-${originalIdx}`}
                            className={`px-4 py-2.5 whitespace-nowrap text-sm ${
                              isMapped
                                ? 'text-blue-900 font-medium bg-blue-50'
                                : 'text-gray-600'
                            }`}
                          >
                            {cell}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilePreview;