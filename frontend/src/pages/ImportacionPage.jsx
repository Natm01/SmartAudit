// frontend/src/pages/ImportacionPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, Routes, Route, useLocation } from 'react-router-dom';
import ImportacionStep1 from '../components/importacion/ImportacionStep1';
import ImportacionStep2 from '../components/importacion/ImportacionStep2';
import ImportacionStep3 from '../components/importacion/ImportacionStep3';
import StepIndicator from '../components/StepIndicator';
import { getPreviewData, cleanupTempFiles } from '../services/api';

const ImportacionPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Estado principal
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    project: '',
    year: '2024',
    startDate: '',
    endDate: '',
    libroFiles: [],
    sumasFiles: []
  });
  const [validationData, setValidationData] = useState(null);
  const [processData, setProcessData] = useState(null);
  const [tempDir, setTempDir] = useState('');
  const [validationId, setValidationId] = useState('');
  const [entries, setEntries] = useState([]);
  const [sumasSaldosData, setSumasSaldosData] = useState([]);
  const [hasTriggeredValidation, setHasTriggeredValidation] = useState(false);
  const [isUploadingFiles, setIsUploadingFiles] = useState(false);
  const [lastValidationParams, setLastValidationParams] = useState(null);

  // Nuevo estado para manejar recargas de página
  const [hasValidState, setHasValidState] = useState(false);
  const [isCheckingState, setIsCheckingState] = useState(true);

  // Función para determinar el paso actual basado en la URL
  const getStepFromURL = () => {
    const path = location.pathname;
    if (path.includes('/step3')) return 3;
    if (path.includes('/step2')) return 2;
    return 1;
  };

  // Función para verificar si el estado es válido para el paso actual
  const isStateValidForStep = (step) => {
    switch (step) {
      case 1:
        return true; // Step 1 siempre es válido
      case 2:
        // Step 2 requiere al menos formData básico y tempDir
        return formData.project && formData.year && tempDir;
      case 3:
        // Step 3 requiere validationData o processData
        return (formData.project && formData.year && tempDir && (validationData || processData));
      default:
        return false;
    }
  };

  // Función para redirigir al step válido más cercano
  const redirectToValidStep = () => {
    console.log('Redirecting to valid step due to invalid state');
    
    // Si estamos en step 3 pero no tenemos validationData, ir a step 1
    if (currentStep === 3 && !validationData && !processData) {
      handleStepChange(1);
      return;
    }
    
    // Si estamos en step 2 pero no tenemos datos básicos, ir a step 1
    if (currentStep === 2 && (!formData.project || !tempDir)) {
      handleStepChange(1);
      return;
    }
    
    // Si tenemos todo para step 3, permitir estar ahí
    if (currentStep === 3 && validationData) {
      return;
    }
    
    // En caso de duda, ir a step 1
    if (currentStep > 1) {
      handleStepChange(1);
    }
  };

  // useEffect para manejar la sincronización inicial con la URL
  useEffect(() => {
    const urlStep = getStepFromURL();
    console.log('URL step detected:', urlStep);
    console.log('Current state:', { 
      formData: formData.project ? 'has data' : 'empty', 
      tempDir: tempDir ? 'has tempDir' : 'no tempDir',
      validationData: validationData ? 'has validation' : 'no validation',
      processData: processData ? 'has process' : 'no process'
    });

    setCurrentStep(urlStep);
    
    // Verificar si el estado es válido para el paso actual después de un pequeño delay
    // Esto permite que otros useEffects se ejecuten primero
    const checkTimer = setTimeout(() => {
      const stateIsValid = isStateValidForStep(urlStep);
      console.log(`State is ${stateIsValid ? 'valid' : 'invalid'} for step ${urlStep}`);
      
      if (!stateIsValid && urlStep > 1) {
        console.log('Invalid state detected, redirecting...');
        redirectToValidStep();
      }
      
      setHasValidState(stateIsValid);
      setIsCheckingState(false);
    }, 100);

    return () => clearTimeout(checkTimer);
  }, [location.pathname]); // Solo depender de la URL

  // useEffect separado para detectar cambios en el estado y revalidar
  useEffect(() => {
    if (!isCheckingState) {
      const stateIsValid = isStateValidForStep(currentStep);
      setHasValidState(stateIsValid);
      
      if (!stateIsValid && currentStep > 1) {
        console.log('State became invalid, redirecting...');
        redirectToValidStep();
      }
    }
  }, [formData, tempDir, validationData, processData, currentStep, isCheckingState]);

  const handleNavigation = (screen) => {
    navigate(`/${screen}`);
  };

  const handleStepChange = (step) => {
    if (step >= 1 && step <= 3) {
      setCurrentStep(step);
      const stepPath = step === 1 ? '/importacion' : `/importacion/step${step}`;
      console.log(`Navigating to step ${step}: ${stepPath}`);
      navigate(stepPath);
    }
  };

  // Función para determinar si se puede navegar a un paso específico
  const canNavigateToStep = (step) => {
    switch (step) {
      case 1:
        return true; // Siempre se puede volver al Step 1
      case 2:
        // Step 2 requiere al menos formData básico y tempDir
        return formData.project && formData.year && tempDir;
      case 3:
        // Step 3 requiere validationData completada sin errores
        return validationData && !validationData.has_errors;
      default:
        return false;
    }
  };

  const handleFormChange = (newData) => {
    console.log('Form data changing:', newData);
    
    // Si ya hay datos de validación y cambian parámetros importantes, limpiar estado
    if (validationData && (newData.project || newData.year || newData.startDate || newData.endDate)) {
      console.log('Important form parameters changed, clearing validation state');
      setValidationData(null);
      setProcessData(null);
      setHasTriggeredValidation(false);
    }
    
    // Si cambian los archivos, también limpiar
    if (validationData && (newData.libroFiles || newData.sumasFiles)) {
      console.log('Files changed, clearing validation state');
      setValidationData(null);
      setProcessData(null);
      setEntries([]);
      setSumasSaldosData([]);
      setHasTriggeredValidation(false);
    }
    
    setFormData({ ...formData, ...newData });
  };

  const handleUploadSuccess = async (response) => {
    console.log("Upload response received:", response);
    
    // Limpiar estado anterior si existe
    if (tempDir && tempDir !== response.temp_dir) {
      console.log("New upload detected, clearing previous state");
      setValidationData(null);
      setProcessData(null);
      setEntries([]);
      setSumasSaldosData([]);
      setHasTriggeredValidation(false);
    }
    
    setTempDir(response.temp_dir);
    setIsUploadingFiles(false);
    
    // Cargar datos de previsualización de forma asíncrona SIN mostrar modal
    loadPreviewDataSilently(response.temp_dir);
    
    // Ir al paso 2 inmediatamente
    handleStepChange(2);
  };

  const handleUploadStart = () => {
    setIsUploadingFiles(true);
  };

  const handleUploadError = () => {
    setIsUploadingFiles(false);
  };

  const loadPreviewDataSilently = async (tempDirectory) => {
    if (!tempDirectory) {
      console.warn("No temp directory provided for preview");
      return;
    }

    try {
      console.log("Loading preview data for:", tempDirectory);
      
      // Cargar datos del libro diario
      try {
        const libroData = await getPreviewData(tempDirectory, 'libro');
        if (libroData.entries && libroData.entries.length > 0) {
          setEntries(libroData.entries);
          console.log("Libro diario data loaded:", libroData.entries.length, "entries");
        }
      } catch (error) {
        console.warn("Could not load libro diario preview:", error.message);
      }
      
      // Cargar datos de sumas y saldos
      try {
        const sumasData = await getPreviewData(tempDirectory, 'sumas');
        if (sumasData.records && sumasData.records.length > 0) {
          setSumasSaldosData(sumasData.records);
          console.log("Sumas y saldos data loaded:", sumasData.records.length, "records");
        }
      } catch (error) {
        console.warn("Could not load sumas y saldos preview:", error.message);
      }
    } catch (error) {
      console.error('Error cargando datos de previsualización:', error);
    }
  };

  const handleValidationComplete = (validationResult) => {
    console.log("Validation completed:", validationResult);
    setValidationData(validationResult);
    setValidationId(validationResult.validation_id);
    setHasTriggeredValidation(true);
    
    // Registrar los parámetros que se usaron para esta validación
    setLastValidationParams({
      project: formData.project,
      year: formData.year,
      startDate: formData.startDate,
      endDate: formData.endDate,
      libroFilesCount: formData.libroFiles?.length || 0,
      sumasFilesCount: formData.sumasFiles?.length || 0,
      tempDir: tempDir
    });
  };

  const handleProcessComplete = (processResult) => {
    console.log("Processing completed:", processResult);
    setProcessData(processResult);
    if (processResult.entries) {
      setEntries(processResult.entries);
    }
  };

  const handleFinish = async () => {
    console.log("Finishing importation process");
    
    // Limpiar archivos temporales al finalizar
    if (tempDir) {
      try {
        await cleanupTempFiles(tempDir);
        console.log("Temporary files cleaned up");
      } catch (error) {
        console.warn('Error al limpiar archivos temporales:', error);
      }
    }
    
    // Limpiar estado
    setFormData({
      project: '',
      year: '2024',
      startDate: '',
      endDate: '',
      libroFiles: [],
      sumasFiles: []
    });
    setValidationData(null);
    setProcessData(null);
    setTempDir('');
    setValidationId('');
    setEntries([]);
    setSumasSaldosData([]);
    setHasTriggeredValidation(false);
    setIsUploadingFiles(false);
    setLastValidationParams(null);
    
    // Navegar al inicio
    handleNavigation('');
  };

  // Generar datos mockeados para desarrollo/testing cuando no hay datos reales
  const generateMockEntries = () => {
    if (entries.length === 0) {
      const mockEntries = [];
      for (let i = 1; i <= 5; i++) {
        const entry = {
          entry_number: `0000000${i}`,
          document_number: `010000000${i}`,
          accounting_date: '010124',
          doc_date: '010124',
          header_text: 'Cobros por Tarjeta',
          lines: [
            {
              account_name: 'PASARELA PAGO EXPOS.',
              account_number: '57200001',
              debit: i * 1000.28,
              credit: 0
            },
            {
              account_name: i % 2 === 0 ? 'SANTIAGO GUIJARRO' : 'KEDECORAS S.L.',
              account_number: '43000043',
              debit: 0,
              credit: i * 1000.28
            }
          ]
        };
        mockEntries.push(entry);
      }
      return mockEntries;
    }
    return entries;
  };

  const generateMockSumasSaldos = () => {
    if (sumasSaldosData.length === 0) {
      const mockData = [
        {
          sociedad: 'AV00',
          cuenta: '10000000',
          descripcion: 'Capital social',
          moneda: 'EUR',
          divisa: '',
          arrastre: -412359.99,
          saldoAnterior: 0,
          debe: 0,
          haber: 0,
          saldoAcumulado: -412359.99
        },
        {
          sociedad: 'AV00',
          cuenta: '11200000',
          descripcion: 'Reserva legal',
          moneda: 'EUR',
          divisa: '',
          arrastre: -82472,
          saldoAnterior: 0,
          debe: 0,
          haber: 0,
          saldoAcumulado: -82472
        },
        {
          sociedad: 'AV00',
          cuenta: '11300000',
          descripcion: 'Reservas voluntarias',
          moneda: 'EUR',
          divisa: '',
          arrastre: -2022172.88,
          saldoAnterior: 0,
          debe: 0,
          haber: 0,
          saldoAcumulado: -2022172.88
        },
        {
          sociedad: 'AV00',
          cuenta: '43000001',
          descripcion: 'Clientes varios',
          moneda: 'EUR',
          divisa: '',
          arrastre: 125000,
          saldoAnterior: 0,
          debe: 15000,
          haber: 5000,
          saldoAcumulado: 135000
        },
        {
          sociedad: 'AV00',
          cuenta: '57000000',
          descripcion: 'Tesorería',
          moneda: 'EUR',
          divisa: '',
          arrastre: 85000,
          saldoAnterior: 0,
          debe: 25000,
          haber: 10000,
          saldoAcumulado: 100000
        }
      ];
      return mockData;
    }
    return sumasSaldosData;
  };

  // Limpieza cuando se abandona la página
  useEffect(() => {
    return () => {
      if (tempDir) {
        cleanupTempFiles(tempDir).catch(console.warn);
      }
    };
  }, [tempDir]);

  // Efecto para detectar cambios en parámetros críticos y limpiar validación
  useEffect(() => {
    const currentParams = {
      project: formData.project,
      year: formData.year,
      startDate: formData.startDate,
      endDate: formData.endDate,
      libroFilesCount: formData.libroFiles?.length || 0,
      sumasFilesCount: formData.sumasFiles?.length || 0,
      tempDir: tempDir
    };
    
    // Si hay validación existente y los parámetros han cambiado
    if (validationData && lastValidationParams && 
        JSON.stringify(currentParams) !== JSON.stringify(lastValidationParams)) {
      console.log('Critical parameters changed, clearing validation:', {
        previous: lastValidationParams,
        current: currentParams
      });
      
      setValidationData(null);
      setProcessData(null);
      setHasTriggeredValidation(false);
    }
    
    // Actualizar los últimos parámetros cuando se complete una validación
    if (validationData && !lastValidationParams) {
      setLastValidationParams(currentParams);
    }
    
  }, [formData.project, formData.year, formData.startDate, formData.endDate, 
      formData.libroFiles, formData.sumasFiles, tempDir, validationData, lastValidationParams]);

  // Reset validation trigger when changing steps
  useEffect(() => {
    if (currentStep !== 2) {
      setHasTriggeredValidation(false);
    }
    
    // Si el usuario regresa al Step 1, limpiar algunos estados
    if (currentStep === 1) {
      console.log("User returned to Step 1, clearing validation state");
      setValidationData(null);
      setProcessData(null);
      setLastValidationParams(null);
    }
  }, [currentStep]);

  // Debug logging para troubleshooting
  useEffect(() => {
    console.log("ImportacionPage state:", {
      currentStep,
      tempDir,
      hasValidationData: !!validationData,
      hasEntries: entries.length > 0,
      isUploadingFiles,
      hasValidState,
      isCheckingState
    });
  }, [currentStep, tempDir, validationData, entries, isUploadingFiles, hasValidState, isCheckingState]);

  // Mostrar loading mientras verificamos el estado
  if (isCheckingState) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-700 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando estado de la aplicación...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Importación Libro Diario</h2>
            <p className="text-gray-600 mt-1">Proceso de carga y validación de archivos contables</p>
          </div>
          <button
            onClick={() => handleNavigation('')}
            className="px-4 py-2 text-sm text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-lg transition-colors"
          >
            ← Volver al inicio
          </button>
        </div>
        
        <StepIndicator 
          currentStep={currentStep} 
          handleStepChange={handleStepChange}
          canNavigateToStep={canNavigateToStep}
        />
      </div>
      
      <Routes>
        <Route
          path="/"
          element={
            <ImportacionStep1
              formData={formData}
              onFormChange={handleFormChange}
              onUploadSuccess={handleUploadSuccess}
              onUploadStart={handleUploadStart}
              onUploadError={handleUploadError}
              onNext={() => handleStepChange(2)}
              isLoading={isUploadingFiles}
            />
          }
        />
        <Route
          path="/step2"
          element={
            <ImportacionStep2
              tempDir={tempDir}
              formData={formData}
              validationData={validationData}
              entries={entries.length > 0 ? entries : generateMockEntries()}
              sumasSaldosData={sumasSaldosData.length > 0 ? sumasSaldosData : generateMockSumasSaldos()}
              onValidationComplete={handleValidationComplete}
              onNext={() => handleStepChange(3)}
              onPrev={() => handleStepChange(1)}
              isLoadingPreview={false}
              hasTriggeredValidation={hasTriggeredValidation}
            />
          }
        />
        <Route
          path="/step3"
          element={
            <ImportacionStep3
              tempDir={tempDir}
              validationId={validationId}
              processData={processData}
              entries={entries.length > 0 ? entries : generateMockEntries()}
              sumasSaldosData={sumasSaldosData.length > 0 ? sumasSaldosData : generateMockSumasSaldos()}
              onProcessComplete={handleProcessComplete}
              onPrev={() => handleStepChange(2)}
              onFinish={handleFinish}
            />
          }
        />
      </Routes>
    </div>
  );
};

export default ImportacionPage;