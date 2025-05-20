// frontend/src/pages/ImportacionPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, Routes, Route } from 'react-router-dom';
import ImportacionStep1 from '../components/importacion/ImportacionStep1';
import ImportacionStep2 from '../components/importacion/ImportacionStep2';
import ImportacionStep3 from '../components/importacion/ImportacionStep3';
import StepIndicator from '../components/importacion/StepIndicator';
import { getPreviewData, cleanupTempFiles } from '../services/api';

const ImportacionPage = () => {
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
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  
  const navigate = useNavigate();

  const handleNavigation = (screen) => {
    navigate(`/${screen}`);
  };

  const handleStepChange = (step) => {
    if (step >= 1 && step <= 3) {
      setCurrentStep(step);
      navigate(step === 1 ? '/importacion' : `/importacion/step${step}`);
    }
  };

  const handleFormChange = (newData) => {
    setFormData({ ...formData, ...newData });
  };

  const handleUploadSuccess = async (response) => {
    setTempDir(response.temp_dir);
    
    // Cargar datos de previsualización
    await loadPreviewData(response.temp_dir);
    
    handleStepChange(2);
  };

  const loadPreviewData = async (tempDirectory) => {
    setIsLoadingPreview(true);
    try {
      // Cargar datos del libro diario
      const libroData = await getPreviewData(tempDirectory, 'libro');
      if (libroData.entries) {
        setEntries(libroData.entries);
      }
      
      // Cargar datos de sumas y saldos
      const sumasData = await getPreviewData(tempDirectory, 'sumas');
      if (sumasData.records) {
        setSumasSaldosData(sumasData.records);
      }
    } catch (error) {
      console.error('Error cargando datos de previsualización:', error);
      // No mostramos error al usuario ya que la previsualización es opcional
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleValidationComplete = (validationResult) => {
    setValidationData(validationResult);
    setValidationId(validationResult.validation_id);
  };

  const handleProcessComplete = (processResult) => {
    setProcessData(processResult);
    if (processResult.entries) {
      setEntries(processResult.entries);
    }
  };

  const handleFinish = async () => {
    // Limpiar archivos temporales al finalizar
    if (tempDir) {
      try {
        await cleanupTempFiles(tempDir);
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
    
    // Navegar al inicio
    handleNavigation('');
  };

  // Generar datos mockeados para desarrollo/testing
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
        
        <StepIndicator currentStep={currentStep} handleStepChange={handleStepChange} />
      </div>
      
      <Routes>
        <Route
          path="/"
          element={
            <ImportacionStep1
              formData={formData}
              onFormChange={handleFormChange}
              onUploadSuccess={handleUploadSuccess}
              onNext={() => handleStepChange(2)}
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
              isLoadingPreview={isLoadingPreview}
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
      
      {/* Loading overlay para previsualización */}
      {isLoadingPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center gap-3 shadow-xl">
            <div className="animate-spin h-6 w-6 border-2 border-purple-700 border-t-transparent rounded-full"></div>
            <span className="text-gray-700 font-medium">Cargando datos de previsualización...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportacionPage;