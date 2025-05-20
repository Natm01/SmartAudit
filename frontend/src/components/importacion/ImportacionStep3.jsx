// frontend/src/components/importacion/ImportacionStep3.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Download, Loader, FileSpreadsheet, FileText } from 'lucide-react';
import { processFiles } from '../../services/api';

const ImportacionStep3 = ({ tempDir, validationId, processData, onProcessComplete, onPrev, onFinish, entries, sumasSaldosData }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(processData);
  const [downloadLoading, setDownloadLoading] = useState({
    csv: false,
    excel: false
  });

  // Define handleProcess with useCallback before using it in useEffect
  const handleProcess = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const processFormData = new FormData();
      processFormData.append('temp_dir', tempDir);
      processFormData.append('validation_id', validationId || 'valid'); // Use 'valid' as fallback for the example
      
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
    // If no processing data, start processing
    if (!processData && tempDir && validationId) {
      handleProcess();
    } else {
      setData(processData);
    }
  }, [processData, tempDir, validationId, handleProcess]);

  const handleDownloadCSV = () => {
    // Función para convertir datos de libro diario a CSV
    if (!entries || entries.length === 0) return;

    setDownloadLoading(prev => ({ ...prev, csv: true }));
    
    try {
      // Preparar datos en formato tabular
      let csvContent = "Nº Asiento,Nº Documento,Fecha Contable,Fecha Documento,Cuenta,Descripción,Debe,Haber\n";
      
      entries.forEach(entry => {
        entry.lines.forEach(line => {
          const row = [
            entry.entry_number,
            entry.document_number,
            `${entry.accounting_date.substring(0, 2)}/${entry.accounting_date.substring(2, 4)}/${entry.accounting_date.substring(4, 6)}`,
            `${entry.doc_date.substring(0, 2)}/${entry.doc_date.substring(2, 4)}/${entry.doc_date.substring(4, 6)}`,
            line.account_number || "",
            line.account_name || "",
            line.debit ? line.debit.toFixed(2) : "",
            line.credit ? line.credit.toFixed(2) : ""
          ];
          
          // Escape commas in fields and wrap in quotes if needed
          const escapedRow = row.map(field => {
            if (typeof field === 'string' && (field.includes(',') || field.includes('"'))) {
              return `"${field.replace(/"/g, '""')}"`;
            }
            return field;
          });
          
          csvContent += escapedRow.join(',') + "\n";
        });
      });
      
      // Create and download the file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `libro_diario_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error generating CSV:", error);
      alert("Error al generar el archivo CSV.");
    } finally {
      setDownloadLoading(prev => ({ ...prev, csv: false }));
    }
  };

  const handleDownloadExcel = () => {
    // Función para convertir datos de sumas y saldos a Excel real
    if (!sumasSaldosData || sumasSaldosData.length === 0) return;

    setDownloadLoading(prev => ({ ...prev, excel: true }));
    
    try {
      // Usar SheetJS para crear un archivo Excel real
      import('xlsx').then((XLSX) => {
        // Preparar datos para Excel
        const excelData = [
          // Headers
          [
            'Sociedad',
            'Cuenta',
            'Descripción',
            'Moneda',
            'Divisa',
            'Arrastre',
            'Saldo Anterior',
            'Debe Período',
            'Haber Período',
            'Saldo Acumulado'
          ],
          // Data rows
          ...sumasSaldosData.map(record => [
            record.sociedad || "",
            record.cuenta || "",
            record.descripcion || "",
            record.moneda || "",
            record.divisa || "",
            record.arrastre || 0,
            record.saldoAnterior || 0,
            record.debe || 0,
            record.haber || 0,
            record.saldoAcumulado || 0
          ])
        ];

        // Crear workbook y worksheet
        const workbook = XLSX.utils.book_new();
        const worksheet = XLSX.utils.aoa_to_sheet(excelData);

        // Configurar anchos de columnas
        const columnWidths = [
          { wch: 10 }, // Sociedad
          { wch: 15 }, // Cuenta
          { wch: 40 }, // Descripción
          { wch: 8 },  // Moneda
          { wch: 8 },  // Divisa
          { wch: 15 }, // Arrastre
          { wch: 15 }, // Saldo Anterior
          { wch: 15 }, // Debe Período
          { wch: 15 }, // Haber Período
          { wch: 15 }  // Saldo Acumulado
        ];
        worksheet['!cols'] = columnWidths;

        // Aplicar formato a los headers
        const headerRange = XLSX.utils.decode_range(worksheet['!ref']);
        for (let col = headerRange.s.c; col <= headerRange.e.c; col++) {
          const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
          if (!worksheet[cellAddress]) continue;
          
          // Estilo de header (bold y fondo)
          worksheet[cellAddress].s = {
            font: { bold: true },
            fill: { fgColor: { rgb: "DDDDDD" } },
            alignment: { horizontal: "center" }
          };
        }

        // Aplicar formato a las celdas numéricas
        for (let row = 1; row <= headerRange.e.r; row++) {
          for (let col = 5; col <= 9; col++) { // Columnas numéricas (Arrastre a Saldo Acumulado)
            const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
            if (!worksheet[cellAddress]) continue;
            
            // Formato numérico con 2 decimales
            worksheet[cellAddress].z = '#,##0.00';
          }
        }

        // Agregar la hoja al workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, "Sumas y Saldos");

        // Agregar metadatos al archivo
        workbook.Props = {
          Title: "Sumas y Saldos",
          Subject: "Archivo de Sumas y Saldos",
          Author: "SmartAudit",
          CreatedDate: new Date()
        };

        // Generar y descargar el archivo
        const fileName = `sumas_saldos_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(workbook, fileName);

        setDownloadLoading(prev => ({ ...prev, excel: false }));
      }).catch(error => {
        console.error("Error loading XLSX library:", error);
        
        // Fallback a CSV si no se puede cargar XLSX
        const csvContent = "Sociedad,Cuenta,Descripción,Moneda,Divisa,Arrastre,Saldo Anterior,Debe Período,Haber Período,Saldo Acumulado\n" +
          sumasSaldosData.map(record => [
            record.sociedad || "",
            record.cuenta || "",
            `"${(record.descripcion || "").replace(/"/g, '""')}"`,
            record.moneda || "",
            record.divisa || "",
            (record.arrastre || 0).toFixed(2),
            (record.saldoAnterior || 0).toFixed(2),
            (record.debe || 0).toFixed(2),
            (record.haber || 0).toFixed(2),
            (record.saldoAcumulado || 0).toFixed(2)
          ].join(',')).join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `sumas_saldos_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        alert("No se pudo generar Excel, se descargó en formato CSV");
        setDownloadLoading(prev => ({ ...prev, excel: false }));
      });
    } catch (error) {
      console.error("Error generating Excel file:", error);
      alert("Error al generar el archivo Excel.");
      setDownloadLoading(prev => ({ ...prev, excel: false }));
    }
  };

  const getStatistics = () => {
    const stats = {
      libro: {
        asientos: entries ? entries.length : 0,
        lineas: entries ? entries.reduce((sum, entry) => sum + (entry.lines ? entry.lines.length : 0), 0) : 0
      },
      sumas: {
        cuentas: sumasSaldosData ? sumasSaldosData.length : 0,
        totalDebe: sumasSaldosData ? sumasSaldosData.reduce((sum, record) => sum + (record.debe || 0), 0) : 0,
        totalHaber: sumasSaldosData ? sumasSaldosData.reduce((sum, record) => sum + Math.abs(record.haber || 0), 0) : 0
      }
    };
    return stats;
  };

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

  const stats = getStatistics();

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h3 className="text-2xl font-semibold text-gray-800 mb-6">Resultados de la importación</h3>
      
      <div className="space-y-8">
        {/* Estadísticas generales */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
            <h4 className="font-semibold text-purple-800 mb-3 flex items-center">
              <FileText className="mr-2" size={20} />
              Libro Diario
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Asientos procesados:</span>
                <span className="font-semibold text-gray-900">{stats.libro.asientos.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Líneas contables:</span>
                <span className="font-semibold text-gray-900">{stats.libro.lineas.toLocaleString()}</span>
              </div>
              {data && data.accounting_date_range && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Período contable:</span>
                  <span className="font-semibold text-gray-900">{data.accounting_date_range}</span>
                </div>
              )}
            </div>
          </div>

          {sumasSaldosData && sumasSaldosData.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-3 flex items-center">
                <FileSpreadsheet className="mr-2" size={20} />
                Sumas y Saldos
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Cuentas procesadas:</span>
                  <span className="font-semibold text-gray-900">{stats.sumas.cuentas.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total debe período:</span>
                  <span className="font-semibold text-green-700">{stats.sumas.totalDebe.toLocaleString('es-ES', {minimumFractionDigits: 2})} €</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total haber período:</span>
                  <span className="font-semibold text-red-700">{stats.sumas.totalHaber.toLocaleString('es-ES', {minimumFractionDigits: 2})} €</span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Sección de descarga */}
        <div className="border-t pt-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center">
            <Download className="mr-2" size={20} />
            Exportar datos procesados
          </h4>
          <p className="text-sm text-gray-600 mb-6">
            Los datos han sido procesados correctamente. Puedes descargar los archivos en los formatos disponibles.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Descarga Libro Diario */}
            {entries && entries.length > 0 && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h5 className="font-medium text-gray-800">Libro Diario</h5>
                    <p className="text-xs text-gray-500">Formato CSV con estructura tabular</p>
                  </div>
                  <FileText className="text-purple-600" size={24} />
                </div>
                
                <button
                  onClick={handleDownloadCSV}
                  disabled={downloadLoading.csv}
                  className="w-full bg-purple-700 text-white px-4 py-2 rounded-lg hover:bg-purple-800 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {downloadLoading.csv ? (
                    <>
                      <Loader size={16} className="animate-spin" />
                      Generando CSV...
                    </>
                  ) : (
                    <>
                      <Download size={16} />
                      Descargar CSV
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Descarga Sumas y Saldos */}
            {sumasSaldosData && sumasSaldosData.length > 0 && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h5 className="font-medium text-gray-800">Sumas y Saldos</h5>
                    <p className="text-xs text-gray-500">Formato Excel con estructura contable</p>
                  </div>
                  <FileSpreadsheet className="text-green-600" size={24} />
                </div>
                
                <button
                  onClick={handleDownloadExcel}
                  disabled={downloadLoading.excel}
                  className="w-full bg-green-700 text-white px-4 py-2 rounded-lg hover:bg-green-800 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {downloadLoading.excel ? (
                    <>
                      <Loader size={16} className="animate-spin" />
                      Generando Excel...
                    </>
                  ) : (
                    <>
                      <FileSpreadsheet size={16} />
                      Descargar Excel
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Información adicional */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-semibold text-blue-800 mb-3 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Proceso completado
          </h4>
          <div className="space-y-2 text-sm text-blue-700">
            <p>• Los datos han sido importados y validados correctamente</p>
            <p>• Los archivos están disponibles para descarga en los formatos correspondientes</p>
            <p>• Puedes utilizar los módulos de análisis desde la página principal para operaciones avanzadas</p>
            {data && data.summary && data.summary.length > 0 && (
              <p>• Resumen de actividad generado con {data.summary.length} usuario(s) identificado(s)</p>
            )}
          </div>
        </div>
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
          onClick={onFinish}
          className="bg-purple-700 text-white px-6 py-3 rounded-lg hover:bg-purple-800 transition"
        >
          Finalizar
        </button>
      </div>
    </div>
  );
};

export default ImportacionStep3;