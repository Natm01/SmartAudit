// frontend/src/components/importacion/ImportacionStep1.jsx
import React, { useState, useEffect } from 'react';
import { Upload, Trash2, ArrowRight, AlertCircle, Eye, FileText, Download, CheckCircle, Clock, XCircle } from 'lucide-react';
import { uploadFiles } from '../../services/api';

const ImportacionStep1 = ({ formData, onFormChange, onUploadSuccess, onNext }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detailedError, setDetailedError] = useState(null);
  const [showHistory, setShowHistory] = useState(true);

  // Mock data para el historial de importaciones
  const importHistory = [
    {
      id: 1,
      herramienta: "Importación libro diario",
      proyecto: "12345-ACME-Auditoría cuentas anuales (24-25)",
      fecha: "15/03/2025 12:43:30",
      usuario: "María García",
      ejercicio: "31/12/2024",
      periodo: "01/01/2024-31/12/2024",
      parametros: "N/A",
      resultado: "exito", // exito, warning, error
      tooltip: "Importación completada exitosamente"
    },
    {
      id: 2,
      herramienta: "Importación libro diario",
      proyecto: "12345-ACME-Auditoría cuentas anuales (24-25)",
      fecha: "15/03/2025 10:00:03",
      usuario: "María García",
      ejercicio: "31/12/2024",
      periodo: "01/01/2024-31/12/2024",
      parametros: "N/A",
      resultado: "warning",
      tooltip: "Importación con advertencias menores"
    },
    {
      id: 3,
      herramienta: "Importación libro diario",
      proyecto: "12345-ACME-Auditoría cuentas anuales (24-25)",
      fecha: "15/03/2025 09:05:00",
      usuario: "María García",
      ejercicio: "31/12/2024",
      periodo: "01/01/2024-31/12/2024",
      parametros: "N/A",
      resultado: "error",
      tooltip: "Error en validación de archivos"
    },
    {
      id: 4,
      herramienta: "Importación libro diario",
      proyecto: "23456-TEST-Auditoría cuentas anuales (24-25)",
      fecha: "11/11/2024 10:43:00",
      usuario: "Juan Pérez",
      ejercicio: "31/12/2024",
      periodo: "01/01/2024-30/09/2024",
      parametros: "N/A",
      resultado: "exito",
      tooltip: "Proceso completado"
    },
    {
      id: 5,
      herramienta: "Importación libro diario",
      proyecto: "23456-TEST-Auditoría cuentas anuales (24-25)",
      fecha: "12/02/2024 18:13:34",
      usuario: "Paula Pérez",
      ejercicio: "31/12/2024",
      periodo: "01/01/2024-31/12/2024",
      parametros: "N/A",
      resultado: "exito",
      tooltip: "Importación exitosa"
    }
  ];

  // Project options from your specifications
  const projectOptions = [
    { id: "00041796", name: "HOTELES TURISTICOS UNIDOS, S.A.", type: "Audit CCAA individuales obligatoria", year: "24-25" },
    { id: "00041708", name: "GRUP FLASH RABAT, S.L.", type: "Audit CCAA consolidadas obligatoria", year: "24-25" },
    { id: "00042009", name: "GRUP INUIT, S.A.", type: "Auditoría de cuentas anuales", year: "24-25" }
  ];

  useEffect(() => {
    // Auto-set year to 2024 when project changes
    if (formData.project && !formData.year) {
      onFormChange({ year: "2024" });
    }
  }, [formData.project, formData.year, onFormChange]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onFormChange({ [name]: value });
  };

  const handleFileSelection = (e, fileType) => {
    if (e.target.files && e.target.files.length > 0) {
      try {
        const filesArray = Array.from(e.target.files).map(file => ({
          name: file.name,
          size: (file.size / 1024).toFixed(2) + ' KB',
          type: file.type,
          file // Guardar el archivo para subir después
        }));
        
        if (fileType === 'libro') {
          onFormChange({ libroFiles: [...formData.libroFiles, ...filesArray] });
        } else if (fileType === 'sumas') {
          onFormChange({ sumasFiles: [...formData.sumasFiles, ...filesArray] });
        }
      } catch (err) {
        console.error("Error processing files:", err);
        setError("Error al procesar los archivos seleccionados.");
      }
    }
  };

  const removeFile = (index, fileType) => {
    if (fileType === 'libro') {
      const newFiles = [...formData.libroFiles];
      newFiles.splice(index, 1);
      onFormChange({ libroFiles: newFiles });
    } else if (fileType === 'sumas') {
      const newFiles = [...formData.sumasFiles];
      newFiles.splice(index, 1);
      onFormChange({ sumasFiles: newFiles });
    }
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

  const getResultIcon = (resultado) => {
    switch (resultado) {
      case 'exito':
        return <CheckCircle className="text-green-500" size={18} />;
      case 'warning':
        return <Clock className="text-yellow-500" size={18} />;
      case 'error':
        return <XCircle className="text-red-500" size={18} />;
      default:
        return <CheckCircle className="text-gray-400" size={18} />;
    }
  };

  const handleDownloadSample = () => {
    // Generar archivo CSV de ejemplo con libro diario inventado
    const sampleData = [
      // Headers
      "Nº Asiento,Nº Documento,Fecha Contable,Fecha Documento,Cuenta,Descripción,Debe,Haber",
      // Asientos de ejemplo
      "00000001,0100000001,01/01/24,01/01/24,57200001,BANCOS,15000.00,",
      "00000001,0100000001,01/01/24,01/01/24,10000000,CAPITAL SOCIAL,,15000.00",
      "00000002,0100000002,02/01/24,02/01/24,60000000,COMPRAS,2500.50,",
      "00000002,0100000002,02/01/24,02/01/24,47200000,I.V.A. SOPORTADO,525.11,",
      "00000002,0100000002,02/01/24,02/01/24,40000001,PROVEEDORES,,3025.61",
      "00000003,0100000003,05/01/24,05/01/24,43000001,CLIENTES,4800.00,",
      "00000003,0100000003,05/01/24,05/01/24,47700000,I.V.A. REPERCUTIDO,,1008.00",
      "00000003,0100000003,05/01/24,05/01/24,70000000,VENTAS,,3792.00",
      "00000004,0100000004,10/01/24,10/01/24,40000001,PROVEEDORES,3025.61,",
      "00000004,0100000004,10/01/24,10/01/24,57200001,BANCOS,,3025.61",
      "00000005,0100000005,15/01/24,15/01/24,57200001,BANCOS,4800.00,",
      "00000005,0100000005,15/01/24,15/01/24,43000001,CLIENTES,,4800.00",
      "00000006,0100000006,20/01/24,20/01/24,62100000,GASTOS DE PERSONAL,3500.00,",
      "00000006,0100000006,20/01/24,20/01/24,64000000,GASTOS DE PERSONAL,,3500.00",
      "00000007,0100000007,25/01/24,25/01/24,62500000,SERVICIOS PROFESIONALES,1200.00,",
      "00000007,0100000007,25/01/24,25/01/24,47200000,I.V.A. SOPORTADO,252.00,",
      "00000007,0100000007,25/01/24,25/01/24,41000001,ACREEDORES,,1452.00",
      "00000008,0100000008,28/01/24,28/01/24,47700000,I.V.A. REPERCUTIDO,1008.00,",
      "00000008,0100000008,28/01/24,28/01/24,47200000,I.V.A. SOPORTADO,777.11,",
      "00000008,0100000008,28/01/24,28/01/24,47500000,I.V.A. A INGRESAR,,230.89",
      "00000009,0100000009,30/01/24,30/01/24,64000000,GASTOS DE PERSONAL,3500.00,",
      "00000009,0100000009,30/01/24,30/01/24,57200001,BANCOS,,3500.00",
      "00000010,0100000010,31/01/24,31/01/24,41000001,ACREEDORES,1452.00,",
      "00000010,0100000010,31/01/24,31/01/24,57200001,BANCOS,,1452.00"
    ];

    const csvContent = sampleData.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `libro_diario_ejemplo_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setDetailedError(null);
    
    try {
      // Validación básica
      if (!formData.project) {
        throw new Error('Por favor, selecciona un proyecto');
      }
      
      if (!formData.year) {
        throw new Error('Por favor, selecciona un ejercicio');
      }
      
      if (!formData.startDate || !formData.endDate) {
        throw new Error('Por favor, selecciona las fechas del periodo');
      }
      
      if (formData.libroFiles.length === 0) {
        throw new Error('Por favor, selecciona al menos un archivo de libro diario');
      }
      
      // Preparar FormData para la subida
      const uploadFormData = new FormData();
      uploadFormData.append('project', formData.project);
      uploadFormData.append('year', formData.year);
      uploadFormData.append('start_date', formData.startDate);
      uploadFormData.append('end_date', formData.endDate);
      
      // Agregar archivos de libro diario
      formData.libroFiles.forEach((fileObj, index) => {
        if (fileObj.file) {
          uploadFormData.append(`libro_diario_files`, fileObj.file);
        } else {
          console.warn(`File object at index ${index} doesn't have a file property`);
        }
      });
      
      // Agregar archivos de sumas y saldos si existen
      if (formData.sumasFiles.length > 0) {
        formData.sumasFiles.forEach((fileObj, index) => {
          if (fileObj.file) {
            uploadFormData.append('sumas_saldos_files', fileObj.file);
          } else {
            console.warn(`Sumas File object at index ${index} doesn't have a file property`);
          }
        });
      }
      
      // Debug output to verify FormData contents
      for (let pair of uploadFormData.entries()) {
        console.log(pair[0] + ': ' + (pair[1] instanceof File ? pair[1].name : pair[1]));
      }
      
      // Enviar datos al servidor
      const response = await uploadFiles(uploadFormData);
      console.log("Upload response:", response);
      
      // Notificar éxito
      if (response && response.temp_dir) {
        onUploadSuccess(response);
      } else {
        throw new Error("Respuesta incompleta del servidor");
      }
    } catch (err) {
      // Mostrar error detallado
      console.error("Error completo al subir:", err);
      
      // Mostrar mensaje de error simplificado
      setError("Error al subir archivos");
      
      // Guardar error detallado
      setDetailedError(err.message || "Error desconocido en la subida de archivos");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Formulario de importación - Diseño original */}
      <div className="bg-white rounded-lg shadow-md p-8">
        <h3 className="text-xl font-medium text-gray-800 mb-6">Selecciona los datos a importar</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Project and Year in the same row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="project" className="block text-sm font-medium text-gray-700 mb-2">Proyecto</label>
                <select
                  id="project"
                  name="project"
                  className="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition"
                  value={formData.project}
                  onChange={handleInputChange}
                >
                  <option value="">Seleccionar proyecto</option>
                  {projectOptions.map(project => (
                    <option key={project.id} value={project.id}>
                      {project.id} | {project.name} | {project.type} | {project.year}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">Ejercicio</label>
                <select
                  id="year"
                  name="year"
                  className="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition"
                  value={formData.year}
                  onChange={handleInputChange}
                  disabled // Disabled as it's auto-set based on project
                >
                  <option value="2024">2024</option>
                  <option value="2023">2023</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Periodo</label>
              <div className="flex gap-4">
                <input 
                  type="date"
                  name="startDate"
                  className="flex-1 rounded-md border border-gray-300 p-2"
                  value={formData.startDate}
                  onChange={handleInputChange}
                />
                <span className="flex items-center">a</span>
                <input 
                  type="date"
                  name="endDate"
                  className="flex-1 rounded-md border border-gray-300 p-2"
                  value={formData.endDate}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Libro diario</label>
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
                      onChange={(e) => handleFileSelection(e, 'libro')}
                    />
                  </label>
                </div>
              </div>
              
              {formData.libroFiles.length > 0 && (
                <div className="mt-2">
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {formData.libroFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-white p-2 rounded-md border border-gray-200 text-sm">
                        <div className="flex items-center">
                          {getFileIcon(file.name)}
                          <span className="truncate max-w-xs">{file.name}</span>
                          <span className="text-gray-500 ml-2">({file.size})</span>
                        </div>
                        <button 
                          type="button"
                          onClick={() => removeFile(index, 'libro')}
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
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sumas y saldos</label>
              <div className="border border-dashed border-gray-300 rounded-md p-3 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 text-purple-700">
                      <Upload size={20} />
                    </div>
                    <div className="flex-grow">
                      <p className="text-sm text-gray-600">Selecciona archivos CSV, TXT, XLSX, XLS</p>
                    </div>
                  </div>
                  <label className="cursor-pointer bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition text-sm">
                    Archivo
                    <input 
                      type="file"
                      accept=".csv,.txt,.xlsx,.xls"
                      className="hidden"
                      onChange={(e) => handleFileSelection(e, 'sumas')}
                    />
                  </label>
                </div>
              </div>
              
              {formData.sumasFiles.length > 0 && (
                <div className="mt-2">
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {formData.sumasFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-white p-2 rounded-md border border-gray-200 text-sm">
                        <div className="flex items-center">
                          {getFileIcon(file.name)}
                          <span className="truncate max-w-xs">{file.name}</span>
                          <span className="text-gray-500 ml-2">({file.size})</span>
                        </div>
                        <button 
                          type="button"
                          onClick={() => removeFile(index, 'sumas')}
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
            
            {error && (
              <div className="p-4 mt-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-start">
                  <AlertCircle className="text-red-500 mr-2 flex-shrink-0 mt-0.5" size={18} />
                  <div>
                    <p className="text-red-600 font-medium">{error}</p>
                    {detailedError && (
                      <p className="text-red-500 text-sm mt-1">Detalles: {detailedError}</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-8 flex justify-end">
            <button 
              type="submit"
              disabled={isLoading}
              className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Cargando...
                </>
              ) : (
                <>
                  Siguiente
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Historial de importaciones - Movido abajo y más pequeño */}
      {showHistory && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-medium text-gray-800">Historial de importaciones recientes</h4>
            <button
              onClick={() => setShowHistory(false)}
              className="text-gray-400 hover:text-gray-600 text-sm"
            >
              Ocultar
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Herramienta</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proyecto</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ejercicio</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Período</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Parámetros</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resultado</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {importHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-900">{item.herramienta}</td>
                    <td className="px-3 py-2 text-gray-900 max-w-xs truncate">{item.proyecto}</td>
                    <td className="px-3 py-2 text-gray-500">{item.fecha}</td>
                    <td className="px-3 py-2 text-gray-900">{item.usuario}</td>
                    <td className="px-3 py-2 text-gray-500">{item.ejercicio}</td>
                    <td className="px-3 py-2 text-gray-500">{item.periodo}</td>
                    <td className="px-3 py-2 text-gray-500">{item.parametros}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center" title={item.tooltip}>
                        {getResultIcon(item.resultado)}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center space-x-2">
                        <button
                          title="Visualización de la ejecución"
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          title="Informe de la ejecución"
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <FileText size={14} />
                        </button>
                        <button
                          onClick={handleDownloadSample}
                          title="Descargar resultados de la ejecución"
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Download size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Botón para mostrar historial si está oculto */}
      {!showHistory && (
        <div className="text-center">
          <button
            onClick={() => setShowHistory(true)}
            className="text-purple-600 hover:text-purple-800 text-sm"
          >
            Mostrar historial de importaciones
          </button>
        </div>
      )}
    </div>
  );
};

export default ImportacionStep1;