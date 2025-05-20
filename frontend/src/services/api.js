const API_BASE_URL = 'http://localhost:8080/api';
// Función de ayuda para manejar respuestas de la API
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorText = await response.text();
    try {
      const errorData = JSON.parse(errorText);
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    } catch {
      throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
    }
  }
  return response.json();
};

// Función de ayuda para manejar errores de red
const handleNetworkError = (error) => {
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    throw new Error('Error de conexión. Verifique su conexión a internet y que el servidor esté ejecutándose.');
  }
  throw error;
};

// Subir archivos al servidor
export const uploadFiles = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    return await handleResponse(response);
  } catch (error) {
    handleNetworkError(error);
  }
};

// Validar archivos
export const validateFiles = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/validate`, {
      method: 'POST',
      body: formData,
    });
    return await handleResponse(response);
  } catch (error) {
    handleNetworkError(error);
  }
};

// Procesar archivos
export const processFiles = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      body: formData,
    });
    return await handleResponse(response);
  } catch (error) {
    handleNetworkError(error);
  }
};

// Obtener datos de previsualización (simulado para desarrollo)
export const getPreviewData = async (tempDir, fileType = 'libro') => {
  try {
    // En un entorno de producción, esto haría una llamada real al backend
    // Para desarrollo, retornamos datos mockeados
    if (fileType === 'libro') {
      return {
        entries: generateMockLibroEntries(),
        total: 150
      };
    } else if (fileType === 'sumas') {
      return {
        records: generateMockSumasSaldosRecords(),
        total: 471
      };
    }
  } catch (error) {
    handleNetworkError(error);
  }
};

// Función auxiliar para generar entradas de libro diario mockeadas
const generateMockLibroEntries = () => {
  const entries = [];
  for (let i = 1; i <= 10; i++) {
    const entry = {
      entry_number: `0000000${i}`,
      document_number: `010000000${i}`,
      accounting_date: '010124',
      doc_date: '010124',
      header_text: i % 2 === 0 ? 'Cobros por Tarjeta' : 'Pagos Diversos',
      lines: [
        {
          account_name: 'PASARELA PAGO EXPOS.',
          account_number: '57200001',
          debit: i * 1000.28,
          credit: 0
        },
        {
          account_name: i % 2 === 0 ? 'SANTIAGO GUIJARRO' : 'KEDECORAS S.L.',
          account_number: '43000043',
          debit: 0,
          credit: i * 1000.28
        }
      ]
    };
    entries.push(entry);
  }
  return entries;
};

// Función auxiliar para generar registros de sumas y saldos mockeados
const generateMockSumasSaldosRecords = () => {
  const records = [];
  const cuentas = [
    { cuenta: '10000000', descripcion: 'Capital social', arrastre: -412359.99 },
    { cuenta: '11200000', descripcion: 'Reserva legal', arrastre: -82472 },
    { cuenta: '11300000', descripcion: 'Reservas voluntarias', arrastre: -2022172.88 },
    { cuenta: '11800000', descripcion: 'Aportaciones de socios o propietarios', arrastre: -9200000 },
    { cuenta: '12100000', descripcion: 'Resultados negativos de ejercicios anteriores', arrastre: 9377086.6 },
    { cuenta: '20000000', descripcion: 'Inmovilizaciones intangibles', arrastre: 15000 },
    { cuenta: '21000000', descripcion: 'Inmovilizaciones materiales', arrastre: 850000 },
    { cuenta: '30000000', descripcion: 'Comerciales', arrastre: 45000 },
    { cuenta: '43000001', descripcion: 'Clientes', arrastre: 125000 },
    { cuenta: '57000000', descripcion: 'Tesorería', arrastre: 85000 }
  ];
  
  cuentas.forEach((cuenta, index) => {
    const debe = Math.random() > 0.7 ? Math.random() * 50000 : 0;
    const haber = Math.random() > 0.7 ? Math.random() * 50000 : 0;
    
    records.push({
      sociedad: 'AV00',
      cuenta: cuenta.cuenta,
      descripcion: cuenta.descripcion,
      moneda: 'EUR',
      divisa: '',
      arrastre: cuenta.arrastre,
      saldoAnterior: 0,
      debe: debe,
      haber: haber,
      saldoAcumulado: cuenta.arrastre + debe - haber
    });
  });
  
  return records;
};

// Descargar archivo de resultados
export const downloadResults = async (tempDir, format = 'csv') => {
  try {
    const response = await fetch(`${API_BASE_URL}/download/${tempDir}?format=${format}`, {
      method: 'GET',
    });
    
    if (!response.ok) {
      throw new Error(`Error al descargar: ${response.status}`);
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `resultados_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    handleNetworkError(error);
  }
};

// Limpiar archivos temporales
export const cleanupTempFiles = async (tempDir) => {
  try {
    const response = await fetch(`${API_BASE_URL}/cleanup/${tempDir}`, {
      method: 'DELETE',
    });
    return await handleResponse(response);
  } catch (error) {
    // No lanzar error para limpieza ya que es opcional
    console.warn('Error al limpiar archivos temporales:', error);
  }
};

// Obtener estadísticas de procesamiento
export const getProcessingStats = async (tempDir) => {
  try {
    const response = await fetch(`${API_BASE_URL}/stats/${tempDir}`, {
      method: 'GET',
    });
    return await handleResponse(response);
  } catch (error) {
    handleNetworkError(error);
  }
};

export default {
  uploadFiles,
  validateFiles,
  processFiles,
  getPreviewData,
  downloadResults,
  cleanupTempFiles,
  getProcessingStats
};