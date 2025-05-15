// frontend/src/components/importacion/ImportacionStep2.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Check, ArrowLeft, ArrowRight } from 'lucide-react';
import { validateFiles } from '../../services/api';

const ImportacionStep2 = ({ tempDir, formData, validationData, onValidationComplete, onNext, onPrev }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(validationData);

  // Definir handleValidate con useCallback antes de usarlo en useEffect
  const handleValidate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const validationFormData = new FormData();
      validationFormData.append('temp_dir', tempDir);
      validationFormData.append('project', formData.project);
      validationFormData.append('year', formData.year);
      validationFormData.append('start_date', formData.startDate);
      validationFormData.append('end_date', formData.endDate);
      
      const result = await validateFiles(validationFormData);
      setValidation(result);
      onValidationComplete(result);
    } catch (err) {
      setError(err.message || 'Error en la validación');
    } finally {
      setIsLoading(false);
    }
  }, [tempDir, formData, onValidationComplete]);

  useEffect(() => {
    // Si no hay datos de validación, iniciar validación
    if (!validationData && tempDir) {
      handleValidate();
    } else {
      setValidation(validationData);
    }
  }, [validationData, tempDir, handleValidate]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-700 mx-auto"></div>
            </div>
            <p className="text-gray-600">Validando archivos...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md mb-6">
          <h4 className="text-red-700 font-medium mb-2">Error</h4>
          <p className="text-red-600">{error}</p>
        </div>
        
        <div className="flex justify-between">
          <button 
            onClick={onPrev}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition flex items-center gap-2"
          >
            <ArrowLeft size={16} />
            Anterior
          </button>
          <button 
            onClick={handleValidate}
            className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!validation) {
    return null; // Esperando validación
  }

  const libroValidation = validation.libro_diario_validation;
  const sumasValidation = validation.sumas_saldos_validation;
  const hasErrors = validation.has_errors;

  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Validación de archivos</h3>
      
      <div className="space-y-8">
        <div className="border-b pb-6">
          <h4 className="font-medium mb-4">Fichero: Libro diario</h4>
          <div className="space-y-3">
            {libroValidation.checks.map((check, index) => (
              <div key={index} className="flex items-center gap-2">
                {check.passed ? (
                  <Check className="text-green-500" size={20} />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="text-red-500" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                )}
                <span>{check.name}</span>
                {!check.passed && check.message && (
                  <span className="text-xs text-red-500">({check.message})</span>
                )}
              </div>
            ))}
          </div>
        </div>
        
        {sumasValidation && (
          <div>
            <h4 className="font-medium mb-4">Fichero: Sumas y saldos</h4>
            <div className="space-y-3">
              {sumasValidation.checks.map((check, index) => (
                <div key={index} className="flex items-center gap-2">
                  {check.passed ? (
                    <Check className="text-green-500" size={20} />
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="text-red-500" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  )}
                  <span>{check.name}</span>
                  {!check.passed && check.message && (
                    <span className="text-xs text-red-500">({check.message})</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {hasErrors && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-700">Se han encontrado errores en la validación. Por favor, corrige los errores antes de continuar.</p>
          </div>
        )}
      </div>
      
      <div className="mt-8 flex justify-between">
        <button 
          onClick={onPrev}
          className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition flex items-center gap-2"
        >
          <ArrowLeft size={16} />
          Anterior
        </button>
        <button 
          onClick={onNext}
          className={`bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 ${hasErrors ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={hasErrors}
        >
          Siguiente
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};

export default ImportacionStep2;