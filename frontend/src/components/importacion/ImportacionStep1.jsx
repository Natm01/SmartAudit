// frontend/src/components/importacion/ImportacionStep1.jsx
import React, { useState } from 'react';
import { Upload, Trash2, ArrowRight } from 'lucide-react';
import { uploadFiles } from '../../services/api';

const ImportacionStep1 = ({ formData, onFormChange, onUploadSuccess, onNext }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onFormChange({ [name]: value });
  };

  const handleFileSelection = (e, fileType) => {
    if (e.target.files) {
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
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
      formData.libroFiles.forEach((fileObj) => {
        uploadFormData.append('libro_diario_files', fileObj.file);
      });
      
      // Agregar archivos de sumas y saldos si existen
      if (formData.sumasFiles.length > 0) {
        formData.sumasFiles.forEach((fileObj) => {
          uploadFormData.append('sumas_saldos_files', fileObj.file);
        });
      }
      
      // Enviar datos al servidor
      const response = await uploadFiles(uploadFormData);
      
      // Notificar éxito
      onUploadSuccess(response);
    } catch (err) {
      setError(err.message || 'Error al subir los archivos');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Selecciona los datos a importar</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
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
              <option value="Proyecto A">Proyecto A</option>
              <option value="Proyecto B">Proyecto B</option>
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
            >
              <option value="">Seleccionar ejercicio</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
            </select>
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
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-700">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <div className="flex-grow">
                  <p className="text-sm text-gray-600">Selecciona archivos CSV, TXT, XLSX, XLS</p>
                </div>
                <label className="cursor-pointer text-xs bg-purple-700 text-white px-3 py-1.5 rounded-md hover:bg-purple-800 transition">
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
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {formData.libroFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-white p-1.5 rounded-md border border-gray-200 text-xs">
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
                        <Trash2 size={14} />
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
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  <Upload className="text-purple-700" size={20} />
                </div>
                <div className="flex-grow">
                  <p className="text-sm text-gray-600">Selecciona archivos CSV, TXT, XLSX, XLS</p>
                </div>
                <label className="cursor-pointer text-xs bg-purple-700 text-white px-3 py-1.5 rounded-md hover:bg-purple-800 transition">
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
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {formData.sumasFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-white p-1.5 rounded-md border border-gray-200 text-xs">
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
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
        </div>
        
        <div className="mt-8 flex justify-end">
          <button 
            type="submit"
            disabled={isLoading}
            className="bg-purple-700 text-white px-4 py-2 rounded-md hover:bg-purple-800 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Cargando...' : 'Siguiente'}
            {!isLoading && <ArrowRight size={16} />}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ImportacionStep1;