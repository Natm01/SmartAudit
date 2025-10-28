// frontend/src/components/FieldMapper/FieldMapper.jsx 
import React, { useState, useEffect } from 'react';
import importService from '../../services/importService';
// Importar los JSONs de campos
import journalEntriesMapping from '../../config/journal_entries_table_mapping.json';
import trialBalanceMapping from '../../config/trial_balance_table_mapping.json';

const FieldMapper = ({ originalFields, onMappingChange, isOpen, onToggle, fileType = 'libro_diario', executionId }) => {
  // Estado único unificado para el mapper
  const [mapperData, setMapperData] = useState({
    originalColumns: [],
    mappings: {},
    confidences: {},
    appliedToBackend: false
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // 🆕 Flag para controlar si ya se cargaron los datos iniciales
  const [initialDataLoaded, setInitialDataLoaded] = useState(false);

  // Clave única en sessionStorage
  const getStorageKey = () => `mapper_data_${executionId}_${fileType}`;

  // ============================================
  // FUNCIÓN UNIFICADA: Guardar TODO en sessionStorage
  // ============================================
  const saveMapperData = (data) => {
    if (!executionId) return;

    try {
      const dataToSave = {
        ...data,
        timestamp: Date.now(),
        executionId,
        fileType
      };
      sessionStorage.setItem(getStorageKey(), JSON.stringify(dataToSave));
      console.log('💾 Mapper data guardado:', {
        columnas: data.originalColumns.length,
        mapeos: Object.keys(data.mappings).length,
        key: getStorageKey()
      });
    } catch (error) {
      console.error('❌ Error guardando mapper data:', error);
    }
  };

  // ============================================
  // FUNCIÓN UNIFICADA: Cargar TODO desde sessionStorage
  // ============================================
  const loadMapperData = () => {
    if (!executionId) return null;

    try {
      const saved = sessionStorage.getItem(getStorageKey());
      if (saved) {
        const data = JSON.parse(saved);

        // Verificar que no haya expirado (30 minutos)
        const maxAge = 30 * 60 * 1000;
        if (Date.now() - data.timestamp < maxAge) {
          console.log('📦 Mapper data restaurado:', {
            columnas: data.originalColumns?.length || 0,
            mapeos: Object.keys(data.mappings || {}).length,
            key: getStorageKey()
          });
          return data;
        } else {
          console.log('⏰ Mapper data expirado, se descarta');
          sessionStorage.removeItem(getStorageKey());
        }
      }
    } catch (error) {
      console.error('❌ Error cargando mapper data:', error);
    }
    return null;
  };

  // Cargar campos desde JSON según el tipo de archivo
  const getDatabaseFieldsFromJSON = () => {
    if (fileType === 'sumas_saldos') {
      const fields = {};
      trialBalanceMapping.trial_balance.fields.forEach(field => {
        fields[field.name] = {
          label: field.label,
          required: field.required,
          description: `${field.label} (${field.type})`,
          fileTypes: ['sumas_saldos'],
          table: 'trial_balance',
          visible: field.visible !== undefined ? field.visible : true,
          order: field.order
        };
      });
      return fields;
    } else {
      const fields = {};
      
      journalEntriesMapping.journal_entries.header_fields.forEach(field => {
        fields[field.name] = {
          label: field.label,
          required: field.required,
          description: `${field.label} (${field.type})`,
          fileTypes: ['libro_diario'],
          table: 'journal_entries',
          structure: 'header',
          visible: field.visible !== undefined ? field.visible : true,
          order: field.order
        };
      });
      
      journalEntriesMapping.journal_entries.detail_fields.forEach(field => {
        fields[field.name] = {
          label: field.label,
          required: field.required,
          description: `${field.label} (${field.type})`,
          fileTypes: ['libro_diario'],
          table: 'journal_entry_lines',
          structure: 'detail',
          visible: field.visible !== undefined ? field.visible : true,
          order: field.order
        };
      });
      
      return fields;
    }
  };

  const databaseFields = getDatabaseFieldsFromJSON();

  // ============================================
  // EFECTO 1: Cargar datos al montar el componente (UNA VEZ)
  // ✅ CORREGIDO: Carga desde sessionStorage SIEMPRE al montar
  // ============================================
  useEffect(() => {
    if (!executionId || initialDataLoaded) return;

    console.log('🔄 Iniciando carga INICIAL de mapper desde sessionStorage...');

    // Intentar cargar desde sessionStorage primero
    const saved = loadMapperData();

    if (saved && (saved.originalColumns?.length > 0 || Object.keys(saved.mappings || {}).length > 0)) {
      // Usar datos guardados (incluso si solo tiene mapeos)
      setMapperData(saved);
      console.log('✅ Datos restaurados desde sessionStorage:', {
        columnas: saved.originalColumns?.length || 0,
        mapeos: Object.keys(saved.mappings || {}).length,
        appliedToBackend: saved.appliedToBackend
      });
    } else {
      console.log('ℹ️ No hay datos en sessionStorage');
    }

    // ✅ SIEMPRE marcar como cargado después del primer intento
    setInitialDataLoaded(true);

    // Verificar si el mapeo ya fue aplicado
    const storageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(storageKey);
    if (mappingAppliedFlag === 'true') {
      console.log('🔒 Mapeo fue aplicado previamente');
    }
  }, [executionId, fileType]); // Solo al montar (sin isOpen)

  // ============================================
  // EFECTO 1b: Cargar desde backend cuando se abre el mapper
  // ✅ NUEVO: Si el mapper se abre Y no hay mapeos, cargar desde backend
  // ============================================
  useEffect(() => {
    if (!executionId || !isOpen || !initialDataLoaded) return;

    // Solo cargar desde backend si NO hay mapeos guardados
    if (Object.keys(mapperData.mappings).length === 0) {
      console.log('🌐 Mapper abierto sin mapeos, cargando desde backend...');
      fetchMapeoFromBackend();
    }
  }, [isOpen, initialDataLoaded]); // Cuando se abre el mapper

  // ============================================
  // EFECTO 2: Guardar automáticamente cuando cambien los datos
  // ============================================
  useEffect(() => {
    if (mapperData.originalColumns.length > 0 || Object.keys(mapperData.mappings).length > 0) {
      saveMapperData(mapperData);
    }
  }, [mapperData]);

  // ============================================
  // EFECTO 3: Sincronizar columnas desde props
  // ✅ CORREGIDO: Actualiza columnas cuando llegan desde FilePreview
  // ============================================
  useEffect(() => {
    if (!originalFields || originalFields.length === 0 || !initialDataLoaded) return;

    // Comparar si las columnas son diferentes (archivo nuevo vs guardado)
    const currentColumns = mapperData.originalColumns;
    const newColumns = originalFields;

    // Si no hay columnas guardadas O las columnas son diferentes → actualizar
    const columnsChanged = currentColumns.length === 0 ||
                          currentColumns.length !== newColumns.length ||
                          !currentColumns.every((col, idx) => col === newColumns[idx]);

    if (columnsChanged) {
      console.log('🔄 Actualizando columnas desde archivo actual:', {
        antes: currentColumns.length,
        ahora: newColumns.length,
        nuevasColumnas: newColumns
      });

      // Si las columnas cambiaron Y ya había columnas guardadas → es un archivo DIFERENTE
      // Limpiar mapeos porque ya no son válidos para las nuevas columnas
      if (currentColumns.length > 0) {
        console.log('⚠️ Archivo diferente detectado - limpiando mapeos obsoletos');
        setMapperData({
          originalColumns: newColumns,
          mappings: {},
          confidences: {},
          appliedToBackend: false
        });
      } else {
        // Primera carga de columnas → mantener mapeos si existen
        setMapperData(prev => ({
          ...prev,
          originalColumns: newColumns
        }));
      }
    }
  }, [originalFields, initialDataLoaded]);

  // ============================================
  // FUNCIÓN: Cargar mapeo desde el backend
  // ============================================
  const fetchMapeoFromBackend = async () => {
    if (!executionId) return;

    setLoading(true);
    try {
      console.log(`🌐 Obteniendo mapeo desde backend (${fileType})...`);

      if (fileType === 'sumas_saldos') {
        let statusResult = await importService.getSumasSaldosMapeoStatus(executionId);

        // Si no hay mapeo o está vacío, iniciar el proceso automático
        if (!statusResult.success || !statusResult.data.mapping || Object.keys(statusResult.data.mapping).length === 0) {
          console.log('🚀 Iniciando proceso automático de mapeo...');

          const startMapeoResult = await importService.startSumasSaldosMapeo(executionId);

          if (startMapeoResult.success) {
            // Polling para esperar completación
            let attempts = 0;
            const maxAttempts = 30;
            let mapeoCompleted = false;

            while (!mapeoCompleted && attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 2000));
              statusResult = await importService.getSumasSaldosMapeoStatus(executionId);
              attempts++;

              if (statusResult.success && statusResult.data.status) {
                const status = statusResult.data.status.toLowerCase();
                console.log(`🔄 Estado: ${status} (${attempts}/${maxAttempts})`);

                if (status === 'completed') {
                  mapeoCompleted = true;
                  break;
                } else if (status === 'failed' || status === 'error') {
                  console.error('❌ Mapeo falló');
                  break;
                }
              }
            }
          }
        }

        // Cargar el mapeo
        statusResult = await importService.getSumasSaldosMapeoStatus(executionId);

        if (statusResult.success && statusResult.data.mapping) {
          const backendMapping = statusResult.data.mapping || {};
          const mappings = {};

          Object.entries(backendMapping).forEach(([bdField, excelColumn]) => {
            if (excelColumn) {
              mappings[excelColumn] = bdField;
            }
          });

          // Actualizar estado unificado
          setMapperData(prev => ({
            ...prev,
            mappings: mappings,
            confidences: {}
          }));

          console.log('✅ Automapeo de Sumas y Saldos cargado:', Object.keys(mappings).length, 'mapeos');
        }

      } else {
        // Libro Diario
        const fieldsResult = await importService.getFieldsMapping(executionId);

        if (fieldsResult.success) {
          const backendMappings = fieldsResult.data.mapped_fields || {};
          const mappings = {};
          const confidences = {};

          Object.entries(backendMappings).forEach(([standardField, mapping]) => {
            if (mapping.mapped_column) {
              mappings[mapping.mapped_column] = standardField;

              if (mapping.confidence !== undefined) {
                confidences[mapping.mapped_column] = mapping.confidence;
              }
            }
          });

          // Actualizar estado unificado
          setMapperData(prev => ({
            ...prev,
            mappings: mappings,
            confidences: confidences
          }));

          console.log('✅ Automapeo de Libro Diario cargado:', Object.keys(mappings).length, 'mapeos');
        }
      }
      
    } catch (error) {
      console.error('Error al cargar mapeo:', error);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // FUNCIÓN: Cambiar un mapeo de columna
  // ============================================
  const handleMappingChange = (originalField, targetField) => {
    setMapperData(prev => {
      const newMappings = { ...prev.mappings };

      // Si el targetField ya estaba mapeado a otra columna, eliminarlo
      if (targetField) {
        const previousMapping = Object.entries(newMappings).find(
          ([key, value]) => value === targetField && key !== originalField
        );

        if (previousMapping) {
          delete newMappings[previousMapping[0]];
          console.log(`🔄 Removiendo mapeo anterior: ${previousMapping[0]} -> ${targetField}`);
        }
      }

      // Aplicar el nuevo mapeo (o eliminar si está vacío)
      if (targetField) {
        newMappings[originalField] = targetField;
        console.log(`✅ Nuevo mapeo: ${originalField} -> ${targetField}`);
      } else {
        delete newMappings[originalField];
        console.log(`🗑️ Mapeo eliminado: ${originalField}`);
      }

      return {
        ...prev,
        mappings: newMappings,
        appliedToBackend: false // Resetear porque cambió el mapeo
      };
    });
  };

  // ============================================
  // FUNCIÓN: Aplicar mapeos al backend
  // ============================================
  const handleApplyMappings = async () => {
    if (!executionId) {
      if (onMappingChange) {
        onMappingChange(mapperData.mappings);
      }
      return;
    }

    setLoading(true);
    try {
      const mappings = [];

      // Preparar mapeos para enviar al backend
      Object.entries(mapperData.mappings).forEach(([sourceColumn, standardField]) => {
        if (standardField) {
          const mappingObj = {
            column_name: sourceColumn,
            selected_field: standardField,
            force_override: true  // SIEMPRE true cuando el usuario aplica manualmente
          };

          if (fileType === 'libro_diario' && mapperData.confidences[sourceColumn] !== undefined) {
            mappingObj.confidence = mapperData.confidences[sourceColumn];
          } else if (fileType === 'libro_diario') {
            mappingObj.confidence = 1.0; // Mapeo manual = 100% confianza
          }

          mappings.push(mappingObj);
        }
      });

      if (mappings.length === 0) {
        console.log('⚠️ No hay mapeos para enviar');
        setLoading(false);
        return;
      }

      console.log(`📤 Enviando ${mappings.length} mapeos al backend`);

      let result;

      if (fileType === 'sumas_saldos') {
        result = await importService.applySumasSaldosManualMapping(executionId, mappings);
      } else {
        result = await importService.applyManualMapping(executionId, mappings);
      }

      if (result.success) {
        console.log('✅ Mapeo aplicado exitosamente');

        // Marcar como aplicado
        const storageKey = fileType === 'sumas_saldos'
          ? `mappingApplied_${executionId}-ss`
          : `mappingApplied_${executionId}`;

        sessionStorage.setItem(storageKey, 'true');

        // Actualizar estado
        setMapperData(prev => ({
          ...prev,
          appliedToBackend: true
        }));

        if (onMappingChange) {
          onMappingChange(mapperData.mappings);
        }
      } else {
        console.error('❌ Error al aplicar mapeo:', result.error);
        alert('Error al aplicar el mapeo:\n\n' + (result.error || 'Error desconocido'));
      }
    } catch (error) {
      console.error('❌ Error applying mappings:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Error desconocido';
      alert('Error al aplicar el mapeo:\n\n' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getMappedCount = () => {
    return Object.values(mapperData.mappings).filter(v => v).length;
  };

  const getRequiredMappedCount = () => {
    const requiredFields = Object.entries(databaseFields)
      .filter(([_, info]) => info.required && (!info.fileTypes || info.fileTypes.includes(fileType)));

    const mappedRequired = requiredFields.filter(([field]) =>
      Object.values(mapperData.mappings).includes(field)
    ).length;

    return {
      mapped: mappedRequired,
      total: requiredFields.length
    };
  };

  const isFieldMapped = (databaseField) => {
    return Object.values(mapperData.mappings).includes(databaseField);
  };

  const getFilteredDatabaseFields = () => {
    return Object.entries(databaseFields).filter(([field, fieldInfo]) => {
      if (fieldInfo.fileTypes && !fieldInfo.fileTypes.includes(fileType)) {
        return false;
      }

      if (fieldInfo.visible === false && !isFieldMapped(field)) {
        console.log(`Ocultando campo no mapeado: ${field}`);
        return false;
      }
      
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return field.toLowerCase().includes(searchLower) ||
              fieldInfo.label.toLowerCase().includes(searchLower) ||
              fieldInfo.description.toLowerCase().includes(searchLower);
      }
      
      return true;
    }).sort((a, b) => {
      const [fieldA, infoA] = a;
      const [fieldB, infoB] = b;
      
      // PASO 1: Ordenar por si está mapeado (mapeados primero)
      const isMappedA = isFieldMapped(fieldA);
      const isMappedB = isFieldMapped(fieldB);
      
      if (isMappedA && !isMappedB) return -1;
      if (!isMappedA && isMappedB) return 1;
      
      // PASO 2: Si ambos están mapeados O ambos NO están mapeados, ordenar por 'order'
      if (infoA.order !== undefined && infoB.order !== undefined) {
        return infoA.order - infoB.order;
      }
      
      if (infoA.order !== undefined && infoB.order === undefined) return -1;
      if (infoA.order === undefined && infoB.order !== undefined) return 1;
      
      // PASO 3: Si no tienen 'order', ordenar por requerido
      if (infoA.required && !infoB.required) return -1;
      if (!infoA.required && infoB.required) return 1;
      
      // PASO 4: Si todo lo anterior es igual, ordenar alfabéticamente
      return fieldA.localeCompare(fieldB);
    });
  };

  const getVisibleDatabaseFieldsCount = () => {
    return getFilteredDatabaseFields().length;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'bg-green-100 text-green-800';
    if (confidence >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const getFileTypeTitle = () => {
    return fileType === 'libro_diario' 
      ? 'Mapeo de Campos - Libro Diario'
      : 'Mapeo de Campos - Sumas y Saldos';
  };

  //  FUNCIÓN: Limpiar mapeos (restaurar desde backend si es necesario)
  const handleClearMappings = () => {
    setMapperData(prev => ({
      ...prev,
      mappings: {},
      confidences: {},
      appliedToBackend: false
    }));
    console.log('🧹 Mapeos limpiados');
  };

  // ✅ CORREGIDO: SIEMPRE priorizar columnas del archivo ACTUAL (originalFields)
  // Solo usar columnas guardadas (mapperData.originalColumns) como fallback
  const columnsToShow = (originalFields && originalFields.length > 0)
    ? originalFields  // ✅ PRIORIDAD: Columnas del archivo ACTUAL
    : mapperData.originalColumns;  // Fallback: Columnas guardadas

  if (!columnsToShow || columnsToShow.length === 0) {
    if (Object.keys(mapperData.mappings).length > 0) {
      console.log('⏳ Esperando columnas...');
    }
    return null;
  }

  const requiredStats = getRequiredMappedCount();
  const filteredDatabaseFields = getFilteredDatabaseFields();
  const visibleFieldsCount = getVisibleDatabaseFieldsCount();

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div 
        className="px-4 py-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h3 className="text-base font-semibold text-gray-900">
                {getFileTypeTitle()}
              </h3>
              
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {getMappedCount()}/{visibleFieldsCount} mapeados
                </span>
                {fileType === 'libro_diario' && (
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    requiredStats.mapped === requiredStats.total 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {requiredStats.mapped}/{requiredStats.total} obligatorios
                  </span>
                )}
                {loading && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <svg className="animate-spin w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    Procesando
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2 ml-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleApplyMappings();
              }}
              disabled={loading || mapperData.appliedToBackend}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={mapperData.appliedToBackend ? 'Mapeo ya aplicado. Modifica una columna para volver a mapear.' : 'Aplicar el mapeo al archivo'}
            >
              {loading ? 'Aplicando...' : mapperData.appliedToBackend ? 'Mapeo Aplicado ✓' : 'Aplicar Mapeo'}
            </button>
            
            <svg 
              className={`w-5 h-5 text-gray-400 transform transition-transform ${
                isOpen ? 'rotate-180' : ''
              }`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Contenido del mapeo */}
      {isOpen && (
        <div className="px-4 py-3">
          {/* Buscador */}
          <div className="mb-3">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
                <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                className="block w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md leading-4 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-purple-500 focus:border-purple-500 text-xs"
                placeholder="Buscar campos de base de datos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Tabla de mapeo */}
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-3 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campo BD (Destino)
                  </th>
                  <th className="px-3 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campo Origen
                  </th>
                  {fileType === 'libro_diario' && (
                    <th className="px-3 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confianza
                    </th>
                  )}
                  <th className="px-3 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Oblig.
                  </th>
                  <th className="px-3 py-1.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Descripción
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredDatabaseFields.map(([databaseField, fieldInfo]) => {
                  const mappedOriginalField = Object.entries(mapperData.mappings)
                    .find(([_, mappedField]) => mappedField === databaseField)?.[0] || '';
                  
                  const isMapped = isFieldMapped(databaseField);
                  
                  return (
                    <tr 
                      key={databaseField} 
                      className={`
                        ${isMapped ? 'bg-gray-50' : 'bg-white'} 
                        hover:bg-gray-100 
                        transition-colors
                      `}
                    >
                      <td className="px-3 py-1.5 whitespace-nowrap text-sm font-medium text-gray-900">
                        <div className="flex items-center space-x-2">
                          {isMapped && (
                            <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          )}
                          <span>{databaseField}</span>
                        </div>
                      </td>
                      <td className="px-3 py-1.5">
                        <div className="flex items-center space-x-2">
                          <select
                            value={mappedOriginalField || ''}
                            onChange={(e) => handleMappingChange(e.target.value, databaseField)}
                            className="block w-full px-2 py-1 text-sm border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                          >
                            <option value="">-- Seleccionar --</option>
                            {columnsToShow.map((originalField) => {
                              // Ocultar columnas ya mapeadas a otros campos, excepto la actual
                              const isAlreadyMapped = Object.entries(mapperData.mappings).some(
                                ([col, field]) => col === originalField && field !== databaseField
                              );
                              if (isAlreadyMapped && originalField !== mappedOriginalField) {
                                return null;
                              }
                              return (
                                <option
                                  key={originalField}
                                  value={originalField}
                                >
                                  {originalField}
                                </option>
                              );
                            })}
                          </select>
                          {mappedOriginalField && (
                            <button
                              onClick={() => handleMappingChange(mappedOriginalField, '')}
                              className="flex-shrink-0 p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                              title="Quitar mapeo"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </td>
                      {fileType === 'libro_diario' && (
                        <td className="px-3 py-1.5 whitespace-nowrap">
                          {mappedOriginalField && mapperData.confidences[mappedOriginalField] !== undefined && (
                            <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(mapperData.confidences[mappedOriginalField])}`}>
                              {Math.round(mapperData.confidences[mappedOriginalField] * 100)}%
                            </span>
                          )}
                        </td>
                      )}
                      <td className="px-3 py-1.5 whitespace-nowrap">
                        {fieldInfo.required && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Sí
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-1.5">
                        <div className="text-xs text-gray-500 max-w-xs truncate" title={fieldInfo.description}>
                          {fieldInfo.description}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Botones de acción */}
          <div className="mt-3">
            <div className="mt-3 flex justify-end">
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleClearMappings}
                  disabled={loading}
                  className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                >
                  Limpiar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldMapper;