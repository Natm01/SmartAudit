// frontend/src/components/analisis-obsolescencia/AnalisisObsolescenciaStep1.jsx
import React from 'react';
import { ArrowRight, Trash2, Upload } from 'lucide-react';

const AnalisisObsolescenciaStep1 = ({ formData, onInputChange, isLoading, onNext }) => {
  const projectOptions = [
    { id: "00041796", name: "HOTELES TURISTICOS UNIDOS, S.A." },
    { id: "00041708", name: "GRUP FLASH RABAT, S.L." },
    { id: "00042009", name: "GRUP INUIT, S.A." }
  ];

  const timeUnitOptions = [
    { value: 'dias', label: 'Días' },
    { value: 'semanas', label: 'Semanas' },
    { value: 'meses', label: 'Meses' },
    { value: 'años', label: 'Años' }
  ];

  const handleFileSelection = (fileType, e) => {
    if (e.target.files && e.target.files.length > 0) {
      try {
        const filesArray = Array.from(e.target.files).map(file => ({
          name: file.name,
          size: (file.size / 1024).toFixed(2) + ' KB',
          type: file.type,
          file: file
        }));
        
        onInputChange(`files.${fileType}`, [...formData.files[fileType], ...filesArray]);
      } catch (err) {
        console.error("Error processing files:", err);
      }
    }
  };

  const removeFile = (fileType, index) => {
    const newFiles = [...formData.files[fileType]];
    newFiles.splice(index, 1);
    onInputChange(`files.${fileType}`, newFiles);
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

  const canProceed = () => {
    return formData.project && 
           formData.period.start && 
           formData.period.end && 
           formData.obsolescence.value && 
           formData.obsolescence.unit &&
           formData.files.transactions.length > 0;
  };

  // File sections mapping for the import step
  const fileSections = [
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
    <div className="bg-white rounded-lg shadow-md p-8">
      <h3 className="text-xl font-medium text-gray-800 mb-6">Selecciona los datos a importar</h3>
      
      <div className="space-y-6">

        <div className="grid grid-cols-12 gap-4 mb-6">
          {/* Project selection */}
          <div className="col-span-6">
            <label htmlFor="project" className="block text-sm font-medium text-gray-700 mb-2">Proyecto</label>
            <select
              id="project"
              name="project"
              className="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition"
              value={formData.project}
              onChange={(e) => onInputChange('project', e.target.value)}
            >
              <option value="">Seleccionar proyecto</option>
              {projectOptions.map(project => (
                <option key={project.id} value={project.id}>
                  {project.id} - {project.name}
                </option>
              ))}
            </select>
          </div>

          {/* Year selection */}
          <div className="col-span-1">
            <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">Ejercicio</label>
            <select
              id="year"
              name="year"
              className="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition"
              value={formData.year}
              onChange={(e) => onInputChange('year', e.target.value)}
            >
              <option value="2024">2024</option>
              <option value="2023">2023</option>
            </select>
          </div>

          {/* Period selection */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-2">Período</label>
            <div className="flex gap-2 items-center">
              <input 
                type="date"
                name="startDate"
                className="flex-1 rounded-md border border-gray-300 p-2 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                value={formData.period.start}
                onChange={(e) => onInputChange('period.start', e.target.value)}
              />
              <span className="text-gray-500 text-sm">a</span>
              <input 
                type="date"
                name="endDate"
                className="flex-1 rounded-md border border-gray-300 p-2 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                value={formData.period.end}
                onChange={(e) => onInputChange('period.end', e.target.value)}
              />
            </div>
          </div>

          {/* Obsolescence criteria */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Criterios de obsolescencia</label>
            <div className="flex gap-2 items-center">
              <div className="flex-1">
                <input 
                  type="number"
                  id="obsolescenceValue"
                  min="1"
                  placeholder="18"
                  className="w-full rounded-md border border-gray-300 p-2 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  value={formData.obsolescence.value}
                  onChange={(e) => onInputChange('obsolescence.value', e.target.value)}
                />
              </div>
              <div className="flex-1">
                <select
                  id="obsolescenceUnit"
                  className="w-full rounded-md border border-gray-300 p-2 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  value={formData.obsolescence.unit}
                  onChange={(e) => onInputChange('obsolescence.unit', e.target.value)}
                >
                  {timeUnitOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {formData.obsolescence.value && formData.obsolescence.unit ? (
                <>Sin movimiento durante {formData.obsolescence.value} {formData.obsolescence.unit}</>
              ) : 'Tiempo para considerar obsoleto'}
            </p>
          </div>
        </div>
        
        {/* File uploads */}
        {fileSections.map((section) => (
          <div key={section.key}>
            <label className="block text-sm font-medium text-gray-700 mb-2">{section.label}</label>
            <div className="border border-dashed border-gray-300 rounded-md p-3 bg-white/90">
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
                    {formData.files[section.key]?.length === 0 ? (
                          <p className="text-sm text-gray-600">Selecciona archivos CSV, TXT, XLSX, XLS</p>
                        ) : (
                          <div className="space-y-1 max-h-28 overflow-y-auto pr-2">
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
                    )}
                  </div>
                </div>
                <label className="cursor-pointer bg-purple-700 text-white px-2 py-1.5 rounded-md hover:bg-purple-800 transition text-xs">
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
          </div>
        ))}
      </div>
      
      <div className="mt-8 flex justify-end">
        <button 
          onClick={onNext}
          disabled={!canProceed() || isLoading}
          className="bg-purple-700 text-white px-2 py-2 rounded-md hover:bg-purple-800 transition flex items-center text-sm gap-2 disabled:opacity-50 disabled:cursor-not-allowe"
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
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default AnalisisObsolescenciaStep1;