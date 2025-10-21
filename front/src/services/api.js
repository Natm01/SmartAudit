// frontend/src/services/api.js
import axios from 'axios';
import config from '../config/env';

const API_BASE_URL = config.protoApiUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
});

// Interceptor para requests
api.interceptors.request.use(
  (requestConfig) => {
    if (config.isDevelopment) {
      console.log('API Request:', requestConfig.method?.toUpperCase(), requestConfig.url);
      console.log('Full URL:', `${API_BASE_URL}${requestConfig.url}`);
    }
    return requestConfig;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para responses
api.interceptors.response.use(
  (response) => {
    if (config.isDevelopment) {
      console.log('API Response:', response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    console.error('API Error:', error.message);
    console.error('Full error:', error);
    
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
      
      switch (error.response.status) {
        case 404:
          error.message = 'Recurso no encontrado';
          break;
        case 500:
          error.message = 'Error interno del servidor';
          break;
        case 503:
          error.message = 'Servicio no disponible';
          break;
      }
    } else if (error.request) {
      error.message = `No se pudo conectar con el servidor en ${API_BASE_URL}`;
    }
    
    return Promise.reject(error);
  }
);

export default api;