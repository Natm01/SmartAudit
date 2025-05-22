// frontend/src/components/importacion/ImportacionStep2.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Check, ArrowLeft, ArrowRight, ChevronDown, ChevronUp, Eye, Loader, CheckCircle2, AlertCircle, X, AlertTriangle } from 'lucide-react';
import { validateFilesWithStreaming } from '../../services/api';

// Preview Modal Component
const FilePreviewModal = ({ isOpen, onClose, entries, sumasSaldosData }) => {
  const [activeTab, setActiveTab] = useState('libro');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[85vh] flex flex-col">
        <div className="p-4 border-b flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h3 className="font-semibold text-lg">Previsualización de datos</h3>
            
            {/* Tabs */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('libro')}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  activeTab === 'libro' 
                    ? 'bg-white text-purple-700 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Libro Diario
              </button>
              {sumasSaldosData && sumasSaldosData.length > 0 && (
                <button
                  onClick={() => setActiveTab('sumas')}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                    activeTab === 'sumas' 
                      ? 'bg-white text-purple-700 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Sumas y Saldos
                </button>
              )}
            </div>
          </div>
          
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>
        
        <div className="overflow-auto flex-1 p-6">
          {activeTab === 'libro' && entries && entries.length > 0 ? (
            <div className="overflow-x-auto border rounded-lg">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nº Asiento</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nº Documento</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fe. Contable</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fe. Documento</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cuenta</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Debe</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Haber</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {entries.slice(0, 20).map((entry, entryIndex) => (
                    <React.Fragment key={entryIndex}>
                      <tr className="bg-purple-50">
                        <td className="py-2 px-4 font-semibold text-purple-700">{entry.entry_number}</td>
                        <td className="py-2 px-4">{entry.document_number}</td>
                        <td className="py-2 px-4">
                          {entry.accounting_date.substring(0, 2)}/{entry.accounting_date.substring(2, 4)}/{20 + entry.accounting_date.substring(4, 6)}
                        </td>
                        <td className="py-2 px-4">
                          {entry.doc_date.substring(0, 2)}/{entry.doc_date.substring(2, 4)}/{20 + entry.doc_date.substring(4, 6)}
                        </td>
                        <td className="py-2 px-4 text-gray-500">-</td>
                        <td className="py-2 px-4 font-medium text-gray-700">{entry.header_text}</td>
                        <td className="py-2 px-4 text-right text-gray-500">-</td>
                        <td className="py-2 px-4 text-right text-gray-500">-</td>
                      </tr>
                      {entry.lines && entry.lines.map((line, lineIndex) => (
                        <tr key={`${entryIndex}-${lineIndex}`} className="hover:bg-gray-50">
                          <td className="py-2 px-4 text-gray-300">└─</td>
                          <td className="py-2 px-4"></td>
                          <td className="py-2 px-4"></td>
                          <td className="py-2 px-4"></td>
                          <td className="py-2 px-4 font-mono text-sm">{line.account_number}</td>
                          <td className="py-2 px-4">{line.account_name}</td>
                          <td className="py-2 px-4 text-right font-mono">
                            {line.debit && line.debit > 0 ? parseFloat(line.debit).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''}
                          </td>
                          <td className="py-2 px-4 text-right font-mono">
                            {line.credit && line.credit > 0 ? parseFloat(line.credit).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''}
                          </td>
                        </tr>
                      ))}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
              {entries.length > 20 && (
                <div className="p-4 bg-gray-50 text-center text-sm text-gray-600 border-t">
                  Mostrando los primeros 20 asientos de {entries.length} asientos totales
                </div>
              )}
            </div>
          ) : activeTab === 'sumas' && sumasSaldosData && sumasSaldosData.length > 0 ? (
            <div className="overflow-x-auto border rounded-lg">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sociedad</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cuenta</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                    <th className="py-3 px-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Arrastre</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo Anterior</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Debe Período</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Haber Período</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo Acumulado</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sumasSaldosData.slice(0, 30).map((record, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="py-2 px-4 text-purple-700 font-semibold">{record.sociedad}</td>
                      <td className="py-2 px-4 font-mono text-sm">{record.cuenta}</td>
                      <td className="py-2 px-4">{record.descripcion}</td>
                      <td className="py-2 px-4 text-center text-gray-600">{record.moneda}</td>
                      <td className="py-2 px-4 text-right font-mono">
                        {record.arrastre !== 0 ? record.arrastre.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'}
                      </td>
                      <td className="py-2 px-4 text-right font-mono">
                        {record.saldoAnterior !== 0 ? record.saldoAnterior.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'}
                      </td>
                      <td className="py-2 px-4 text-right font-mono text-green-600">
                        {record.debe !== 0 ? record.debe.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'}
                      </td>
                      <td className="py-2 px-4 text-right font-mono text-red-600">
                        {record.haber !== 0 ? record.haber.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'}
                      </td>
                      <td className="py-2 px-4 text-right font-mono font-semibold">
                        {record.saldoAcumulado !== 0 ? record.saldoAcumulado.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sumasSaldosData.length > 30 && (
                <div className="p-4 bg-gray-50 text-center text-sm text-gray-600 border-t">
                  Mostrando los primeros 30 registros de {sumasSaldosData.length} registros totales
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-4">
                <Eye className="mx-auto text-gray-300" size={48} />
              </div>
              <p className="text-lg font-medium">No hay datos disponibles</p>
              <p className="text-sm">Los datos se mostrarán después de una importación exitosa</p>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {activeTab === 'libro' && entries 
              ? `${entries.length} asientos encontrados` 
              : activeTab === 'sumas' && sumasSaldosData 
              ? `${sumasSaldosData.length} cuentas encontradas`
              : 'Sin datos'
            }
          </div>
        </div>
      </div>
    </div>
  );
};

// Validation Details Modal Component
const ValidationDetailsModal = ({ isOpen, onClose, fileValidation }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  const toggleSection = (sectionId) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  if (!isOpen || !fileValidation) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        <div className="p-4 border-b flex justify-between items-center">
          <div>
            <h3 className="font-semibold text-lg">Detalles de validación</h3>
            <p className="text-sm text-gray-600 mt-1">{fileValidation.file_name}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>
        
        <div className="overflow-auto flex-1 p-6">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validación</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {fileValidation.checks.map((check, index) => (
                  <React.Fragment key={index}>
                    <tr className={`${expandedSection === index ? 'bg-gray-50' : ''} transition-colors`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {check.passed ? (
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                              <Check className="text-green-500" size={20} />
                            </div>
                          ) : (
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-red-500 rounded-full mr-3"></div>
                              <X className="text-red-500" size={20} />
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className={`font-semibold ${check.passed ? 'text-green-700' : 'text-red-700'}`}>
                            {check.name}
                          </span>
                          {!check.passed && check.message && (
                            <span className="text-xs text-red-500 mt-1 truncate max-w-xs">
                              {check.message.split(';')[0]}...
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => toggleSection(index)}
                          className="text-purple-700 hover:text-purple-900 flex items-center transition-colors"
                        >
                          Ver detalles
                          {expandedSection === index ? (
                            <ChevronUp size={16} className="ml-1" />
                          ) : (
                            <ChevronDown size={16} className="ml-1" />
                          )}
                        </button>
                      </td>
                    </tr>
                    {expandedSection === index && (
                      <tr>
                        <td colSpan="3" className="px-0 py-0">
                          {check.passed ? (
                            <SuccessDetailsComponent check={check} />
                          ) : (
                            <ErrorDetailsComponent check={check} />
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="p-4 border-t bg-gray-50 flex justify-end">
        </div>
      </div>
    </div>
  );
};

// Error Details Component  
const ErrorDetailsComponent = ({ check }) => {
  if (!check.message) return null;

  // Parse error messages (assuming they come separated by semicolons)
  const errors = check.message.split(';').filter(error => error.trim().length > 0);
  
  // If too many errors, show only first 10 and summarize
  const displayErrors = errors.slice(0, 10);
  const remainingCount = errors.length - displayErrors.length;

  return (
    <div className="px-8 py-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg mx-8 my-2">
      <p className="font-semibold mb-3 flex items-center">
        <AlertCircle size={16} className="mr-2" />
        Errores encontrados:
      </p>
      <ul className="list-disc list-inside space-y-1 text-red-700">
        {displayErrors.map((error, index) => (
          <li key={index} className="break-words">
            {error.trim()}
          </li>
        ))}
      </ul>
      {remainingCount > 0 && (
        <div className="mt-3 pt-3 border-t border-red-200">
          <p className="text-red-600 font-medium">
            Y {remainingCount} error{remainingCount > 1 ? 'es' : ''} adicional{remainingCount > 1 ? 'es' : ''}...
          </p>
          <p className="text-xs text-red-500 mt-1">
            Revise el archivo original para ver todos los detalles
          </p>
        </div>
      )}
    </div>
  );
};

// Success Details Component
const SuccessDetailsComponent = ({ check }) => {
  const getSuccessDetails = (checkName) => {
    switch (checkName) {
      case "Contiene los campos mínimos":
        return {
          description: "Se verificaron correctamente todos los campos requeridos:",
          items: [
            "Número de asiento",
            "Número de documento", 
            "Fecha contable",
            "Fecha documento",
            "Líneas de detalle",
            "Importes debe/haber"
          ]
        };
      case "Formato de campos":
        return {
          description: "Se validaron correctamente los formatos de:",
          items: [
            "Fechas (formato DDMMYY)",
            "Importes numéricos", 
            "Identificadores de cuenta",
            "Caracteres especiales"
          ]
        };
      case "Asientos balanceados":
        return {
          description: "Se verificó que para cada asiento:",
          items: [
            "Total Debe = Total Haber",
            "No hay diferencias por redondeo",
            "Balance correcto en todos los asientos"
          ]
        };
      case "Fechas en periodo válido":
        return {
          description: "Se verificó que todas las fechas estén dentro del periodo permitido:",
          items: [
            "Fechas contables válidas",
            "Fechas dentro del rango configurado",
            "Formato de fecha correcto"
          ]
        };
      case "Contiene todas las cuentas":
        return {
          description: "Se validó correctamente:",
          items: [
            "Códigos de cuenta existen en el plan contable",
            "Estructura de cuentas correcta",
            "No hay cuentas faltantes"
          ]
        };
      case "Balance de debe y haber":
        return {
          description: "Se verificó el balance global:",
          items: [
            "Total debe = Total haber",
            "Balance correcto de sumas y saldos",
            "No hay diferencias significativas"
          ]
        };
      case "Consistencia matemática":
        return {
          description: "Se verificó la consistencia matemática:",
          items: [
            "Arrastre + Debe - Haber = Saldo Acumulado",
            "Cálculos correctos en todas las cuentas",
            "No hay errores de redondeo"
          ]
        };
      case "Cuentas únicas":
        return {
          description: "Se verificó la unicidad de cuentas:",
          items: [
            "No hay cuentas duplicadas",
            "Cada cuenta aparece una sola vez",
            "Códigos de cuenta únicos"
          ]
        };
      case "Formato numérico":
        return {
          description: "Se validó el formato numérico:",
          items: [
            "Todos los importes son valores numéricos válidos",
            "Formato decimal correcto",
            "No hay valores no numéricos en campos de importe"
          ]
        };
      default:
        return {
          description: "Validación completada exitosamente",
          items: []
        };
    }
  };

  const details = getSuccessDetails(check.name);

  return (
    <div className="px-8 py-4 text-sm text-green-700 bg-green-50 border border-green-100 rounded-lg mx-8 my-2">
      <p className="font-semibold mb-3 flex items-center">
        <CheckCircle2 size={16} className="mr-2" />
        Validación exitosa
      </p>
      <p className="mb-3">{details.description}</p>
      {details.items.length > 0 && (
        <ul className="list-disc list-inside space-y-1 text-green-600">
          {details.items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

// Loading Steps Component (for the real loading process)
const LoadingStepsComponent = ({ loadingSteps, currentMessage }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <div className="flex flex-col justify-center items-center">
        <div className="w-full max-w-md">
          <h3 className="text-xl font-semibold text-gray-800 mb-2 text-center">Validando archivos</h3>
          <p className="text-sm text-gray-600 mb-6 text-center">{currentMessage}</p>
          
          <div className="space-y-4">
            {loadingSteps.steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className="flex-shrink-0 mr-4">
                  {step.done ? (
                    <CheckCircle2 className="text-green-500" size={22} />
                  ) : (
                    step.active ? (
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
                      : step.active
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
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-purple-600 to-purple-700 transition-all duration-1000"
                style={{ width: `${loadingSteps.progress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              {loadingSteps.progress}% completado
            </p>
          </div>
          
          {/* Indicador adicional de actividad - solo mientras está cargando */}
          {loadingSteps.loading && (
            <div className="mt-6 flex justify-center">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Validation Step Component
const ImportacionStep2 = ({ tempDir, formData, validationData, entries, sumasSaldosData, onValidationComplete, onNext, onPrev, isLoadingPreview, hasTriggeredValidation }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(validationData);
  const [isValidating, setIsValidating] = useState(false); // Nueva bandera para prevenir doble ejecución
  const [currentMessage, setCurrentMessage] = useState('Preparando validación...');
  const [loadingSteps, setLoadingSteps] = useState({
    loading: true, // Empezar en loading para mostrar "Preparando validación"
    progress: 0,
    steps: [
      { id: 'preparing', label: 'Preparando validación', done: false, active: true }, // Paso inicial activo
      { id: 'loading_files', label: 'Cargando archivos', done: false, active: false },
      { id: 'analyzing_structure', label: 'Analizando estructura', done: false, active: false },
      { id: 'validating_fields', label: 'Validando campos mínimos', done: false, active: false },
      { id: 'validating_dates', label: 'Validando fechas', done: false, active: false },
      { id: 'validating_balance', label: 'Validando balance de asientos', done: false, active: false },
      { id: 'validating_accounts', label: 'Validando cuentas', done: false, active: false }
    ]
  });
  const [showPreview, setShowPreview] = useState(false);
  const [showValidationDetails, setShowValidationDetails] = useState(false);
  const [selectedFileValidation, setSelectedFileValidation] = useState(null);

  // Handle streaming progress updates
  const handleProgressUpdate = useCallback((progressData) => {
    console.log('Progress update received:', progressData);
    
    setCurrentMessage(progressData.message || 'Procesando...');
    
    setLoadingSteps(prev => ({
      ...prev,
      progress: progressData.progress || 0,
      steps: prev.steps.map(step => {
        // Marcar el paso de preparación como completado cuando empiece loading_files
        if (step.id === 'preparing' && progressData.step === 'loading_files') {
          return { ...step, active: false, done: true };
        }
        // Actualizar el paso actual
        if (step.id === progressData.step) {
          return { ...step, active: !progressData.completed, done: progressData.completed };
        }
        return step;
      })
    }));
    
    // If completed, we'll receive the final result
    if (progressData.step === 'completed' && progressData.result) {
      console.log('Validation completed with result:', progressData.result);
      setLoadingSteps(prev => ({
        ...prev,
        loading: false,
        progress: 100,
        steps: prev.steps.map(step => ({ ...step, done: true, active: false }))
      }));
      
      // Small delay to show completion
      setTimeout(() => {
        setValidation(progressData.result);
        onValidationComplete(progressData.result);
      }, 500);
    }
  }, [onValidationComplete]);

  const handleValidate = useCallback(async () => {
    // Prevenir múltiples ejecuciones
    if (isValidating) {
      console.log("Validation already in progress, skipping...");
      return;
    }
    
    console.log("Starting real-time streaming validation...");
    setIsValidating(true);
    setIsLoading(true);
    setError(null);
    
    // Initialize loading state with "Preparando validación" active
    setLoadingSteps(prev => ({
      ...prev,
      loading: true,
      progress: 0,
      steps: prev.steps.map((step, index) => ({
        ...step, 
        done: false, 
        active: index === 0 // Solo el primer paso (Preparando validación) activo
      }))
    }));
    
    try {
      const validationFormData = new FormData();
      validationFormData.append('temp_dir', tempDir);
      validationFormData.append('project', formData.project);
      validationFormData.append('year', formData.year);
      validationFormData.append('start_date', formData.startDate);
      validationFormData.append('end_date', formData.endDate);
      
      console.log("Starting streaming validation...");
      
      // Use streaming validation
      await validateFilesWithStreaming(validationFormData, handleProgressUpdate);
      
    } catch (err) {
      console.error("Streaming validation error:", err);
      setLoadingSteps(prev => ({
        ...prev,
        loading: false,
        steps: prev.steps.map(step => ({ ...step, active: false }))
      }));
      setError(err.message || 'Error en la validación');
    } finally {
      setIsLoading(false);
      setIsValidating(false);
    }
  }, [tempDir, formData, handleProgressUpdate, isValidating]);

  useEffect(() => {
    // Solo ejecutar validación UNA VEZ si:
    // 1. No se ha ejecutado antes (hasTriggeredValidation es false)
    // 2. No hay datos de validación existentes
    // 3. Hay un directorio temporal válido
    // 4. No está ya en proceso de validación
    if (!hasTriggeredValidation && !validationData && tempDir && !isValidating && !isLoading) {
      console.log("Triggering real-time validation for the first time");
      handleValidate();
    } else if (validationData) {
      console.log("Using existing validation data");
      setValidation(validationData);
      // Asegurar que no está en estado de carga
      setLoadingSteps(prev => ({ 
        ...prev, 
        loading: false,
        steps: prev.steps.map(step => ({ ...step, done: true, active: false }))
      }));
    }
  }, [tempDir, hasTriggeredValidation, validationData, isValidating, isLoading, handleValidate]);

  // Estado para rastrear los últimos parámetros procesados
  const [lastProcessedParams, setLastProcessedParams] = useState({
    tempDir: '',
    project: '',
    year: '',
    startDate: '',
    endDate: '',
    libroFilesCount: 0,
    sumasFilesCount: 0
  });

  // Función para crear hash de parámetros actuales
  const getCurrentParams = useCallback(() => {
    return {
      tempDir: tempDir || '',
      project: formData.project || '',
      year: formData.year || '',
      startDate: formData.startDate || '',
      endDate: formData.endDate || '',
      libroFilesCount: formData.libroFiles?.length || 0,
      sumasFilesCount: formData.sumasFiles?.length || 0
    };
  }, [tempDir, formData]);

  // Función para comparar si los parámetros han cambiado
  const paramsHaveChanged = useCallback((current, last) => {
    return JSON.stringify(current) !== JSON.stringify(last);
  }, []);

  // useEffect para detectar cambios en CUALQUIER parámetro y resetear estado
  useEffect(() => {
    const currentParams = getCurrentParams();
    
    // Si hay parámetros válidos y han cambiado respecto a los últimos procesados
    if (tempDir && formData.project && paramsHaveChanged(currentParams, lastProcessedParams)) {
      console.log("Parameters changed, resetting validation state:", {
        previous: lastProcessedParams,
        current: currentParams
      });
      
      // Resetear todo el estado de validación
      setValidation(null);
      setError(null);
      setIsValidating(false);
      setCurrentMessage('Preparando validación...');
      setLoadingSteps({
        loading: true,
        progress: 0,
        steps: [
          { id: 'preparing', label: 'Preparando validación', done: false, active: true },
          { id: 'loading_files', label: 'Cargando archivos', done: false, active: false },
          { id: 'analyzing_structure', label: 'Analizando estructura', done: false, active: false },
          { id: 'validating_fields', label: 'Validando campos mínimos', done: false, active: false },
          { id: 'validating_dates', label: 'Validando fechas', done: false, active: false },
          { id: 'validating_balance', label: 'Validando balance de asientos', done: false, active: false },
          { id: 'validating_accounts', label: 'Validando cuentas', done: false, active: false }
        ]
      });
      
      // Actualizar los últimos parámetros procesados
      setLastProcessedParams(currentParams);
    }
  }, [tempDir, formData, getCurrentParams, paramsHaveChanged, lastProcessedParams]);

  // Function to get file summaries for the main table - MODIFIED to show individual files
  const getFileSummaries = () => {
    if (!validation) return [];
    
    const summaries = [];
    
    // Add individual Libro Diario file validations
    if (validation.libro_diario_validation) {
      const libroValidation = validation.libro_diario_validation;
      
      // Split the file names if there are multiple files
      const fileNames = libroValidation.file_name.split(', ');
      
      fileNames.forEach(fileName => {
        const errorCount = libroValidation.checks.filter(check => !check.passed).length;
        const warningCount = 0; // You can implement warnings logic later
        
        let status = 'success';
        if (errorCount > 0) status = 'error';
        else if (warningCount > 0) status = 'warning';
        
        summaries.push({
          fileName: fileName.trim(),
          origen: 'Libro Diario',
          status: status,
          errorCount: errorCount,
          warningCount: warningCount,
          totalChecks: libroValidation.checks.length,
          validation: libroValidation
        });
      });
    }
    
    // Add individual Sumas y Saldos file validations
    if (validation.sumas_saldos_validation) {
      const sumasValidation = validation.sumas_saldos_validation;
      
      // Split the file names if there are multiple files
      const fileNames = sumasValidation.file_name.split(', ');
      
      fileNames.forEach(fileName => {
        const errorCount = sumasValidation.checks.filter(check => !check.passed).length;
        const warningCount = 0; // You can implement warnings logic later
        
        let status = 'success';
        if (errorCount > 0) status = 'error';
        else if (warningCount > 0) status = 'warning';
        
        summaries.push({
          fileName: fileName.trim(),
          origen: 'Sumas y Saldos',
          status: status,
          errorCount: errorCount,
          warningCount: warningCount,
          totalChecks: sumasValidation.checks.length,
          validation: sumasValidation
        });
      });
    }
    
    return summaries;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <Check className="text-green-500" size={20} />;
      case 'warning':
        return <AlertTriangle className="text-yellow-500" size={20} />;
      case 'error':
        return <X className="text-red-500" size={20} />;
      default:
        return <Check className="text-gray-400" size={20} />;
    }
  };

  const openValidationDetails = (fileValidation) => {
    setSelectedFileValidation(fileValidation);
    setShowValidationDetails(true);
  };

  // Show loading steps when validation is in progress OR when we don't have validation data yet
  if (loadingSteps.loading || (!validation && !error && tempDir)) {
    return <LoadingStepsComponent loadingSteps={loadingSteps} currentMessage={currentMessage} />;
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg mb-6">
          <div className="flex items-start">
            <AlertCircle className="text-red-500 mr-3 flex-shrink-0 mt-0.5" size={24} />
            <div className="flex-grow">
              <h4 className="text-red-700 font-semibold mb-2">Error en la validación</h4>
              <p className="text-red-600 mb-3">{error}</p>
              <div className="text-sm text-red-500 bg-red-100 p-3 rounded border">
                <p className="font-medium mb-1">Posibles soluciones:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Verificar que los archivos estén en el formato correcto</li>
                  <li>Asegurar que los archivos no estén dañados</li>
                  <li>Comprobar la conexión con el servidor</li>
                  <li>Volver al paso anterior y subir los archivos nuevamente</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex justify-between">
          <button 
            onClick={onPrev}
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition flex items-center gap-2"
          >
            <ArrowLeft size={16} />
            Anterior
          </button>
          <button 
            onClick={handleValidate}
            disabled={isLoading}
            className="bg-purple-700 text-white px-6 py-3 rounded-lg hover:bg-purple-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin -ml-1 mr-2 h-4 w-4 inline" />
                Validando...
              </>
            ) : (
              'Reintentar'
            )}
          </button>
        </div>
      </div>
    );
  }

  if (!validation) {
    return null;
  }

  const fileSummaries = getFileSummaries();
  const hasErrors = validation.has_errors;

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h3 className="text-2xl font-semibold text-gray-800 mb-6">Validación de archivos</h3>
      
      <div className="space-y-6">
        {/* Main validation summary table - MODIFIED to show individual files */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fichero</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Origen</th>
                <th scope="col" className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Validaciones</th>
                <th scope="col" className="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fileSummaries.map((summary, index) => (
                <tr key={index} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-3 ${
                        summary.status === 'success' ? 'bg-green-500' :
                        summary.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></div>
                      {getStatusIcon(summary.status)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900">{summary.fileName}</span>
                      {summary.errorCount > 0 && (
                        <span className="text-xs text-red-500 mt-1">
                          {summary.errorCount} error{summary.errorCount > 1 ? 'es' : ''} encontrado{summary.errorCount > 1 ? 's' : ''}
                        </span>
                      )}
                      {summary.warningCount > 0 && (
                        <span className="text-xs text-yellow-600 mt-1">
                          {summary.warningCount} advertencia{summary.warningCount > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      summary.origen === 'Libro Diario' 
                        ? 'bg-purple-100 text-purple-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {summary.origen}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm text-gray-600">
                      {summary.totalChecks - summary.errorCount}/{summary.totalChecks} válidas
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => openValidationDetails(summary.validation)}
                      className="text-purple-700 hover:text-purple-900 flex items-center justify-center mx-auto transition-colors"
                      title="Ver detalles de validación"
                    >
                      <Eye size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* File preview section */}
        <div className="border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Archivos validados</h4>
              <div className="space-y-1">
                <p className="text-sm text-gray-600 flex items-center">
                  <span className="w-3 h-3 bg-purple-500 rounded-full mr-2"></span>
                  {validation.libro_diario_validation.file_name}
                </p>
                {validation.sumas_saldos_validation && (
                  <p className="text-sm text-gray-600 flex items-center">
                    <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                    {validation.sumas_saldos_validation.file_name}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => setShowPreview(true)}
              className="bg-purple-700 text-white px-4 py-2 rounded-lg hover:bg-purple-800 transition flex items-center text-sm gap-2"
              disabled={isLoadingPreview}
            >
              {isLoadingPreview ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  Cargando...
                </>
              ) : (
                <>
                  <Eye size={12} />
                  Previsualizar
                </>
              )}
            </button>
          </div>
        </div>
        
        {hasErrors && (
          <div className="border border-amber-200 rounded-lg p-4 bg-amber-50">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 mr-3" />
              <div className="flex-grow">
                <h4 className="text-amber-800 font-semibold mb-2">Errores de validación encontrados</h4>
                <p className="text-sm text-amber-700 mb-3">
                  Se han encontrado errores en la validación que deben corregirse antes de continuar.
                </p>
                <div className="bg-amber-100 border border-amber-200 rounded p-3">
                  <p className="text-xs text-amber-700 font-medium mb-1">Opciones disponibles:</p>
                  <ul className="text-xs text-amber-600 list-disc list-inside space-y-1">
                    <li>Hacer clic en el ícono del ojo para ver los detalles de cada archivo</li>
                    <li>Corregir los archivos y volver al paso anterior para subirlos nuevamente</li>
                    <li>Contactar al administrador si persisten los problemas</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-8 flex justify-between">
        <button 
          onClick={onPrev}
          className="border border-gray-300 text-gray-700 px-2 py-2 rounded-lg hover:bg-gray-50 transition flex items-center text-sm gap-2"
        >
          <ArrowLeft size={12} />
          Anterior
        </button>
        <button 
          onClick={onNext}
          disabled={hasErrors || isLoading}
          className={`bg-purple-700 text-white px-2 py-2 rounded-md hover:bg-purple-800 transition flex items-center text-sm gap-2 ${
            (hasErrors || isLoading) 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : 'bg-purple-700 text-white hover:bg-purple-800'
          }`}
        >
          {isLoading ? (
            <>
              <Loader className="animate-spin -ml-2 mr-2 h-4 w-4 text-white" size={12} />
              Procesando...
            </>
          ) : (
            <>
              Siguiente
              <ArrowRight size={12} />
            </>
          )}
        </button>
      </div>

      {/* Modals */}
      <FilePreviewModal 
        isOpen={showPreview} 
        onClose={() => setShowPreview(false)} 
        entries={entries || []} 
        sumasSaldosData={sumasSaldosData || []}
      />

      <ValidationDetailsModal
        isOpen={showValidationDetails}
        onClose={() => setShowValidationDetails(false)}
        fileValidation={selectedFileValidation}
      />
    </div>
  );
};

export default ImportacionStep2;