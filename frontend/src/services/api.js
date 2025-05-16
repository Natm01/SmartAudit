// frontend/src/services/api.js

// Use relative URL for same-origin deployments or set based on environment
const API_URL = process.env.REACT_APP_API_URL || '/api';

/**
 * Sube archivos de libro diario y sumas y saldos al servidor
 * @param {FormData} formData - Datos del formulario
 * @returns {Promise<Object>} - Respuesta del servidor
 */
export const uploadFiles = async (formData) => {
  try {
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
      // Include credentials if using cookies for authentication
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error al subir archivos' }));
      throw new Error(errorData.detail || 'Error al subir archivos');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error en uploadFiles:', error);
    throw error;
  }
};

/**
 * Valida los archivos subidos
 * @param {FormData} formData - Datos para validación
 * @returns {Promise<Object>} - Resultados de validación
 */
export const validateFiles = async (formData) => {
  try {
    const response = await fetch(`${API_URL}/validate`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error en la validación' }));
      throw new Error(errorData.detail || 'Error en la validación');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error en validateFiles:', error);
    throw error;
  }
};

/**
 * Procesa los archivos validados
 * @param {FormData} formData - Datos para procesamiento
 * @returns {Promise<Object>} - Resultados del procesamiento
 */
export const processFiles = async (formData) => {
  try {
    const response = await fetch(`${API_URL}/process`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error en el procesamiento' }));
      throw new Error(errorData.detail || 'Error en el procesamiento');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error en processFiles:', error);
    throw error;
  }
};