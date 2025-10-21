# Configuración de Variables de Entorno

Este directorio contiene la configuración centralizada de variables de entorno para SmartAudit Frontend.

## Archivo Principal

### `env.js`

Configuración centralizada que detecta automáticamente el ambiente y exporta todas las URLs necesarias.

## Variables de Entorno Disponibles

### Sobrescrituras Opcionales

Puedes crear un archivo `.env` en la raíz del proyecto frontend para sobrescribir valores:

```bash
# API Proto (SmartAudit Proto - /smau-proto)
REACT_APP_PROTO_API_URL=https://custom-api.example.com/smau-proto

# API Portal (SmartAudit Portal - /smau-portal)
REACT_APP_PORTAL_API_URL=https://custom-api.example.com/smau-portal

# ThoughtSpot
REACT_APP_THOUGHTSPOT_HOST=https://custom-thoughtspot.cloud/
```

## Detección Automática de Ambiente

Si NO defines variables de entorno, el sistema detecta automáticamente el ambiente:

| Ambiente | Hostname | Proto API | Portal API |
|----------|----------|-----------|------------|
| **development** | localhost | `http://localhost:8001/smau-proto` | `http://localhost:8000/smau-portal` |
| **dev** | *dev*, *purple-*, *dev-* | `https://devapi.grantthornton.es/smau-proto` | `https://devapi.grantthornton.es/smau-portal` |
| **test** | *test*, *green-*, *test-* | `https://testapi.grantthornton.es/smau-proto` | `https://testapi.grantthornton.es/smau-portal` |
| **prod** | otros | `https://api.grantthornton.es/smau-proto` | `https://api.grantthornton.es/smau-portal` |

## Uso en el Código

### ✅ Correcto

```javascript
import config from '../config/env';

// Usar las URLs configuradas
const response = await fetch(`${config.portalApiUrl}/api/v1/users/me`);

// Verificar ambiente
if (config.isDevelopment) {
  console.log('Modo desarrollo');
}
```

### ❌ Incorrecto

```javascript
// NO hacer esto - las variables ya están centralizadas
const apiUrl = process.env.REACT_APP_API_URL;
```

## Propiedades Exportadas

El objeto `config` exporta:

```javascript
{
  // Ambiente actual
  environment: 'development' | 'dev' | 'test' | 'prod',

  // URLs de APIs
  protoApiUrl: string,    // URL del API Proto
  portalApiUrl: string,   // URL del API Portal
  thoughtSpotHost: string, // URL de ThoughtSpot

  // Flags booleanos
  isDevelopment: boolean,
  isDev: boolean,
  isTest: boolean,
  isProd: boolean,
}
```

## Migración desde Variables Antiguas

Si encuentras código antiguo que usa estas variables:

| Variable Antigua | Reemplazar con |
|-----------------|----------------|
| `REACT_APP_API_URL` | `config.protoApiUrl` |
| `REACT_APP_API_BASE_URL` | `config.protoApiUrl` |
| `REACT_APP_PORTAL_API_URL` | `config.portalApiUrl` |
| `REACT_APP_THOUGHTSPOT_HOST` | `config.thoughtSpotHost` |
| `process.env.NODE_ENV === 'development'` | `config.isDevelopment` |

## Ejemplo Completo

```javascript
// services/myService.js
import config from '../config/env';

const fetchData = async () => {
  // Usar Proto API
  const protoResponse = await fetch(`${config.protoApiUrl}/api/import/upload`);

  // Usar Portal API
  const portalResponse = await fetch(`${config.portalApiUrl}/api/v1/users/me`);

  // Logs solo en desarrollo
  if (config.isDevelopment) {
    console.log('Proto API:', config.protoApiUrl);
    console.log('Portal API:', config.portalApiUrl);
  }
};
```

## Notas Importantes

1. **NO crear múltiples archivos de configuración** - Usar solo `env.js`
2. **NO duplicar lógica de detección de ambiente** - Ya está centralizada
3. **Siempre importar desde `../config/env`** - No usar `process.env` directamente
4. **Variables de entorno son opcionales** - La detección automática funciona sin ellas
