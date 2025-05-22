// frontend/src/components/analisis-obsolescencia/AnalisisObsolescenciaStep3.jsx
import React from 'react';
import { ArrowLeft, Download } from 'lucide-react';

const AnalisisObsolescenciaStep3 = ({ analysisResults, formData, onPrev, onFinish }) => {
  const downloadResults = () => {
    // La URL es relativa a la carpeta public donde ya tienes el archivo
    const excelFileUrl = '/Ejemplo.xlsx';
    
    fetch(excelFileUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Error al descargar el archivo: ${response.status}`);
        }
        return response.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `analisis_obsolescencia_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      })
      .catch(error => {
        console.error('Error al descargar el archivo Excel:', error);
        alert('Error al descargar el archivo. Por favor, inténtelo de nuevo más tarde.');
      });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Resultados del análisis</h3>
      
      <div className="space-y-6">
        {/* Información de parametrización */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Análisis realizado con los siguientes parámetros:</p>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            <div className="flex items-center">
              <span className="text-xs font-medium text-gray-500 mr-1">Periodo:</span>
              <span className="text-sm text-gray-900">
                {formData.period.start && new Date(formData.period.start).toLocaleDateString()} - 
                {formData.period.end && new Date(formData.period.end).toLocaleDateString()}
              </span>
            </div>
            <div className="flex items-center">
              <span className="text-xs font-medium text-gray-500 mr-1">Criterio obsolescencia:</span>
              <span className="text-sm text-gray-900 font-semibold">
                {formData.obsolescence.value} {formData.obsolescence.unit}
              </span>
            </div>
          </div>
        </div>
        
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

        {/* Resumen gráfico (podría implementarse con un gráfico de barras) */}
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Resumen de análisis</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Porcentaje de unidades con lenta rotación:</span>
              <div className="w-1/2 flex items-center">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-purple-600 h-2.5 rounded-full" 
                    style={{ width: `${analysisResults?.totals.percentage}%` }}
                  ></div>
                </div>
                <span className="ml-2 text-sm font-semibold">{analysisResults?.totals.percentage}%</span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Porcentaje del valor con lenta rotación:</span>
              <div className="w-1/2 flex items-center">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-green-600 h-2.5 rounded-full" 
                    style={{ width: `${analysisResults?.totals.valuePercentage}%` }}
                  ></div>
                </div>
                <span className="ml-2 text-sm font-semibold">{analysisResults?.totals.valuePercentage}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Download Section */}
        <div className="border-t pt-6">
          <h4 className="font-medium text-gray-700 mb-4">Descargar resultados</h4>
          <p className="text-sm text-gray-600 mb-4">
            Los datos han sido procesados correctamente. Puedes descargar los resultados en formato Excel.
          </p>
          <button
            onClick={downloadResults}
            className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2"
          >
            <Download size={16} />
            Descargar resultados
          </button>
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
          className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2"
        >
          Finalizar
        </button>
      </div>
    </div>
  );
};

export default AnalisisObsolescenciaStep3;