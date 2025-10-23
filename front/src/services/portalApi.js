// frontend/src/services/portalApi.js
import axios from 'axios';
import config from '../config/env';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig, loginRequest } from '../context/authConfig';

const PORTAL_API_BASE_URL = config.portalApiUrl;

// Crear instancia de MSAL para obtener tokens
let msalInstance = null;

const getMsalInstance = () => {
  if (!msalInstance) {
    msalInstance = new PublicClientApplication(msalConfig);
  }
  return msalInstance;
};

// Crear instancia de axios para Portal API
const portalApi = axios.create({
  baseURL: PORTAL_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
});

// Interceptor para agregar el token de autenticación
portalApi.interceptors.request.use(
  async (requestConfig) => {
    try {
      const instance = getMsalInstance();
      await instance.initialize();

      const accounts = instance.getAllAccounts();

      if (accounts.length > 0) {
        // Obtener token silenciosamente
        const response = await instance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0]
        });

        // Agregar token al header
        requestConfig.headers.Authorization = `Bearer ${response.idToken}`;
      }

      if (config.isDevelopment) {
        console.log('Portal API Request:', requestConfig.method?.toUpperCase(), requestConfig.url);
        console.log('Full URL:', `${PORTAL_API_BASE_URL}${requestConfig.url}`);
      }
    } catch (error) {
      console.error('Error obteniendo token:', error);
    }

    return requestConfig;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para responses
portalApi.interceptors.response.use(
  (response) => {
    if (config.isDevelopment) {
      console.log('Portal API Response:', response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    console.error('Portal API Error:', error.message);

    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);

      switch (error.response.status) {
        case 401:
          error.message = 'No autorizado. Token inválido o expirado.';
          break;
        case 403:
          error.message = 'Acceso denegado';
          break;
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
      error.message = `No se pudo conectar con el servidor en ${PORTAL_API_BASE_URL}`;
    }

    return Promise.reject(error);
  }
);

export default portalApi;
