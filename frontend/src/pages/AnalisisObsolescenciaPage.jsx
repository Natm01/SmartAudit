// frontend/src/pages/AnalisisObsolescenciaPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AnalisisObsolescenciaStep1 from '../components/analisis-obsolescencia/AnalisisObsolescenciaStep1';
import AnalisisObsolescenciaStep2 from '../components/analisis-obsolescencia/AnalisisObsolescenciaStep2';
import AnalisisObsolescenciaStep3 from '../components/analisis-obsolescencia/AnalisisObsolescenciaStep3';
import StepIndicator from '../components/StepIndicator';

const AnalisisObsolescenciaPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    project: '',
    period: {
      start: '',
      end: ''
    },
    obsolescence: {
      value: '',
      unit: 'meses'
    },
    files: {
      transactions: [],
      movements: [],
      types: []
    }
  });
  const [validationData, setValidationData] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSteps, setLoadingSteps] = useState({
    loading: false,
    steps: [
      { id: 'load', label: 'Cargando archivos', done: false },
      { id: 'obsolete', label: 'Configurando criterios de obsolescencia', done: false },
      { id: 'inventory', label: 'Validando inventario', done: false },
      { id: 'trans', label: 'Validando transacciones', done: false },
      { id: 'types', label: 'Validando tipos de movimientos', done: false }
    ]
  });

  // Determinar el paso actual basado en la URL
  useEffect(() => {
    const path = location.pathname;
    if (path.includes('step2')) {
      setCurrentStep(2);
    } else if (path.includes('step3')) {
      setCurrentStep(3);
    } else {
      setCurrentStep(1);
    }
  }, [location.pathname]);

  // Mock validation results
  const mockValidationResults = [
    {
      fileName: "Criterios de obsolescencia",
      status: "success",
      message: "Criterios configurados correctamente"
    },
    {
      fileName: "InvenTrans_25.xlsx", 
      status: "success",
      message: "Transacciones validadas"
    },
    {
      fileName: "InvenTrans_24.xlsx",
      status: "success", 
      message: "Datos procesados exitosamente"
    },
    {
      fileName: "TiposTransacciones",
      status: "success",
      message: "Tipos de movimientos validados"
    }
  ];

  // Mock analysis results
  const mockAnalysisResults = {
    families: [
      {
        name: "Familia A",
        units: 4792,
        inventoryValue: 255976.00,
        slowMovingUnits: 1172,
        slowMovingValue: 39450.24,
        percentage: 24,
        valuePercentage: 16
      },
      {
        name: "Familia B", 
        units: 2331,
        inventoryValue: 41968.00,
        slowMovingUnits: 452,
        slowMovingValue: 8555.77,
        percentage: 19,
        valuePercentage: 21
      },
      {
        name: "Familia C",
        units: 4424,
        inventoryValue: 97328.00, 
        slowMovingUnits: 814,
        slowMovingValue: 21028.93,
        percentage: 18,
        valuePercentage: 22
      },
      {
        name: "Familia D",
        units: 4316,
        inventoryValue: 215800.00,
        slowMovingUnits: 679,
        slowMovingValue: 52389.04,
        percentage: 16,
        valuePercentage: 24
      },
      {
        name: "Familia E",
        units: 2147,
        inventoryValue: 60116.00,
        slowMovingUnits: 333,
        slowMovingValue: 14722.83,
        percentage: 16,
        valuePercentage: 24
      }
    ],
    totals: {
      units: 18010,
      inventoryValue: 669178.00,
      slowMovingUnits: 3450,
      slowMovingValue: 136246.71,
      percentage: 19,
      valuePercentage: 20
    }
  };

  const handleFormChange = (newData) => {
    setFormData({ ...formData, ...newData });
  };

  const handleInputChange = (name, value) => {
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleStepChange = (step) => {
    if (step >= 1 && step <= 3) {
      setCurrentStep(step);
      navigate(step === 1 ? '/analisis-obsolescencia' : `/analisis-obsolescencia/step${step}`);
    }
  };

  // Function to simulate loading steps with progress
  const simulateLoadingSteps = () => {
    setLoadingSteps(prev => ({
      ...prev,
      loading: true,
      steps: prev.steps.map(step => ({ ...step, done: false }))
    }));

    let stepCounter = 0;
    const interval = setInterval(() => {
      if (stepCounter < loadingSteps.steps.length) {
        setLoadingSteps(prev => ({
          ...prev,
          steps: prev.steps.map((step, idx) => ({
            ...step,
            done: idx <= stepCounter
          }))
        }));
        stepCounter++;
      } else {
        clearInterval(interval);
        setLoadingSteps(prev => ({
          ...prev,
          loading: false,
          steps: prev.steps.map(step => ({ ...step, done: true }))
        }));
        setValidationData(mockValidationResults);
        handleStepChange(2);
      }
    }, 1000); // Each step takes 1 second

    return () => clearInterval(interval);
  };

  const handleNext = () => {
    if (currentStep === 1) {
      // Simulate validation with loading steps
      setIsLoading(true);
      simulateLoadingSteps();
      setTimeout(() => {
        setIsLoading(false);
      }, 6000);
    } else if (currentStep === 2) {
      // Simulate analysis
      setIsLoading(true);
      setTimeout(() => {
        setAnalysisResults(mockAnalysisResults);
        handleStepChange(3);
        setIsLoading(false);
      }, 3000);
    }
  };

  const handleValidationComplete = (validationResult) => {
    setValidationData(validationResult);
  };

  const handleProcessComplete = (results) => {
    setAnalysisResults(results);
  };

  const handleFinish = () => {
    // Limpiar estado
    setFormData({
      project: '',
      period: {
        start: '',
        end: ''
      },
      obsolescence: {
        value: '',
        unit: 'meses'
      },
      files: {
        transactions: [],
        movements: [],
        types: []
      }
    });
    setValidationData(null);
    setAnalysisResults(null);
    
    // Navegar al inicio
    navigate('/');
  };

  // Renderizar el paso actual basado en currentStep
  const renderCurrentStep = () => {
    if (loadingSteps.loading) {
      return (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex flex-col justify-center items-center">
            <div className="w-full max-w-md">
              <h3 className="text-xl font-semibold text-gray-800 mb-6 text-center">Validando archivos</h3>
              
              <div className="space-y-4">
                {loadingSteps.steps.map((step, index) => (
                  <div key={step.id} className="flex items-center">
                    <div className="flex-shrink-0 mr-4">
                      {step.done ? (
                        <div className="text-green-500">✓</div>
                      ) : (
                        index === loadingSteps.steps.findIndex(s => !s.done) ? (
                          <div className="animate-spin h-5 w-5">⟳</div>
                        ) : (
                          <div className="h-5 w-5 rounded-full border-2 border-gray-300"></div>
                        )
                      )}
                    </div>
                    <div className="flex-grow">
                      <p className={`text-sm font-medium ${
                        step.done 
                          ? 'text-green-600' 
                          : index === loadingSteps.steps.findIndex(s => !s.done) 
                          ? 'text-purple-700' 
                          : 'text-gray-500'
                      }`}>
                        {step.label}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-8 relative">
                <div className="overflow-hidden h-2 text-xs flex rounded-lg bg-gray-200">
                  <div 
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-purple-600 to-purple-700 transition-all duration-500"
                    style={{ width: `${(loadingSteps.steps.filter(s => s.done).length / loadingSteps.steps.length) * 100}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  {Math.round((loadingSteps.steps.filter(s => s.done).length / loadingSteps.steps.length) * 100)}% completado
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    switch (currentStep) {
      case 1:
        return (
          <AnalisisObsolescenciaStep1
            formData={formData}
            onInputChange={handleInputChange}
            onFormChange={handleFormChange}
            onNext={handleNext}
            isLoading={isLoading}
          />
        );
      case 2:
        return (
          <AnalisisObsolescenciaStep2
            validationData={validationData}
            onPrev={() => handleStepChange(1)}
            onNext={handleNext}
            isLoading={isLoading}
            onValidationComplete={handleValidationComplete}
          />
        );
      case 3:
        return (
          <AnalisisObsolescenciaStep3
            analysisResults={analysisResults}
            formData={formData}
            onPrev={() => handleStepChange(2)}
            onFinish={handleFinish}
            onProcessComplete={handleProcessComplete}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Análisis de Obsolescencia</h2>
            <p className="text-gray-600 mt-1">Detección y análisis de inventario de lenta rotación</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-sm text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-lg transition-colors"
          >
            ← Volver al inicio
          </button>
        </div>
        
        <StepIndicator currentStep={currentStep} handleStepChange={handleStepChange} />
      </div>

      {/* Main Content */}
      {renderCurrentStep()}
    </div>
  );
};

export default AnalisisObsolescenciaPage;