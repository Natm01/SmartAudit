/**
 * env.js
 *
 * Configuración centralizada de URLs y variables de entorno
 *
 * ARQUITECTURA:
 * - Detección automática del ambiente basada en hostname
 * - Permite sobrescribir con variables de entorno
 * - Exporta todas las URLs necesarias en la aplicación
 *
 * AMBIENTES:
 * - development: localhost
 * - dev: devapi.grantthornton.es
 * - test: testapi.grantthornton.es
 * - prod: api.grantthornton.es
 */

/**
 * Detecta el ambiente actual basado en NODE_ENV y hostname
 * @returns {'development' | 'dev' | 'test' | 'prod'}
 */
const getEnvironment = () => {
  // 1. Desarrollo local
  if (process.env.NODE_ENV === 'development') {
    return 'development';
  }

  // 2. Detección por hostname
  const hostname = window.location.hostname;

  if (hostname.includes('dev') || hostname.includes('purple-') || hostname.includes('dev-')) {
    return 'dev';
  } else if (hostname.includes('test') || hostname.includes('green-') || hostname.includes('test-')) {
    return 'test';
  } else {
    return 'prod';
  }
};

/**
 * Configuración de URLs por ambiente
 */
const API_URLS = {
  development: {
    proto: 'http://localhost:8001/smau-proto',
  },
  dev: {
    proto: 'https://devapi.grantthornton.es/smau-proto',
  },
  test: {
    proto: 'https://testapi.grantthornton.es/smau-proto',
  },
  prod: {
    proto: 'https://api.grantthornton.es/smau-proto',
  },
};

/**
 * Configuración de ThoughtSpot
 */
const THOUGHTSPOT_URLS = {
  development: 'https://gt-es.thoughtspot.cloud/',
  dev: 'https://gt-es.thoughtspot.cloud/',
  test: 'https://gt-es.thoughtspot.cloud/',
  prod: 'https://gt-es.thoughtspot.cloud/',
};

// Detectar ambiente actual
const environment = getEnvironment();

// Log del ambiente detectado (solo en desarrollo)
if (process.env.NODE_ENV === 'development') {
  console.log('🌍 Environment detected:', environment);
  console.log('📍 Hostname:', window.location.hostname);
}

/**
 * Configuración exportada
 */
const config = {
  // Ambiente actual
  environment,

  // URL del API Proto (SmartAudit Proto - /smau-proto)
  // Puede sobrescribirse con REACT_APP_PROTO_API_URL
  protoApiUrl: process.env.REACT_APP_PROTO_API_URL || API_URLS[environment].proto,

  // URL de ThoughtSpot
  // Puede sobrescribirse con REACT_APP_THOUGHTSPOT_HOST
  thoughtSpotHost: process.env.REACT_APP_THOUGHTSPOT_HOST || THOUGHTSPOT_URLS[environment],

  // Flags de desarrollo
  isDevelopment: environment === 'development',
  isDev: environment === 'dev',
  isTest: environment === 'test',
  isProd: environment === 'prod',
};

// Log de configuración (solo en desarrollo)
if (process.env.NODE_ENV === 'development') {
  console.log('⚙️ Config:', {
    environment: config.environment,
    protoApiUrl: config.protoApiUrl,
    thoughtSpotHost: config.thoughtSpotHost,
  });
}

export default config;
