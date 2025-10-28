// frontend/src/components/ValidationPhases/ValidationPhases.jsx
import React, { useState, useEffect } from 'react';
import importService from '../../services/importService';

const ValidationPhases = ({ fileType, executionId, period, onComplete, isMappingApplied = true }) => {
  // Claves para sessionStorage
  const getStorageKey = (suffix) => `validation_${executionId}_${fileType}_${suffix}`;

  // Función para cargar estado desde sessionStorage
  const loadStateFromStorage = () => {
    try {
      const savedPhases = sessionStorage.getItem(getStorageKey('phases'));
      const savedCompleted = sessionStorage.getItem(getStorageKey('allCompleted'));
      const savedProgress = sessionStorage.getItem(getStorageKey('progressData'));
      const savedExpanded = sessionStorage.getItem(getStorageKey('isExpanded'));

      return {
        phases: savedPhases ? JSON.parse(savedPhases) : null,
        allCompleted: savedCompleted === 'true',
        progressData: savedProgress ? JSON.parse(savedProgress) : null,
        isExpanded: savedExpanded === 'true'
      };
    } catch (error) {
      console.warn('Could not load validation state from sessionStorage:', error);
      return { phases: null, allCompleted: false, progressData: null, isExpanded: false };
    }
  };

  // Función para guardar estado en sessionStorage
  const saveStateToStorage = (phasesToSave, completedStatus, progress) => {
    try {
      sessionStorage.setItem(getStorageKey('phases'), JSON.stringify(phasesToSave));
      sessionStorage.setItem(getStorageKey('allCompleted'), completedStatus.toString());
      sessionStorage.setItem(getStorageKey('progressData'), JSON.stringify(progress));
      sessionStorage.setItem(getStorageKey('timestamp'), Date.now().toString());
    } catch (error) {
      console.warn('Could not save validation state to sessionStorage:', error);
    }
  };

  const savedState = loadStateFromStorage();

  const [isExpanded, setIsExpanded] = useState(savedState.isExpanded);
  const [phases, setPhases] = useState(savedState.phases || []);
  const [isValidating, setIsValidating] = useState(false);
  const [allCompleted, setAllCompleted] = useState(savedState.allCompleted);
  const [validationError, setValidationError] = useState(null);

  // Calcular el total de fases según el tipo de archivo
  const getTotalPhases = () => {
    if (fileType === 'libro_diario') return 4;
    if (fileType === 'sumas_saldos') return 1;
    return 4; // default
  };

  const [progressData, setProgressData] = useState(savedState.progressData || {
    completed: 0,
    total: getTotalPhases()
  });

  const phaseDefinitions = {
    libro_diario: [
      {
        id: 1,
        name: "Validaciones de Formato",
        validations: [
          "Fechas con formato correcto",
          "Horas con formato correcto",
          "Importes con formato correcto"
        ]
      },
      {
        id: 2,
        name: "Validaciones de Identificadores",
        validations: [
          "Identificadores de asientos Ãºnicos",
          "Identificadores de apuntes secuenciales"
        ]
      },
      {
        id: 3,
        name: "Validaciones Temporales",
        validations: [
          "Fecha contable en el período",
          "Fecha registro excede el Período contable"
        ]
      },
      {
        id: 4,
        name: "Validaciones de Integridad Contable",
        validations: [
          "Asientos balanceados"
        ]
      }
    ],
    sumas_saldos: [
      {
        id: 1,
        name: "Validaciones de Formato",
        validations: [
          "Fechas con formato correcto",
          "Horas con formato correcto",
          "Importes con formato correcto"
        ]
      }
    ]
  };

  const currentPhaseDefinitions = phaseDefinitions[fileType] || [];

  // Inicializar las fases con estado pendiente solo si no hay estado guardado
  useEffect(() => {
    if (phases.length === 0) {
      const initialPhases = currentPhaseDefinitions.map(phase => ({
        ...phase,
        status: 'pending'
      }));
      setPhases(initialPhases);
    }
  }, [fileType]);

  // Guardar estado cuando cambie
  useEffect(() => {
    if (phases.length > 0) {
      saveStateToStorage(phases, allCompleted, progressData);
    }
  }, [phases, allCompleted, progressData]);

  // Guardar estado de expansión
  useEffect(() => {
    try {
      sessionStorage.setItem(getStorageKey('isExpanded'), isExpanded.toString());
    } catch (error) {
      console.warn('Could not save isExpanded state:', error);
    }
  }, [isExpanded]);

  // Detectar cuando se aplica un nuevo mapeo y resetear el estado de validación
  useEffect(() => {
    // Verificar periódicamente si se aplicó un nuevo mapeo
    const interval = setInterval(() => {
      try {
        const mappingAppliedAt = sessionStorage.getItem(getStorageKey('mappingAppliedAt'));

        // ✅ CORREGIDO: Si hay timestamp de nuevo mapeo, resetear SIEMPRE
        // (no importa si la validación estaba completada o en progreso)
        if (mappingAppliedAt) {
          // Verificar si hay alguna fase que no esté en estado 'pending'
          const hasStartedValidation = phases.some(p => p.status !== 'pending');

          if (hasStartedValidation || allCompleted) {
            console.log('🔄 Nuevo mapeo detectado, reseteando validación...');

            // Resetear todas las fases a pendiente
            const resetPhases = currentPhaseDefinitions.map(phase => ({
              ...phase,
              status: 'pending'
            }));

            setPhases(resetPhases);
            setAllCompleted(false);
            setProgressData({
              completed: 0,
              total: getTotalPhases()
            });
            setValidationError(null);
            setIsExpanded(false);

            // Remover el timestamp para no resetear múltiples veces
            sessionStorage.removeItem(getStorageKey('mappingAppliedAt'));

            console.log('✅ Validación reseteada, botón disponible para re-validar');
          }
        }
      } catch (error) {
        console.warn('Error checking validation state:', error);
      }
    }, 500); // Verificar cada 500ms

    return () => clearInterval(interval);
  }, [phases, allCompleted]); // ✅ Agregado phases a dependencias

  const startValidation = async () => {
    if (!executionId) {
      setValidationError('Falta executionId');
      return;
    }

    // ✅ VALIDACIÓN CONDICIONAL SEGÚN EL TIPO DE ARCHIVO
    // Para libro_diario se necesita period, para sumas_saldos NO
    if (fileType === 'libro_diario' && !period) {
      setValidationError('Faltan datos necesarios: executionId o period');
      return;
    }

    // ✅ CRÍTICO: Limpiar timestamp de mapeo al INICIAR validación
    // Esto previene que el useEffect detecte el timestamp como "nuevo mapeo"
    // cuando en realidad ya se estaba validando
    try {
      sessionStorage.removeItem(getStorageKey('mappingAppliedAt'));
      console.log('🧹 Timestamp de mapeo limpiado al iniciar validación');
    } catch (error) {
      console.warn('Could not clear mapping timestamp:', error);
    }

    setIsValidating(true);
    setIsExpanded(true);
    setValidationError(null);
    
    try {
      let startResult;
      
      // ✅ LLAMAR AL ENDPOINT CORRECTO SEGÚN EL TIPO DE ARCHIVO
      if (fileType === 'sumas_saldos') {
        // Para Sumas y Saldos: usar el endpoint específico
        startResult = await importService.startSumasSaldosValidation(executionId);
      } else {
        // Para Libro Diario: usar el endpoint de validation rules
        startResult = await importService.startValidationRules(executionId, period);
      }
      
      if (!startResult.success) {
        throw new Error(startResult.error || 'Error al iniciar validación');
      }

      // ✅ POLLING DIFERENTE SEGÚN EL TIPO
      if (fileType === 'sumas_saldos') {
        // Polling para Sumas y Saldos (solo tiene fase 1)
        const pollingResult = await importService.pollSumasSaldosValidationProgress(
          executionId,
          {
            intervalMs: 2000,
            timeoutMs: 300000, // 5 minutos
            onProgress: (progressUpdate) => {
              console.log('📊 [FRONTEND] Sumas y Saldos progress update:', progressUpdate);
              console.log('📊 [FRONTEND] Overall status:', progressUpdate.status);
              console.log('📊 [FRONTEND] Phases:', progressUpdate.phases);

              if (progressUpdate.progress) {
                setProgressData(progressUpdate.progress);
                console.log('📊 [FRONTEND] Progress data updated:', progressUpdate.progress);
              }

              // Actualizar estado de la fase 1
              if (progressUpdate.phases && progressUpdate.phases.length > 0) {
                console.log('📊 [FRONTEND] Actualizando fases...');
                const updatedPhases = phases.map(phase => {
                  const phaseUpdate = progressUpdate.phases.find(p => p.phase === phase.id);
                  if (phaseUpdate) {
                    console.log(`📊 [FRONTEND] Fase ${phase.id}: ${phase.status} -> ${phaseUpdate.status}`);
                    return {
                      ...phase,
                      status: phaseUpdate.status
                    };
                  }
                  return phase;
                });
                setPhases(updatedPhases);
                console.log('📊 [FRONTEND] Fases actualizadas:', updatedPhases);
              }
            }
          }
        );

        if (!pollingResult.success) {
          throw new Error(pollingResult.error || 'Error en validación');
        }

        setAllCompleted(true);
        if (onComplete) onComplete();
        
      } else {
        // Polling para Libro Diario (4 fases)
        const pollingResult = await importService.pollValidationRulesProgress(
          executionId,
          {
            intervalMs: 2000,
            timeoutMs: 300000, // 5 minutos
            onProgress: (progressUpdate) => {
              console.log('Progress update:', progressUpdate);
              
              if (progressUpdate.progress) {
                setProgressData(progressUpdate.progress);
              }

              if (progressUpdate.phases && progressUpdate.phases.length > 0) {
                const updatedPhases = phases.map(phase => {
                  const phaseUpdate = progressUpdate.phases.find(p => p.phase === phase.id);
                  if (phaseUpdate) {
                    return {
                      ...phase,
                      status: phaseUpdate.status
                    };
                  }
                  return phase;
                });
                setPhases(updatedPhases);
              }
            }
          }
        );

        if (!pollingResult.success) {
          throw new Error(pollingResult.error || 'Error en validación');
        }

        setAllCompleted(true);
        if (onComplete) onComplete();
      }

    } catch (error) {
      console.error('Error in validation:', error);
      setValidationError(error.message || 'Error al ejecutar validaciones');
    } finally {
      setIsValidating(false);
    }
  };

  const getPhaseStatus = (phaseId) => {
    const phase = phases.find(p => p.id === phaseId);
    return phase?.status || 'pending';
  };

  const getFileTypeTitle = () => {
    return fileType === 'libro_diario' 
      ? 'Validaciones de Libro Diario' 
      : 'Validaciones de Sumas y Saldos';
  };

  const getProgressPercentage = () => {
    if (progressData.total === 0) return 0;
    return (progressData.completed / progressData.total) * 100;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header - siempre visible */}
      <div className="bg-white border-b border-gray-200">
        <div
          className="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-gray-900">
                  {getFileTypeTitle()}
                </h3>
                <span className="text-xs text-gray-500">
                  {progressData.completed} de {progressData.total} fases completadas
                </span>
              </div>

              {/* Barra de progreso */}
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ease-out ${
                    allCompleted ? 'bg-green-500' : 'bg-purple-600'
                  }`}
                  style={{ width: `${getProgressPercentage()}%` }}
                ></div>
              </div>
            </div>

            {/* Botón para iniciar validación */}
            <div className="flex items-center ml-4">
              {!isValidating && !allCompleted && (
                <div className="flex flex-col items-end">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startValidation();
                    }}
                    disabled={!isMappingApplied}
                    className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white transition-colors ${
                      isMappingApplied
                        ? 'bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500'
                        : 'bg-gray-400 cursor-not-allowed'
                    }`}
                    title={!isMappingApplied ? 'Primero debes aplicar el mapeo de campos' : ''}
                  >
                    <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m2-10v16a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2h8l4 4z" />
                    </svg>
                    Iniciar Validación
                  </button>
                  {!isMappingApplied && (
                    <span className="text-xs text-gray-500 mt-1">
                      Aplica el mapeo primero
                    </span>
                  )}
                </div>
              )}
              
              {/* Icono de expand/collapse */}
              <svg 
                className={`w-4 h-4 text-gray-400 transition-transform duration-200 ml-3 ${
                  isExpanded ? 'rotate-180' : ''
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
      </div>

      {/* Contenido desplegable */}
      {isExpanded && (
        <div className="px-4 py-3 space-y-3">
          {/* Mostrar error si existe */}
          {validationError && (
            <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-4 h-4 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-xs font-medium text-red-800">
                  {validationError}
                </p>
              </div>
            </div>
          )}

          {phases.map((phase) => {
            const status = phase.status;
            
            return (
              <div
                key={phase.id}
                className={`p-3 rounded-lg border transition-all duration-300 ${
                  status === 'completed'
                    ? 'border-green-300 bg-green-50'
                    : status === 'validating'
                    ? 'border-blue-300 bg-blue-50'
                    : status === 'failed'
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      status === 'completed'
                        ? 'bg-green-100 text-green-600'
                        : status === 'validating'
                        ? 'bg-blue-100 text-blue-600'
                        : status === 'failed'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-gray-100 text-gray-400'
                    }`}>
                      {status === 'completed' ? (
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : status === 'validating' ? (
                        <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : status === 'failed' ? (
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        phase.id
                      )}
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        Fase {phase.id}: {phase.name}
                      </h4>
                      <p className="text-xs text-gray-600">
                        {status === 'completed' && 'Completada'}
                        {status === 'validating' && 'Validando...'}
                        {status === 'failed' && 'Falló'}
                        {status === 'pending' && 'Pendiente'}
                      </p>
                    </div>
                  </div>
                  
                  {status === 'completed' && (
                    <span className="text-xs font-medium text-green-600">
                      Completada
                    </span>
                  )}
                  {status === 'failed' && (
                    <span className="text-xs font-medium text-red-600">
                      Falló
                    </span>
                  )}
                </div>

                {/* Lista de validaciones */}
                <div className="ml-8 space-y-1">
                  {phase.validations.map((validation, validationIndex) => (
                    <div key={validationIndex} className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        status === 'completed'
                          ? 'bg-green-500'
                          : status === 'validating'
                          ? 'bg-blue-500'
                          : status === 'failed'
                          ? 'bg-red-500'
                          : 'bg-gray-300'
                      }`}></div>
                      <span className="text-xs text-gray-700">{validation}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Mensaje final */}
          {allCompleted && (
            <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
              </svg>
              <div className="ml-2">
                <p className="text-xs font-medium text-green-800">
                  Todas las validaciones completadas exitosamente
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ValidationPhases;