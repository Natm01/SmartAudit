// frontend/src/components/analisis-obsolescencia/AnalisisObsolescenciaStep2.jsx
import React from 'react';
import { ArrowLeft, ArrowRight, Eye, FileText, BarChart3, CheckCircle, Loader } from 'lucide-react';

const AnalisisObsolescenciaStep2 = ({ validationData, onPrev, onNext, isLoading, onValidationComplete }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Validación de archivos</h3>
      
      <div className="space-y-4">
        {validationData?.map((result, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="text-green-500 mr-3" size={18} />
                <div>
                  <span className="font-medium">{result.fileName}</span>
                  <span className="text-sm text-gray-500 ml-2">{result.message}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button 
                  className="text-gray-400 hover:text-purple-600 transition"
                  title="Previsualizar archivo"
                >
                  <Eye size={16} />
                </button>
                <button 
                  className="text-gray-400 hover:text-purple-600 transition"
                  title="Ver detalles"
                >
                  <FileText size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Explicación adicional */}
      <div className="mt-6 bg-purple-50 border border-purple-100 rounded-lg p-4">
        <h4 className="text-sm font-medium text-purple-700 mb-2">Validaciones realizadas</h4>
        <ul className="text-sm text-purple-600 list-disc pl-5 space-y-1">
          <li>Verificación de la estructura de archivos</li>
          <li>Validación de fechas y períodos</li>
          <li>Comprobación de inventario al cierre</li>
          <li>Validación de transacciones y movimientos</li>
          <li>Verificación de criterios de obsolescencia</li>
        </ul>
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
          disabled={isLoading || !validationData || validationData.some(result => result.status !== 'success')}
          className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader className="animate-spin -ml-1 mr-2 h-4 w-4" size={16} />
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
  );
};

export default AnalisisObsolescenciaStep2;