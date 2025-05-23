// frontend/src/services/api.js

// Validar y obtener la URL base de la API
const getApiBaseUrl = () => {
  const url = process.env.REACT_APP_API_URL;
  
  if (!url || url === 'undefined') {
    console.error('REACT_APP_API_URL no está definida o es undefined');
    console.log('Variables de entorno disponibles:', Object.keys(process.env).filter(key => key.startsWith('REACT_APP_')));
    
    // URL de fallback para desarrollo local
    const fallbackUrl = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8000' 
      : '';
    
    if (!fallbackUrl) {
      throw new Error('REACT_APP_API_URL no está configurada. Por favor, configura esta variable de entorno con la URL de tu backend.');
    }
    
    console.warn(`Usando URL de fallback: ${fallbackUrl}`);
    return fallbackUrl;
  }
  
  // Remover barra final si existe
  return url.replace(/\/$/, '');
};

const API_BASE_URL = getApiBaseUrl();

console.log('API_BASE_URL configurada:', API_BASE_URL);

class APIError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }
}

const handleApiResponse = async (response) => {
  let responseData;
  
  try {
    responseData = await response.json();
  } catch (e) {
    responseData = { detail: 'Error parsing response' };
  }

  if (!response.ok) {
    const errorMessage = responseData?.detail || `HTTP Error ${response.status}`;
    console.error('API Error:', {
      status: response.status,
      message: errorMessage,
      url: response.url,
      data: responseData
    });
    throw new APIError(errorMessage, response.status, responseData);
  }

  return responseData;
};

export const uploadFiles = async (formData) => {
  console.log('Uploading files to:', `${API_BASE_URL}/api/upload`);
  
  try {
    // Log form data contents for debugging
    for (let pair of formData.entries()) {
      if (pair[1] instanceof File) {
        console.log(`${pair[0]}: File - ${pair[1].name} (${pair[1].size} bytes)`);
      } else {
        console.log(`${pair[0]}: ${pair[1]}`);
      }
    }

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
    });

    const result = await handleApiResponse(response);
    console.log('Upload successful:', result);
    return result;
    
  } catch (error) {
    console.error('Upload failed:', error);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    // Handle network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new APIError('No se pudo conectar con el servidor. Verifique su conexión.', 0);
    }
    
    throw new APIError(error.message || 'Error desconocido durante la carga de archivos', 500);
  }
};

export const validateFilesWithStreaming = async (formData, onProgress) => {
  console.log('Starting streaming validation to:', `${API_BASE_URL}/api/validate-stream`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/validate-stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalResult = null;

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('Streaming validation completed');
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              console.log('Received progress update:', data);
              
              // Call progress callback
              if (onProgress) {
                onProgress(data);
              }
              
              // Store final result
              if (data.step === 'completed' && data.result) {
                finalResult = data.result;
              }
              
              // Handle errors
              if (data.error) {
                throw new Error(data.message || 'Error en la validación');
              }
              
            } catch (parseError) {
              console.warn('Error parsing JSON line:', line, parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    if (!finalResult) {
      throw new Error('No se recibió resultado de validación');
    }

    console.log('Streaming validation successful:', finalResult);
    return finalResult;
    
  } catch (error) {
    console.error('Streaming validation failed:', error);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    throw new APIError(error.message || 'Error desconocido durante la validación streaming', 500);
  }
};

export const validateFiles = async (formData) => {
  console.log('Validating files to:', `${API_BASE_URL}/api/validate`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/validate`, {
      method: 'POST',
      body: formData,
    });

    const result = await handleApiResponse(response);
    console.log('Validation successful:', result);
    return result;
    
  } catch (error) {
    console.error('Validation failed:', error);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    throw new APIError(error.message || 'Error desconocido durante la validación', 500);
  }
};

export const processFiles = async (formData) => {
  console.log('Processing files to:', `${API_BASE_URL}/api/process`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/process`, {
      method: 'POST',
      body: formData,
    });

    const result = await handleApiResponse(response);
    console.log('Processing successful:', result);
    return result;
    
  } catch (error) {
    console.error('Processing failed:', error);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    throw new APIError(error.message || 'Error desconocido durante el procesamiento', 500);
  }
};

export const getPreviewData = async (tempDir, fileType = 'libro') => {
  console.log(`Getting preview data for ${fileType} from ${tempDir}`);
  
  try {
    // Encode the temp directory path to handle special characters
    const encodedTempDir = encodeURIComponent(tempDir);
    
    const response = await fetch(
      `${API_BASE_URL}/api/preview/${encodedTempDir}?file_type=${fileType}`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      }
    );

    const result = await handleApiResponse(response);
    console.log(`Preview data for ${fileType}:`, result);
    return result;
    
  } catch (error) {
    console.error(`Preview data failed for ${fileType}:`, error);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    throw new APIError(error.message || 'Error obteniendo datos de previsualización', 500);
  }
};

export const cleanupTempFiles = async (tempDir) => {
  console.log('Cleaning up temporary files:', tempDir);
  
  try {
    if (!tempDir) {
      console.warn('No temp directory provided for cleanup');
      return { message: 'No directory provided', cleaned: false };
    }

    // Encode the temp directory path to handle special characters
    const encodedTempDir = encodeURIComponent(tempDir);
    
    const response = await fetch(`${API_BASE_URL}/api/cleanup/${encodedTempDir}`, {
      method: 'DELETE',
    });

    // For cleanup, we don't throw errors even if it fails (404, etc.)
    // since cleanup is not critical for the user flow
    if (response.ok) {
      const result = await response.json();
      console.log('Cleanup result:', result);
      return result;
    } else {
      console.warn(`Cleanup returned ${response.status}, but continuing...`);
      return { message: `Cleanup returned ${response.status}`, cleaned: false };
    }
    
  } catch (error) {
    console.warn('Cleanup failed (non-critical):', error);
    return { message: error.message, cleaned: false };
  }
};

// Health check function
export const healthCheck = async () => {
  console.log('Health check to:', `${API_BASE_URL}/api/health`);
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const result = await handleApiResponse(response);
    return result;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

// Test connection function
export const testConnection = async () => {
  console.log('Testing connection to:', `${API_BASE_URL}/api`);
  try {
    const response = await fetch(`${API_BASE_URL}/api`);
    const result = await handleApiResponse(response);
    return result;
  } catch (error) {
    console.error('Connection test failed:', error);
    throw error;
  }
};

// Export the APIError class for use in components
export { APIError };