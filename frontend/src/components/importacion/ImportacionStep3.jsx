// frontend/src/components/importacion/ImportacionStep3.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft } from 'lucide-react';
import { processFiles } from '../../services/api';

const ImportacionStep3 = ({ tempDir, validationId, processData, onProcessComplete, onPrev, onFinish }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(processData);

  // Definir handleProcess con useCallback antes de usarlo en useEffect
  const handleProcess = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const processFormData = new FormData();
      processFormData.append('temp_dir', tempDir);
      processFormData.append('validation_id', validationId || 'valid'); // Usar 'valid' como fallback para el ejemplo
      
      const result = await processFiles(processFormData);
      setData(result);
      onProcessComplete(result);
    } catch (err) {
      setError(err.message || 'Error en el procesamiento');
    } finally {
      setIsLoading(false);
    }
  }, [tempDir, validationId, onProcessComplete]);

  useEffect(() => {
    // Si no hay datos de procesamiento, iniciar procesamiento
    if (!processData && tempDir && validationId) {
      handleProcess();
    } else {
      setData(processData);
    }
  }, [processData, tempDir, validationId, handleProcess]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-700 mx-auto"></div>
            </div>
            <p className="text-gray-600">Procesando archivos...</p>
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
            onClick={handleProcess}
            className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return null; // Esperando procesamiento
  }

  // Calcular totales para la tabla de resumen
  const totalEntries = data.summary.reduce((acc, user) => acc + user.entries, 0);
  const totalDebit = data.summary.reduce((acc, user) => acc + user.debit_amount, 0);

  // Obtener primeros 10 asientos para la previsualización
  const previewEntries = data.entries.slice(0, 10);

  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Resultados de la importación</h3>
      
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-600 mb-2">Fecha contable</h4>
            <p className="text-gray-900">{data.accounting_date_range}</p>
          </div>
          <div>
            <h4 className="font-medium text-gray-600 mb-2">Fecha registro</h4>
            <p className="text-gray-900">{data.registration_date_range}</p>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-gray-700 mb-3">Previsualización de datos</h4>
          <div className="overflow-x-auto border rounded-md">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nº act.</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nº doc.</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FeCont</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FeDoc</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Denominación cuenta</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Impte.Debe ML</th>
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Impte.Haber ML</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {previewEntries.map((entry, entryIndex) => (
                  <React.Fragment key={entryIndex}>
                    <tr className="bg-gray-50">
                      <td className="py-1.5 px-3 whitespace-nowrap">{entry.entry_number}</td>
                      <td className="py-1.5 px-3 whitespace-nowrap">{entry.document_number}</td>
                      <td className="py-1.5 px-3 whitespace-nowrap">
                        {entry.accounting_date.substring(0, 2) + 
                         entry.accounting_date.substring(2, 4) + 
                         entry.accounting_date.substring(4, 6)}
                      </td>
                      <td className="py-1.5 px-3 whitespace-nowrap">
                        {entry.doc_date.substring(0, 2) + 
                         entry.doc_date.substring(2, 4) + 
                         entry.doc_date.substring(4, 6)}
                      </td>
                      <td className="py-1.5 px-3 whitespace-nowrap font-medium">{entry.header_text}</td>
                      <td className="py-1.5 px-3 whitespace-nowrap"></td>
                      <td className="py-1.5 px-3 whitespace-nowrap"></td>
                    </tr>
                    {entry.lines.map((line, lineIndex) => (
                      <tr key={`${entryIndex}-${lineIndex}`}>
                        <td className="py-1.5 px-3 whitespace-nowrap"></td>
                        <td className="py-1.5 px-3 whitespace-nowrap"></td>
                        <td className="py-1.5 px-3 whitespace-nowrap"></td>
                        <td className="py-1.5 px-3 whitespace-nowrap"></td>
                        <td className="py-1.5 px-3 whitespace-nowrap">{line.account_name}</td>
                        <td className="py-1.5 px-3 whitespace-nowrap text-right">
                          {line.debit ? line.debit.toFixed(2) : ''}
                        </td>
                        <td className="py-1.5 px-3 whitespace-nowrap text-right">
                          {line.credit ? line.credit.toFixed(2) : ''}
                        </td>
                      </tr>
                    ))}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-gray-700 mb-3">Resumen de actividad</h4>
          <div className="overflow-x-auto border rounded-md">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuarios</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asientos</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Debe</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.summary.map((user, index) => (
                  <tr key={index}>
                    <td className="py-3 px-4 whitespace-nowrap">{user.user}</td>
                    <td className="py-3 px-4 whitespace-nowrap">{user.entries}</td>
                    <td className="py-3 px-4 whitespace-nowrap">{user.debit_amount.toFixed(2)} €</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td className="py-2 px-4 whitespace-nowrap font-medium">Total</td>
                  <td className="py-2 px-4 whitespace-nowrap font-medium">{totalEntries}</td>
                  <td className="py-2 px-4 whitespace-nowrap font-medium">{totalDebit.toFixed(2)} €</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
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
          onClick={onFinish}
          className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition"
        >
          Finalizar
        </button>
      </div>
    </div>
  );
};

export default ImportacionStep3;