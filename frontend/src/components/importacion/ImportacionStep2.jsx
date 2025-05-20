// frontend/src/components/importacion/ImportacionStep2.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Check, ArrowLeft, ArrowRight, ChevronDown, ChevronUp, Eye, Loader, CheckCircle2, AlertCircle } from 'lucide-react';
import { validateFiles } from '../../services/api';

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
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
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
          <button 
            onClick={onClose} 
            className="px-6 py-2 bg-purple-700 text-white rounded-lg hover:bg-purple-800 transition-colors"
          >
            Cerrar
          </button>
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

// Validation Step Component
const ImportacionStep2 = ({ tempDir, formData, validationData, entries, sumasSaldosData, onValidationComplete, onNext, onPrev, isLoadingPreview }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(validationData);
  const [expandedSection, setExpandedSection] = useState(null);
  const [loadingSteps, setLoadingSteps] = useState({
    loading: false,
    steps: [
      { id: 'load', label: 'Cargando archivos', done: false },
      { id: 'fields', label: 'Validando campos mínimos', done: false },
      { id: 'dates', label: 'Validando fechas', done: false },
      { id: 'balance', label: 'Validando balance de asientos', done: false },
      { id: 'accounts', label: 'Validando cuentas', done: false },
      { id: 'sumas', label: 'Validando sumas y saldos', done: false }
    ]
  });
  const [showPreview, setShowPreview] = useState(false);

  // Simulate loading steps
  const simulateLoadingSteps = useCallback(() => {
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
      }
    }, 800); // Each step takes 0.8 seconds

    return () => clearInterval(interval);
  }, [loadingSteps.steps.length]);

  const handleValidate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    simulateLoadingSteps();
    
    try {
      const validationFormData = new FormData();
      validationFormData.append('temp_dir', tempDir);
      validationFormData.append('project', formData.project);
      validationFormData.append('year', formData.year);
      validationFormData.append('start_date', formData.startDate);
      validationFormData.append('end_date', formData.endDate);
      
      const result = await validateFiles(validationFormData);
      console.log("Validation result:", result);
      setValidation(result);
      onValidationComplete(result);
    } catch (err) {
      console.error("Validation error:", err);
      setError(err.message || 'Error en la validación');
    } finally {
      setIsLoading(false);
    }
  }, [tempDir, formData, onValidationComplete, simulateLoadingSteps]);

  useEffect(() => {
    if (!validationData && tempDir) {
      handleValidate();
    } else {
      setValidation(validationData);
    }
  }, [validationData, tempDir, handleValidate]);

  const toggleSection = (sectionId) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  const getAllValidationChecks = () => {
    if (!validation) return [];
    
    const libroChecks = validation.libro_diario_validation?.checks || [];
    const sumasChecks = validation.sumas_saldos_validation?.checks || [];
    
    return [
      ...libroChecks.map(check => ({ ...check, source: 'Libro Diario' })),
      ...sumasChecks.map(check => ({ ...check, source: 'Sumas y Saldos' }))
    ];
  };

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
    );
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

  const allChecks = getAllValidationChecks();
  const hasErrors = validation.has_errors;

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h3 className="text-2xl font-semibold text-gray-800 mb-6">Validación de archivos</h3>
      
      <div className="space-y-6">
        {/* Combined validation table */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validación</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Origen</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {allChecks.map((check, index) => (
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
                            <svg xmlns="http://www.w3.org/2000/svg" className="text-red-500" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <line x1="18" y1="6" x2="6" y2="18"></line>
                              <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
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
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        check.source === 'Libro Diario' 
                          ? 'bg-purple-100 text-purple-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {check.source}
                      </span>
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
                      <td colSpan="4" className="px-0 py-0">
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
              className="bg-purple-700 text-white px-4 py-2 rounded-lg hover:bg-purple-800 transition flex items-center gap-2"
              disabled={isLoadingPreview}
            >
              {isLoadingPreview ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  Cargando...
                </>
              ) : (
                <>
                  <Eye size={16} />
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
                    <li>Revisar los detalles de cada error expandiendo las secciones de validación</li>
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
          className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition flex items-center gap-2"
        >
          <ArrowLeft size={16} />
          Anterior
        </button>
        <button 
          onClick={onNext}
          disabled={hasErrors || isLoading}
          className={`px-6 py-3 rounded-lg transition flex items-center gap-2 ${
            (hasErrors || isLoading) 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : 'bg-purple-700 text-white hover:bg-purple-800'
          }`}
        >
          {isLoading ? (
            <>
              <Loader className="animate-spin" size={16} />
              Procesando...
            </>
          ) : (
            <>
              Siguiente
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>

      <FilePreviewModal 
        isOpen={showPreview} 
        onClose={() => setShowPreview(false)} 
        entries={entries || []} 
        sumasSaldosData={sumasSaldosData || []}
      />
    </div>
  );
};

export default ImportacionStep2;