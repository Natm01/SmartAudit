// frontend/src/pages/ValidationPage/ValidationPage.jsx - Con secciones desplegables
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import ValidationPhases from '../../components/ValidationPhases/ValidationPhases';
import FilePreview from '../../components/FilePreview/FilePreview';
import StatusModal from '../../components/StatusModal/StatusModal';
import importService from '../../services/importService';
import projectService from '../../services/projectService';

const ValidationPage = () => {
  const { executionId } = useParams();
  const navigate = useNavigate();
  const processStartedRef = useRef(false);
  
  // Estados principales
  const [executionData, setExecutionData] = useState(null);
  const [sumasSaldosExecutionData, setSumasSaldosExecutionData] = useState(null);
  const [loading, setLoading] = useState(false); // Cambiado a false para mostrar la página inmediatamente
  const [error, setError] = useState(null);

  // Estados para controlar las secciones desplegables
  const [libroDiarioExpanded, setLibroDiarioExpanded] = useState(true);
  const [sumasSaldosExpanded, setSumasSaldosExpanded] = useState(true);

  // Estado para controlar si el mapeo fue aplicado
  const [isMappingApplied, setIsMappingApplied] = useState(false);
  
  // Estados del proceso paso a paso
  const [processState, setProcessState] = useState({
    step: 'starting',
    libroDiario: {
      validated: false,
      validationError: null,
      converted: false, 
      conversionError: null,
      mapped: false,
      mappingError: null
    },
    sumasSaldos: {
      validated: false,
      validationError: null
    }
  });
  
  const [statusModal, setStatusModal] = useState({ open: false, title: '', subtitle: '', status: 'info' });

  // Claves para sessionStorage
  const getStorageKey = (suffix) => {
    if (!executionId) return `validation_unknown_${suffix}`;
    return `validation_${executionId}_${suffix}`;
  };

  // Guardar estado en sessionStorage
  const saveStateToStorage = (state) => {
    if (!executionId) return;
    try {
      sessionStorage.setItem(getStorageKey('processState'), JSON.stringify(state));
      sessionStorage.setItem(getStorageKey('timestamp'), Date.now().toString());
    } catch (error) {
      console.warn('Could not save state to sessionStorage:', error);
    }
  };

  // Cargar estado desde sessionStorage
  const loadStateFromStorage = () => {
    if (!executionId) return null;
    try {
      const savedState = sessionStorage.getItem(getStorageKey('processState'));
      const timestamp = sessionStorage.getItem(getStorageKey('timestamp'));
      
      if (savedState && timestamp) {
        const timeDiff = Date.now() - parseInt(timestamp);
        const maxAge = 30 * 60 * 1000; // 30 minutos
        
        if (timeDiff < maxAge) {
          const parsedState = JSON.parse(savedState);
          console.log(' Restaurando estado desde sessionStorage:', parsedState);
          return parsedState;
        } else {
          clearStorageForExecution();
        }
      }
    } catch (error) {
      console.warn('Could not load state from sessionStorage:', error);
    }
    return null;
  };

  // Limpiar storage para esta ejecución
  const clearStorageForExecution = () => {
    if (!executionId) return;
    try {
      sessionStorage.removeItem(getStorageKey('processState'));
      sessionStorage.removeItem(getStorageKey('timestamp'));
      sessionStorage.removeItem(getStorageKey('executionData'));
    } catch (error) {
      console.warn('Could not clear sessionStorage:', error);
    }
  };

  useEffect(() => {
    loadInitialData();
    // Cargar estado de mapeo aplicado desde sessionStorage
    try {
      const mappingAppliedStatus = sessionStorage.getItem(`mappingApplied_${executionId}`);
      if (mappingAppliedStatus === 'true') {
        setIsMappingApplied(true);
      }
    } catch (error) {
      console.warn('Could not load mapping applied status:', error);
    }
  }, [executionId]);

  useEffect(() => {
    if (processState.step !== 'starting' && executionId) {
      saveStateToStorage(processState);
    }
  }, [processState, executionId]);

  const loadInitialData = async () => {
    try {
      setError(null);

      if (!executionId) {
        setError('ID de ejecución no encontrado');
        return;
      }
      
      console.log(' Cargando datos para execution:', executionId);

      const savedState = loadStateFromStorage();
      
      if (savedState) {
        console.log('Estado restaurado desde sessionStorage');
        setProcessState(savedState);
        
        if (savedState.step === 'completed') {
          console.log('Proceso ya completado, saltando ejecución');
          processStartedRef.current = true;
        }
      }

      const executionResponse = await importService.getExecutionStatus(executionId);

      if (!executionResponse.success || !executionResponse.execution) {
        setError('No se pudo cargar la información de la ejecución');
        setLoading(false);
        return;
      }

      const execution = executionResponse.execution;
      console.log('ðŸ“¦ Datos de ejecución obtenidos:', execution);

      // Obtener el nombre del proyecto usando project_id
      let projectName = 'Proyecto no especificado';
      if (execution.project_id) {
        try {
          const projectResponse = await projectService.getProjectById(execution.project_id);
          if (projectResponse.success && projectResponse.project) {
            projectName = projectResponse.project.name;
            console.log(' Nombre del proyecto obtenido:', projectName);
          }
        } catch (err) {
          console.warn('No se pudo obtener el nombre del proyecto:', err);
        }
      }

      // Crear el objeto de datos de ejecución con la información real
      const execData = {
        executionId: executionId,
        projectName: projectName,
        period: execution.period || 'PerÃ­odo no especificado',
        libroDiarioFile: execution.file_name || 'Archivo no especificado',
      };

      console.log('ðŸ“‹ Datos de ejecución preparados:', execData);
      setExecutionData(execData);

      // Intentar obtener datos de Sumas y Saldos si existe
      try {
        const sumasSaldosId = `${executionId}-ss`; // El formato correcto segÃºn execution_service.py
        console.log('Buscando Sumas y Saldos con ID:', sumasSaldosId);
        
        const ssExecution = await importService.getExecutionStatus(sumasSaldosId);
        console.log('Respuesta de bÃºsqueda SS:', ssExecution);
        
        if (ssExecution && ssExecution.success && ssExecution.execution) {
          const executionInfo = ssExecution.execution;
          setSumasSaldosExecutionData({
            execution_id: sumasSaldosId,
            fileName: executionInfo.file_name || 'Sumas_Saldos.xlsx',
            status: executionInfo.status,
            file_path: executionInfo.file_path
          });
          console.log('Datos de Sumas y Saldos encontrados:', executionInfo);
        } else {
          console.log('No hay archivo de Sumas y Saldos para esta ejecución');
          setSumasSaldosExecutionData(null);
        }
      } catch (err) {
        console.log('No se encontrÃ³ archivo de Sumas y Saldos:', err.message);
        setSumasSaldosExecutionData(null);
      }

      try {
        sessionStorage.setItem(getStorageKey('executionData'), JSON.stringify(execData));
      } catch (error) {
        console.warn('Could not save execution data:', error);
      }

      if (!processStartedRef.current && (!savedState || savedState.step !== 'completed')) {
        processStartedRef.current = true;
        console.log(' Iniciando proceso completo...');
        await startCompleteProcess();
      }

    } catch (err) {
      console.error('Error en carga inicial:', err);
      setError('Error al cargar la información inicial: ' + (err.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  };

  const startCompleteProcess = async () => {
    try {
      console.log('niciando proceso completo para:', executionId);
      
      setStatusModal({
        open: true,
        title: 'Cargando y procesando archivos',
        subtitle: 'Verificando archivos antes del procesamiento',
        status: 'loading'
      });

      const result = await importService.runCompleteValidationConversionMapeo(executionId);

      if (result && result.success) {
        const completedState = {
          step: 'completed',
          libroDiario: {
            validated: true,
            validationError: null,
            converted: true,
            conversionError: null,
            mapped: true,
            mappingError: null
          },
          sumasSaldos: {
            validated: result.validationResult?.results?.sumasSaldos?.success || false,
            validationError: result.validationResult?.results?.sumasSaldos?.error || null
          }
        };

        setProcessState(completedState);

        setStatusModal({
          open: true,
          title: '¡Proceso completado!',
          subtitle: 'Archivo validado, convertido y mapeado correctamente',
          status: 'success'
        });

      } else {
        const errorState = { ...processState, step: 'error' };
        setProcessState(errorState);
        
        setStatusModal({
          open: true,
          title: 'Error en el proceso',
          subtitle: result?.error || 'OcurriÃ³ un error durante el proceso',
          status: 'error'
        });
      }

    } catch (error) {
      console.error('Error en proceso completo:', error);
      const errorState = { ...processState, step: 'error' };
      setProcessState(errorState);
      
      setStatusModal({
        open: true,
        title: 'Error inesperado',
        subtitle: error?.message || 'OcurriÃ³ un problema al procesar tu solicitud',
        status: 'error'
      });
    }
  };


  const handleProceedToResults = () => {
    const canProceed = processState.step === 'completed' && 
                      processState.libroDiario.validated && 
                      processState.libroDiario.converted &&
                      processState.libroDiario.mapped;
                      
    if (canProceed) {
      try {
        sessionStorage.setItem(getStorageKey('navigatedToResults'), 'true');
      } catch (error) {
        console.warn('Could not save navigation state:', error);
      }
      
      navigate(`/libro-diario/results/${executionId}`);
    }
  };


  const canProceedToResults = () => {
    return processState.step === 'completed' && 
           processState.libroDiario.validated && 
           processState.libroDiario.converted &&
           processState.libroDiario.mapped;
  };

  const getStepStatus = (stepNumber) => {
    if (stepNumber === 1) return 'completed';
    if (stepNumber === 2) {
      return processState.step === 'completed' ? 'completed' : 'active';
    }
    if (stepNumber === 3) {
      return canProceedToResults() ? 'ready' : 'pending';
    }
    return 'pending';
  };

  const shouldShowPreview = () => {
    return processState.libroDiario.converted && processState.libroDiario.mapped;
  };

  const handleRestartProcess = () => {
    clearStorageForExecution();
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600"></div>
            <span className="ml-4 text-lg text-gray-600">Cargando proceso...</span>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="max-w-md w-full bg-white rounded-xl shadow-sm p-8 text-center border border-red-100">
              <h2 className="text-xl font-semibold text-red-600 mb-2">Error al cargar resultados</h2>
              <p className="text-gray-600 mb-6">{error}</p>
              <div className="space-y-2">
                <button 
                  onClick={() => window.location.reload()} 
                  className="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  Reintentar
                </button>
                <button 
                  onClick={handleRestartProcess} 
                  className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
                >
                  Reiniciar Proceso
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      
      
      <main className="flex-1 [&_*]:text-xs [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm">
        <div className="space-y-6 max-w-full mx-auto px-6 sm:px-8 lg:px-12 xl:px-16 py-8">
          
          {/* Breadcrumb */}
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-4">
              <li>
                <div>
                  <a href="/" className="text-gray-400 hover:text-gray-500" title="Inicio">
                    <svg className="flex-shrink-0 w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
                    </svg>
                    <span className="sr-only">Inicio</span>
                  </a>
                </div>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="flex-shrink-0 w-4 h-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"></path>
                  </svg>
                  <a href="/libro-diario" className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">Importación Libro Diario</a>
                </div>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="flex-shrink-0 w-4 h-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"></path>
                  </svg>
                  <span className="ml-4 text-sm font-medium text-gray-500">Validación</span>
                </div>
              </li>
            </ol>
          </nav>

          {/* Header con indicador de estado persistido */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Validación de Archivos Contables</h1>
              <p className="mt-2 text-sm text-gray-600">
                Proyecto: {executionData?.projectName} | PerÃ­odo: {executionData?.period}
              </p>
            </div>
          </div>

          {/* Steps - Barra horizontal de seguimiento */}
          <div className="p-6">
            <div className="flex items-center justify-center">
              <div className="flex items-center text-green-600">
                <div className="flex items-center justify-center w-8 h-8 border-2 border-green-600 rounded-full bg-green-600 text-white text-sm font-medium">
                  1
                </div>
                <span className="ml-2 text-sm font-medium">Importación</span>
              </div>
              <div className="flex-1 h-px bg-gray-200 mx-4"></div>
              <div className={`flex items-center ${
                getStepStatus(2) === 'completed' ? 'text-green-600' : 'text-purple-600'
              }`}>
                <div className={`flex items-center justify-center w-8 h-8 border-2 rounded-full text-sm font-medium ${
                  getStepStatus(2) === 'completed' 
                    ? 'border-green-600 bg-green-600 text-white' 
                    : 'border-purple-600 bg-purple-600 text-white'
                }`}>
                  {getStepStatus(2) === 'completed' ? '2' : '2'}
                </div>
                <span className="ml-2 text-sm font-medium">Validación</span>
              </div>
              <div className="flex-1 h-px bg-gray-200 mx-4"></div>
              <div className={`flex items-center ${
                getStepStatus(3) === 'ready' ? 'text-green-600' : 'text-gray-400'
              }`}>
                <div className={`flex items-center justify-center w-8 h-8 border-2 rounded-full text-sm font-medium ${
                  getStepStatus(3) === 'ready'
                    ? 'border-green-600 bg-green-600 text-white'
                    : 'border-gray-300'
                }`}>
                  {getStepStatus(3) === 'ready' ? '3' : '3'}
                </div>
                <span className="ml-2 text-sm font-medium">Resultados</span>
              </div>
            </div>
          </div>


          {/* ================================================ */}
          {/* SECCIÓN DESPLEGABLE: LIBRO DIARIO                */}
          {/* ================================================ */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {/* Header de la sección desplegable */}
            <button
              onClick={() => setLibroDiarioExpanded(!libroDiarioExpanded)}
              className="w-full flex items-center justify-between p-6 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="text-left">
                  <h3 className="text-base font-semibold text-gray-900">Libro Diario</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Validación y mapeo de libro diario contable
                  </p>
                </div>
              </div>
              <svg
                className={`w-5 h-5 text-gray-400 transform transition-transform ${
                  libroDiarioExpanded ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Contenido desplegable */}
            {libroDiarioExpanded && (
            <div className="border-t border-gray-200 p-6 space-y-6">
              {/* Primero: Mapeo de columnas */}
              {shouldShowPreview() && (
                <FilePreview
                  file={executionData.libroDiarioFile}
                  fileType="libro_diario"
                  executionId={executionId}
                  maxRows={25}
                  onMappingApplied={(applied) => setIsMappingApplied(applied)}
                />
              )}

              {/* Segundo: Validación */}
              <ValidationPhases
                fileType="libro_diario"
                executionId={executionId}
                period={executionData?.period}
                isMappingApplied={isMappingApplied}
                onComplete={() => {
                  console.log('Validación de Libro Diario completada');
                }}
              />

              {!shouldShowPreview() && (
                <div className="bg-gray-50 rounded-lg p-6 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-purple-600 mb-4"></div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Procesando archivo...</h3>
                  <p className="text-xs text-gray-600">
                    {processState.step === 'validating' && 'Validando estructura del archivo'}
                    {processState.step === 'converting' && 'Convirtiendo a formato estÃ¡ndar'}
                    {processState.step === 'mapping' && 'Generando sugerencias de mapeo'}
                    {processState.step === 'starting' && 'Iniciando proceso'}
                  </p>
                </div>
              )}
            </div>
          )}
          </div>

          {/* ================================================ */}
          {/* SECCIÓN DESPLEGABLE: SUMAS Y SALDOS             */}
          {/* Solo mostrar si realmente existe el archivo     */}
          {/* ================================================ */}
          {sumasSaldosExecutionData && sumasSaldosExecutionData.execution_id && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* Header de la sección desplegable */}
              <button
                onClick={() => setSumasSaldosExpanded(!sumasSaldosExpanded)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <h3 className="text-base font-semibold text-gray-900">Sumas y Saldos</h3>
                    <p className="text-sm text-gray-500">{sumasSaldosExecutionData.fileName || 'Archivo de Sumas y Saldos'}</p>
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    sumasSaldosExpanded ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Contenido desplegable */}
              {sumasSaldosExpanded && (
                <div className="border-t border-gray-200 p-6 space-y-6">
                  
                  {/* ✅ COMPONENTE DE VALIDACIONES PARA SUMAS Y SALDOS - PROPS CORREGIDOS */}
                  <ValidationPhases 
                    fileType="sumas_saldos" 
                    executionId={sumasSaldosExecutionData?.execution_id}
                    period={executionData?.period}  // Se pasa pero no se usa en sumas_saldos
                    onComplete={() => {
                      console.log('Validación de Sumas y Saldos completada');
                    }}
                  />

                  {/* Preview del archivo con mapeo de Sumas y Saldos */}
                  {processState.sumasSaldos.validated && sumasSaldosExecutionData?.execution_id && (
                    <FilePreview
                      fileType="sumas_saldos"
                      executionId={sumasSaldosExecutionData.execution_id}
                      maxRows={10}
                      showMapperByDefault={true}
                    />
                  )}

                  {/* Estado de error de validación */}
                  {processState.sumasSaldos.validationError && (
                    <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-lg">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 101.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-red-800">
                            {processState.sumasSaldos.validationError}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Navegación inferior */}
          <div className="flex justify-between items-center mt-8 pt-8 border-t border-gray-200">
            <button 
              onClick={() => navigate('/libro-diario')} 
              className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Volver a Importación
            </button>

            <button 
              onClick={handleProceedToResults} 
              disabled={!canProceedToResults()}
              className={`flex items-center px-6 py-2 rounded-lg transition-colors ${
                canProceedToResults()
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'disabled:opacity-50 disabled:cursor-not-allowed bg-purple-600 text-white'
              }`}
            >
              Continuar a Resultados
              <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

        </div>
      </main>

      {/* Modal de estado de validación */}
      <StatusModal
        isOpen={statusModal.open}
        title={statusModal.title}
        subtitle={statusModal.subtitle}
        status={statusModal.status}
        onClose={() => setStatusModal(prev => ({ ...prev, open: false }))}
      />

    </div>
  );
};

export default ValidationPage;