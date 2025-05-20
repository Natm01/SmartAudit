// frontend/src/pages/AnalisisObsolescenciaPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, Download, FileText, Trash2, Eye, CheckCircle, XCircle, AlertCircle, Search, BarChart3, Loader, CheckCircle2 } from 'lucide-react';

const AnalisisObsolescenciaPage = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    project: '',
    period: {
      start: '',
      end: ''
    },
    files: {
      inventory: [],
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
      { id: 'obsolete', label: 'Validando meses obsoletos', done: false },
      { id: 'inventory', label: 'Validando inventario', done: false },
      { id: 'trans', label: 'Validando transacciones', done: false },
      { id: 'types', label: 'Validando tipos de movimientos', done: false }
    ]
  });

  const projectOptions = [
    { id: "00041796", name: "HOTELES TURISTICOS UNIDOS, S.A." },
    { id: "00041708", name: "GRUP FLASH RABAT, S.L." },
    { id: "00042009", name: "GRUP INUIT, S.A." }
  ];

  // Mock validation results
  const mockValidationResults = [
    {
      fileName: "Inventario_24.xlsx",
      status: "success",
      message: "Archivo validado correctamente"
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

  const handleFileSelection = (fileType, e) => {
    if (e.target.files && e.target.files.length > 0) {
      try {
        const filesArray = Array.from(e.target.files).map(file => ({
          name: file.name,
          size: (file.size / 1024).toFixed(2) + ' KB',
          type: file.type,
          file: file
        }));
        
        setFormData(prev => ({
          ...prev,
          files: {
            ...prev.files,
            [fileType]: [...prev.files[fileType], ...filesArray]
          }
        }));
      } catch (err) {
        console.error("Error processing files:", err);
      }
    }
  };

  const removeFile = (fileType, index) => {
    setFormData(prev => ({
      ...prev,
      files: {
        ...prev.files,
        [fileType]: prev.files[fileType].filter((_, i) => i !== index)
      }
    }));
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
        setCurrentStep(2);
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
        setCurrentStep(3);
        setIsLoading(false);
      }, 3000);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      navigate('/');
    }
  };

  const canProceed = () => {
    if (currentStep === 1) {
      return formData.project && 
             formData.period.start && 
             formData.period.end && 
             formData.files.inventory.length > 0;
    }
    if (currentStep === 2) {
      return validationData && validationData.every(result => result.status === 'success');
    }
    return false;
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    
    if (['xlsx', 'xls'].includes(extension)) {
      return <svg xmlns="http://www.w3.org/2000/svg" className="text-green-600 mr-2" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M8 16H6v-2h2v2zm0-6H6v2h2v-2zm6 6h-4v-2h4v2zm0-6h-4v2h4v-2z"/></svg>;
    } else if (['csv', 'txt'].includes(extension)) {
      return <svg xmlns="http://www.w3.org/2000/svg" className="text-blue-600 mr-2" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>;
    } else {
      return <svg xmlns="http://www.w3.org/2000/svg" className="text-purple-700 mr-2" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>;
    }
  };

  const downloadResults = () => {
    const csvContent = [
      'Familia de producto,Unidades,Datos inventario,Unidades lenta rotación,Importe,Porcentaje,Importe %',
      ...mockAnalysisResults.families.map(family => 
        `${family.name},${family.units},${family.inventoryValue.toFixed(2)},${family.slowMovingUnits},${family.slowMovingValue.toFixed(2)},${family.percentage}%,${family.valuePercentage}%`
      ),
      `Total,${mockAnalysisResults.totals.units},${mockAnalysisResults.totals.inventoryValue.toFixed(2)},${mockAnalysisResults.totals.slowMovingUnits},${mockAnalysisResults.totals.slowMovingValue.toFixed(2)},${mockAnalysisResults.totals.percentage}%,${mockAnalysisResults.totals.valuePercentage}%`
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analisis_obsolescencia_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // File sections mapping for the import step
  const fileSections = [
    { 
      key: 'inventory', 
      label: 'Meses a los que se considera obsoleto', 
      help: 'Selecciona los meses a partir de los cuales se considera un producto obsoleto'
    },
    { 
      key: 'transactions', 
      label: 'Inventario a fin del período', 
      help: 'Archivo con el inventario al cierre del período'
    },
    { 
      key: 'movements', 
      label: 'Transacciones de existencias', 
      help: 'Archivo con los movimientos de inventario'
    },
    { 
      key: 'types', 
      label: 'Tipos de movimientos', 
      help: 'Archivo con los tipos de movimientos permitidos'
    }
  ];

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
        
        {/* Progress Steps - Same as ImportacionPage */}
        <div className="relative mb-8">
          <div className="flex justify-between items-center">
            <div 
              className={`flex flex-col items-center cursor-pointer ${currentStep >= 1 ? 'text-purple-700' : 'text-gray-400'}`}
              onClick={() => currentStep > 1 && setCurrentStep(1)}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 1 ? 'bg-purple-700' : 'bg-gray-300'}`}>
                1
              </div>
              <span className="text-sm mt-1">Importación</span>
            </div>
            
            <div 
              className={`flex flex-col items-center cursor-pointer ${currentStep >= 2 ? 'text-purple-700' : 'text-gray-400'}`}
              onClick={() => currentStep > 2 && setCurrentStep(2)}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 2 ? 'bg-purple-700' : 'bg-gray-300'}`}>
                2
              </div>
              <span className="text-sm mt-1">Validación</span>
            </div>
            
            <div 
              className={`flex flex-col items-center cursor-pointer ${currentStep >= 3 ? 'text-purple-700' : 'text-gray-400'}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 3 ? 'bg-purple-700' : 'bg-gray-300'}`}>
                3
              </div>
              <span className="text-sm mt-1">Resultado</span>
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="absolute top-4 h-1 left-0 right-0 -z-10">
            {/* Background bar */}
            <div className="absolute top-0 left-14 right-14 h-0.5 bg-gray-200"></div>
            {/* Purple progress overlay */}
            <div 
              className="absolute top-0 left-14 h-0.5 bg-purple-700 transition-all duration-300" 
              style={{ 
                width: currentStep === 1 ? '0%' : 
                       currentStep === 2 ? '50%' : '100%'
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {loadingSteps.loading ? (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex flex-col justify-center items-center">
            <div className="w-full max-w-md">
              <h3 className="text-xl font-semibold text-gray-800 mb-6 text-center">Validando archivos</h3>
              
              <div className="space-y-4">
                {loadingSteps.steps.map((step, index) => (
                  <div key={step.id} className="flex items-center">
                    <div className="flex-shrink-0 mr-4">
                      {step.done ? (
                        <CheckCircle2 className="text-green-500" size={22} />
                      ) : (
                        index === loadingSteps.steps.findIndex(s => !s.done) ? (
                          <div className="animate-spin h-5 w-5">
                            <Loader className="text-purple-700" size={22} />
                          </div>
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
      ) : currentStep === 1 ? (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h3 className="text-xl font-medium text-gray-800 mb-6">Selecciona los datos a importar</h3>
          
          <div className="space-y-4">
            {/* Project selection */}
            <div>
              <label htmlFor="project" className="block text-sm font-medium text-gray-700 mb-2">Proyecto</label>
              <select
                id="project"
                name="project"
                className="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition"
                value={formData.project}
                onChange={(e) => handleInputChange('project', e.target.value)}
              >
                <option value="">Seleccionar proyecto</option>
                {projectOptions.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.id} - {project.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Period selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Periodo</label>
              <div className="flex gap-4">
                <input 
                  type="date"
                  name="startDate"
                  className="flex-1 rounded-md border border-gray-300 p-2"
                  value={formData.period.start}
                  onChange={(e) => handleInputChange('period.start', e.target.value)}
                />
                <span className="flex items-center">a</span>
                <input 
                  type="date"
                  name="endDate"
                  className="flex-1 rounded-md border border-gray-300 p-2"
                  value={formData.period.end}
                  onChange={(e) => handleInputChange('period.end', e.target.value)}
                />
              </div>
            </div>
            
            {/* File uploads - Same style as Libro Diario */}
            {fileSections.map((section) => (
              <div key={section.key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">{section.label}</label>
                <div className="border border-dashed border-gray-300 rounded-md p-3 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0 text-purple-700">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="17 8 12 3 7 8"/>
                          <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                      </div>
                      <div className="flex-grow">
                        <p className="text-sm text-gray-600">Selecciona archivos CSV, TXT, XLSX, XLS</p>
                      </div>
                    </div>
                    <label className="cursor-pointer bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition text-sm">
                      Archivo
                      <input 
                        type="file" 
                        multiple
                        accept=".csv,.txt,.xlsx,.xls"
                        className="hidden" 
                        onChange={(e) => handleFileSelection(section.key, e)}
                      />
                    </label>
                  </div>
                </div>
                
                {formData.files[section.key]?.length > 0 && (
                  <div className="mt-2">
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {formData.files[section.key].map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-white p-2 rounded-md border border-gray-200 text-sm">
                          <div className="flex items-center">
                            {getFileIcon(file.name)}
                            <span className="truncate max-w-xs">{file.name}</span>
                            <span className="text-gray-500 ml-2">({file.size})</span>
                          </div>
                          <button 
                            type="button"
                            onClick={() => removeFile(section.key, index)}
                            className="text-gray-400 hover:text-red-500"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-8 flex justify-end">
            <button 
              onClick={handleNext}
              disabled={!canProceed() || isLoading}
              className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Validando...
                </>
              ) : (
                <>
                  Siguiente
                  
                </>
              )}
            </button>
          </div>
        </div>
      ) : currentStep === 2 ? (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h3 className="text-xl font-medium text-gray-800 mb-6">Validación de archivos</h3>
          
          <div className="space-y-4">
            {validationData?.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CheckCircle className="text-green-500 mr-3" size={18} />
                    <div>
                      <span className="foncdt-medium">{result.fileName}</span>
                      <span className="text-sm text-gray-500 ml-2">{result.message}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button className="text-gray-400 hover:text-purple-600 transition">
                      <Eye size={16} />
                    </button>
                    <button className="text-gray-400 hover:text-purple-600 transition">
                      <FileText size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-8 flex justify-between">
            <button 
              onClick={handleBack}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition flex items-center gap-2"
            >
              <ArrowLeft size={16} />
              Anterior
            </button>
            <button 
              onClick={handleNext}
              disabled={isLoading}
              className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analizando...
                </>
              ) : (
                <>
                  Analizar
                  <BarChart3 size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h3 className="text-xl font-medium text-gray-800 mb-6">Resultados del análisis</h3>
          
          <div className="space-y-6">
            {/* Summary Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Familia de producto
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unidades
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Datos inventario
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unidades lenta rotación
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Importe
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Porcentaje
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Importe %
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analysisResults?.families.map((family, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{family.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.units.toLocaleString()}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.inventoryValue.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.slowMovingUnits.toLocaleString()}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.slowMovingValue.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.percentage}%</td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-center">{family.valuePercentage}%</td>
                    </tr>
                  ))}
                  {/* Total row */}
                  <tr className="bg-gray-100 font-semibold">
                    <td className="px-4 py-3 text-sm text-gray-900">Total</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.units.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.inventoryValue.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.slowMovingUnits.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.slowMovingValue.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.percentage}%</td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-center">{analysisResults?.totals.valuePercentage}%</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Download Section */}
            <div className="border-t pt-6">
              <h4 className="font-medium text-gray-700 mb-4">Descargar resultados</h4>
              <p className="text-sm text-gray-600 mb-4">
                Los datos han sido procesados correctamente. Puedes descargar los resultados en formato CSV.
              </p>
              <button
                onClick={downloadResults}
                className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2"
              >
                <Download size={16} />
                Descargar CSV
              </button>
            </div>
          </div>
          
          <div className="mt-8 flex justify-between">
            <button 
              onClick={handleBack}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition flex items-center gap-2"
            >
              <ArrowLeft size={16} />
              Anterior
            </button>
            <button 
              onClick={() => navigate('/')}
              className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2"
            >
              Finalizar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalisisObsolescenciaPage;