// frontend/src/components/FieldMapper/FieldMapper.jsx 
import React, { useState, useEffect } from 'react';
import importService from '../../services/importService';
// Importar los JSONs de campos
import journalEntriesMapping from '../../config/journal_entries_table_mapping.json';
import trialBalanceMapping from '../../config/trial_balance_table_mapping.json';

const FieldMapper = ({ originalFields, onMappingChange, isOpen, onToggle, fileType = 'libro_diario', executionId }) => {
  const [fieldMappings, setFieldMappings] = useState({});
  const [fieldConfidences, setFieldConfidences] = useState({});
  const [originalBackendMappings, setOriginalBackendMappings] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [mapeoData, setMapeoData] = useState(null);
  // Estados para controlar el botón de mapeo
  const [mappingApplied, setMappingApplied] = useState(false);
  const [initialMappingsSnapshot, setInitialMappingsSnapshot] = useState({});
  // Estado local para las columnas originales (para persistir después de recargar)
  const [localOriginalFields, setLocalOriginalFields] = useState([]);

  // Claves para sessionStorage
  const getStorageKey = (suffix) => `fieldmapper_${executionId}_${suffix}`;

  // Guardar mapeo en sessionStorage
  const saveMappingToStorage = (mappings, confidences = {}) => {
    try {
      const dataToSave = {
        mappings: mappings,
        confidences: confidences
      };
      sessionStorage.setItem(getStorageKey('fieldMappings'), JSON.stringify(dataToSave));
      sessionStorage.setItem(getStorageKey('timestamp'), Date.now().toString());
    } catch (error) {
      console.warn('Could not save field mappings to sessionStorage:', error);
    }
  };

  // Guardar columnas originales en sessionStorage
  const saveOriginalFieldsToStorage = (fields) => {
    try {
      sessionStorage.setItem(getStorageKey('originalFields'), JSON.stringify(fields));
      console.log('💾 Columnas originales guardadas en sessionStorage:', fields);
    } catch (error) {
      console.warn('Could not save original fields to sessionStorage:', error);
    }
  };

  // Cargar columnas originales desde sessionStorage
  const loadOriginalFieldsFromStorage = () => {
    try {
      const savedFields = sessionStorage.getItem(getStorageKey('originalFields'));
      if (savedFields) {
        const fields = JSON.parse(savedFields);
        console.log('📦 Columnas originales restauradas desde sessionStorage:', fields);
        return fields;
      }
    } catch (error) {
      console.warn('Could not load original fields from sessionStorage:', error);
    }
    return null;
  };

  // Cargar mapeo desde sessionStorage
  const loadMappingFromStorage = () => {
    try {
      const savedMappings = sessionStorage.getItem(getStorageKey('fieldMappings'));
      const timestamp = sessionStorage.getItem(getStorageKey('timestamp'));

      if (savedMappings && timestamp) {
        const timeDiff = Date.now() - parseInt(timestamp);
        const maxAge = 30 * 60 * 1000; // 30 minutos

        if (timeDiff < maxAge) {
          const parsedData = JSON.parse(savedMappings);
          console.log('📦 Restaurando mapeo desde sessionStorage:', parsedData);
          console.log('⚠️ IMPORTANTE: Mapeos cargados pero NO marcar como aplicados (esperando acción del usuario)');
          // Soportar formato antiguo y nuevo
          if (parsedData.mappings) {
            return parsedData; // Formato nuevo con mappings y confidences
          } else {
            return { mappings: parsedData, confidences: {} }; // Formato antiguo
          }
        }
      }
    } catch (error) {
      console.warn('Could not load field mappings from sessionStorage:', error);
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

  // Efecto para manejar originalFields: guardar cuando llegan y restaurar si no hay
  useEffect(() => {
    if (originalFields && originalFields.length > 0) {
      // Si llegan originalFields por prop, guardarlos y usarlos
      setLocalOriginalFields(originalFields);
      saveOriginalFieldsToStorage(originalFields);
      console.log('✅ Columnas originales recibidas y guardadas:', originalFields.length);
    }
  }, [originalFields]);

  // Efecto separado para restaurar columnas al montar (solo una vez)
  useEffect(() => {
    if (executionId && localOriginalFields.length === 0) {
      // Intentar cargar columnas desde sessionStorage
      const savedFields = loadOriginalFieldsFromStorage();
      if (savedFields && savedFields.length > 0) {
        setLocalOriginalFields(savedFields);
        console.log('🔄 Columnas originales restauradas desde sessionStorage:', savedFields.length);
      } else {
        console.log('⚠️ No se encontraron columnas guardadas en sessionStorage');
      }
    }
  }, [executionId]); // Solo depende de executionId, se ejecuta al montar

  useEffect(() => {
    // Intentar cargar mapeo incluso si no hay columnas todavía
    // porque el mapeo puede estar guardado en sessionStorage
    if (isOpen && executionId) {
      loadMapeoData();
    }
  }, [isOpen, executionId, localOriginalFields]);

  useEffect(() => {
    if (Object.keys(fieldMappings).length > 0) {
      saveMappingToStorage(fieldMappings, fieldConfidences);
    }
  }, [fieldMappings, fieldConfidences]);

  // Verificar si el mapeo ya fue aplicado previamente (al cargar el componente)
  useEffect(() => {
    if (!executionId) return;

    const storageKey = fileType === 'sumas_saldos'
      ? `mappingApplied_${executionId}-ss`
      : `mappingApplied_${executionId}`;

    const mappingAppliedFlag = sessionStorage.getItem(storageKey);
    if (mappingAppliedFlag === 'true') {
      setMappingApplied(true);
      console.log('🔒 Mapeo fue aplicado previamente, botón deshabilitado');
    }
  }, [executionId, fileType]);

  // Función para cargar los datos del mapeo
  const loadMapeoData = async () => {
    if (!executionId) return;
    
    setLoading(true);
    try {
      const savedData = loadMappingFromStorage();
      if (savedData && savedData.mappings && Object.keys(savedData.mappings).length > 0) {
        console.log('📦 Cargando mapeo desde sessionStorage');
        setFieldMappings(savedData.mappings);
        setFieldConfidences(savedData.confidences || {});

        // También actualizar originalBackendMappings para el botón "Auto mapeo"
        if (fileType === 'libro_diario') {
          setOriginalBackendMappings({
            mappings: savedData.mappings,
            confidences: savedData.confidences || {}
          });
        } else {
          setOriginalBackendMappings(savedData.mappings);
        }
        console.log('💾 originalBackendMappings actualizado desde sessionStorage');

        // ❌ NO guardar flag de mapeo aplicado aquí
        // El flag solo debe guardarse cuando el usuario hace click en "Aplicar Mapeo"
        console.log('ℹ️ Mapeos cargados en la tabla, pero flag mappingApplied NO modificado (esperando acción del usuario)');

        setLoading(false);
        return;
      }

      console.log(`🔍 Obteniendo mapeo desde el backend (${fileType})...`);

      if (fileType === 'sumas_saldos') {
        let statusResult = await importService.getSumasSaldosMapeoStatus(executionId);

        // Si no hay mapeo o está vacío, iniciar el proceso automático
        if (!statusResult.success || !statusResult.data.mapping || Object.keys(statusResult.data.mapping).length === 0) {
          console.log('🚀 No se encontró mapeo de Sumas y Saldos, iniciando proceso automático...');

          const startMapeoResult = await importService.startSumasSaldosMapeo(executionId);

          if (startMapeoResult.success) {
            console.log('✅ Proceso de mapeo iniciado, esperando completación...');

            // Polling para esperar a que el mapeo se complete
            let attempts = 0;
            const maxAttempts = 30; // 30 intentos * 2 segundos = 1 minuto máximo
            let mapeoCompleted = false;

            while (!mapeoCompleted && attempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 2000)); // Esperar 2 segundos

              statusResult = await importService.getSumasSaldosMapeoStatus(executionId);
              attempts++;

              if (statusResult.success && statusResult.data.status) {
                const status = statusResult.data.status.toLowerCase();
                console.log(`🔄 Intento ${attempts}/${maxAttempts} - Estado: ${status}`);

                if (status === 'completed') {
                  mapeoCompleted = true;
                  console.log('✅ Mapeo de Sumas y Saldos completado');
                  break;
                } else if (status === 'failed' || status === 'error') {
                  console.error('❌ Mapeo de Sumas y Saldos falló:', statusResult.data.error);
                  break;
                }
              }
            }

            if (!mapeoCompleted) {
              console.warn('⚠️ Timeout esperando mapeo de Sumas y Saldos');
            }
          } else {
            console.error('❌ Error al iniciar mapeo de Sumas y Saldos:', startMapeoResult.error);
          }
        }

        // Intentar cargar el mapeo nuevamente después del proceso
        statusResult = await importService.getSumasSaldosMapeoStatus(executionId);

        if (statusResult.success && statusResult.data.mapping) {
          console.log('📋 Mapeo de Sumas y Saldos encontrado:', statusResult.data.mapping);

          const backendMapping = statusResult.data.mapping || {};
          const frontendMappings = {};

          Object.entries(backendMapping).forEach(([bdField, excelColumn]) => {
            if (excelColumn) {
              frontendMappings[excelColumn] = bdField;
            }
          });

          setFieldMappings(frontendMappings);
          setOriginalBackendMappings(frontendMappings);

          // IMPORTANTE: Guardar el automapeo en sessionStorage para persistir al recargar
          saveMappingToStorage(frontendMappings, {});
          console.log('💾 Automapeo de Sumas y Saldos guardado en sessionStorage');

          // ❌ NO guardar flag de mapeo aplicado al cargar automapeo del backend
          // Los mapeos del backend son AUTOMAPEOS, no mapeos aplicados manualmente
          console.log('ℹ️ Automapeo de Sumas y Saldos cargado en la tabla, pero flag mappingApplied NO modificado');
          console.log('   El usuario debe hacer click en "Aplicar Mapeo" para activar el preview azul');
        } else {
          console.log('⚠️ No se pudo cargar el mapeo de Sumas y Saldos');
        }

      } else {
        const fieldsResult = await importService.getFieldsMapping(executionId);

        if (fieldsResult.success) {
          console.log('Respuesta del backend:', fieldsResult.data);
          setMapeoData(fieldsResult.data);

          const backendMappings = fieldsResult.data.mapped_fields || {};
          const frontendMappings = {};
          const confidences = {};

          Object.entries(backendMappings).forEach(([standardField, mapping]) => {
            if (mapping.mapped_column) {
              frontendMappings[mapping.mapped_column] = standardField;

              if (mapping.confidence !== undefined) {
                confidences[mapping.mapped_column] = mapping.confidence;
              }

              console.log(`Mapeando: "${mapping.mapped_column}" -> "${standardField}"${
                mapping.confidence !== undefined ? ` (confidence: ${mapping.confidence})` : ''
              }`);
            }
          });

          console.log('📋 Mapeo final del frontend:', frontendMappings);
          console.log('🎯 Confidences capturadas:', confidences);

          setFieldMappings(frontendMappings);
          setFieldConfidences(confidences);
          setOriginalBackendMappings({ mappings: frontendMappings, confidences });

          // IMPORTANTE: Guardar el automapeo en sessionStorage para persistir al recargar
          saveMappingToStorage(frontendMappings, confidences);
          console.log('💾 Automapeo del Libro Diario guardado en sessionStorage');

          // ❌ NO guardar flag de mapeo aplicado al cargar automapeo del backend
          // Los mapeos del backend son AUTOMAPEOS, no mapeos aplicados manualmente
          console.log('ℹ️ Automapeo del Libro Diario cargado en la tabla, pero flag mappingApplied NO modificado');
          console.log('   El usuario debe hacer click en "Aplicar Mapeo" para activar el preview azul');
        }
      }
      
    } catch (error) {
      console.error('Error al cargar mapeo:', error);
    } finally {
      setLoading(false);
    }
  };

  //  FUNCIÓN CORREGIDA: Permite re-mapear columnas
  const handleMappingChange = (originalField, targetField) => {
    // PASO 1: Crear copia del estado actual
    const newMappings = { ...fieldMappings };

    // PASO 2: Si el targetField ya estaba mapeado a otro originalField,
    // eliminamos ese mapeo anterior
    if (targetField) {
      // Buscar si targetField ya estaba asignado a otra columna
      const previousMapping = Object.entries(fieldMappings).find(
        ([key, value]) => value === targetField && key !== originalField
      );

      // Si existía un mapeo anterior diferente, lo eliminamos
      if (previousMapping) {
        delete newMappings[previousMapping[0]];
        console.log(`🔄 Removiendo mapeo anterior: ${previousMapping[0]} -> ${targetField}`);
      }
    }

    // PASO 3: Aplicar el nuevo mapeo (o eliminar si targetField está vacío)
    if (targetField) {
      newMappings[originalField] = targetField;
      console.log(` Nuevo mapeo: ${originalField} -> ${targetField}`);
    } else {
      // Si targetField está vacío, eliminar el mapeo
      delete newMappings[originalField];
      console.log(`🗑️ Mapeo eliminado: ${originalField}`);
    }

    setFieldMappings(newMappings);

    // PASO 4: Si el mapeo fue aplicado previamente, habilitar el botón nuevamente
    if (mappingApplied) {
      console.log('🔓 Mapeo modificado después de aplicar, habilitando botón de mapeo');
      setMappingApplied(false);
    }
  };

  const handleApplyMappings = async () => {
    if (!executionId) {
      if (onMappingChange) {
        onMappingChange(fieldMappings);
      }
      return;
    }

    setLoading(true);
    try {
      const mappings = [];

      // Cuando el usuario hace click en "Aplicar Mapeo", es una acción EXPLÍCITA
      // Siempre usar force_override=true porque el usuario está confirmando el mapeo
      Object.entries(fieldMappings).forEach(([sourceColumn, standardField]) => {
        if (standardField) {
          const mappingObj = {
            column_name: sourceColumn,
            selected_field: standardField,
            force_override: true  // SIEMPRE true cuando el usuario aplica manualmente
          };

          if (fileType === 'libro_diario' && fieldConfidences[sourceColumn] !== undefined) {
            mappingObj.confidence = fieldConfidences[sourceColumn];
          } else if (fileType === 'libro_diario') {
            mappingObj.confidence = 1.0; // Mapeo manual = 100% confianza
          }

          mappings.push(mappingObj);
        }
      });

      if (mappings.length === 0) {
        console.log('No hay mapeos para enviar al backend');
        if (onMappingChange) {
          onMappingChange(fieldMappings);
        }
        setLoading(false);
        return;
      }

      console.log(`📤 Enviando ${mappings.length} mapeos al backend con force_override=true`);

      let result;

      if (fileType === 'sumas_saldos') {
        result = await importService.applySumasSaldosManualMapping(executionId, mappings);
      } else {
        result = await importService.applyManualMapping(executionId, mappings);
      }
      
      if (result.success) {
        console.log(' Mapeo aplicado exitosamente');

        // Marcar el mapeo como explícitamente aplicado en sessionStorage
        try {
          // CORREGIDO: Guardar con sufijo correcto según tipo de archivo
          const storageKey = fileType === 'sumas_saldos'
            ? `mappingApplied_${executionId}-ss`  // Con sufijo -ss para Sumas y Saldos
            : `mappingApplied_${executionId}`;    // Sin sufijo para Libro Diario

          sessionStorage.setItem(storageKey, 'true');
          console.log(`✅ Guardado flag de mapeo aplicado: ${storageKey}`);
        } catch (error) {
          console.warn('Could not save mapping applied flag:', error);
        }

        // Actualizar el backup con los nuevos mapeos aplicados
        if (fileType === 'libro_diario') {
          setOriginalBackendMappings({
            mappings: fieldMappings,
            confidences: fieldConfidences
          });
        } else {
          setOriginalBackendMappings(fieldMappings);
        }

        // Deshabilitar el botón de mapeo después de aplicar exitosamente
        setMappingApplied(true);
        setInitialMappingsSnapshot({ ...fieldMappings });
        console.log('🔒 Botón de mapeo deshabilitado después de aplicar exitosamente');

        if (onMappingChange) {
          onMappingChange(fieldMappings);
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
    return Object.values(fieldMappings).filter(v => v).length;
  };

  const getRequiredMappedCount = () => {
    const requiredFields = Object.entries(databaseFields)
      .filter(([_, info]) => info.required && (!info.fileTypes || info.fileTypes.includes(fileType)));
    
    const mappedRequired = requiredFields.filter(([field]) => 
      Object.values(fieldMappings).includes(field)
    ).length;

    return {
      mapped: mappedRequired,
      total: requiredFields.length
    };
  };

  const isFieldMapped = (databaseField) => {
    return Object.values(fieldMappings).includes(databaseField);
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

  const handleRestoreBackendMapping = () => {
    if (!originalBackendMappings || Object.keys(originalBackendMappings).length === 0) {
      alert('No hay mapeo automático del backend disponible para restaurar');
      return;
    }

    if (fileType === 'libro_diario' && originalBackendMappings.mappings) {
      setFieldMappings(originalBackendMappings.mappings);
      setFieldConfidences(originalBackendMappings.confidences || {});

      const withConfidence = Object.keys(originalBackendMappings.confidences || {}).length;
      console.log(
        ` Restaurados ${Object.keys(originalBackendMappings.mappings).length} mapeos del backend` +
        (withConfidence > 0 ? ` (${withConfidence} con nivel de confianza)` : '')
      );
    } else {
      setFieldMappings(originalBackendMappings);
      console.log(` Restaurados ${Object.keys(originalBackendMappings).length} mapeos del backend`);
    }

    // Habilitar el botón de mapeo al restaurar, porque se cambió el estado
    setMappingApplied(false);
    console.log('🔓 Botón de mapeo habilitado al restaurar mapeo automático');
  };

  // Usar localOriginalFields en lugar de originalFields
  const fieldsToUse = localOriginalFields.length > 0 ? localOriginalFields : originalFields || [];

  // Log para debugging
  console.log('🔍 FieldMapper render:', {
    localOriginalFieldsCount: localOriginalFields.length,
    originalFieldsCount: originalFields?.length || 0,
    fieldsToUseCount: fieldsToUse.length,
    fieldMappingsCount: Object.keys(fieldMappings).length
  });

  if (!fieldsToUse || fieldsToUse.length === 0) {
    // Si tenemos mapeos pero no columnas, mostrar un mensaje temporal
    if (Object.keys(fieldMappings).length > 0) {
      console.log('⏳ Mapeos disponibles pero esperando columnas...');
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
              disabled={loading || mappingApplied}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={mappingApplied ? 'Mapeo ya aplicado. Modifica una columna para volver a mapear.' : 'Aplicar el mapeo al archivo'}
            >
              {loading ? 'Aplicando...' : mappingApplied ? 'Mapeo Aplicado ✓' : 'Aplicar Mapeo'}
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
                  const mappedOriginalField = Object.entries(fieldMappings)
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
                            {fieldsToUse.map((originalField) => {
                              // Ocultar columnas ya mapeadas a otros campos, excepto la actual
                              const isAlreadyMapped = Object.entries(fieldMappings).some(
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
                          {mappedOriginalField && fieldConfidences[mappedOriginalField] !== undefined && (
                            <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(fieldConfidences[mappedOriginalField])}`}>
                              {Math.round(fieldConfidences[mappedOriginalField] * 100)}%
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
                  onClick={() => {
                    setFieldMappings({});
                    setFieldConfidences({});
                    setMappingApplied(false);
                    console.log('🧹 Mapeos limpiados (el backup del backend se mantiene)');
                    console.log('🔓 Botón de mapeo habilitado al limpiar');
                  }}
                  disabled={loading}
                  className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                >
                  Limpiar
                </button>
                
                <button
                  onClick={handleRestoreBackendMapping}
                  disabled={loading || !originalBackendMappings || Object.keys(originalBackendMappings).length === 0}
                  className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                  title={!originalBackendMappings || Object.keys(originalBackendMappings).length === 0 ? 'No hay mapeo del backend disponible' : 'Restaurar mapeo automático del backend'}
                >
                  Auto mapeo
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