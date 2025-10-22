import React, { createContext, useContext, useState, useEffect } from 'react';
import { useMsal } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import config from '../config/env';

// Crear contexto
const AuthContext = createContext();

// Hook personalizado para usar el contexto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Provider que envuelve toda la aplicación
export const AuthProvider = ({ children }) => {
  const { instance, accounts } = useMsal();
  const [userContext, setUserContext] = useState(null);
  const [loading, setLoading] = useState(true);

  // Efecto que escucha cambios en las cuentas
    useEffect(() => {
    const initAuth = async () => {
        try {
            await instance.initialize(); // Espera a que MSAL esté listo
            
            // Procesa la respuesta del redirect (si existe)
            await instance.handleRedirectPromise();

            const currentAccounts = instance.getAllAccounts();

            if (currentAccounts.length === 0) {
                await instance.loginRedirect({
                ...loginRequest,
                prompt: 'select_account'
                });
            } else {
                checkAuth(currentAccounts);
            }
        } catch (error) {
            console.error('Error inicializando MSAL:', error);
        }
    };
    initAuth();
    }, [instance]);


  // Función principal de verificación de autenticación
  const checkAuth = async (accounts) => {
    try {
      const account = accounts[0];
      
      // Obtener token silenciosamente
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account
      });

      // Extraer y procesar roles
      const roles = response.idTokenClaims?.roles || [];
      const userRole = roles.find(role => role.startsWith('smart-audit.'));
      
      if (userRole) {
        // Primero parseamos los roles base
        const parsed = parseUserRole(userRole, account.username);

        // Luego pedimos los datos enriquecidos del usuario desde el backend
        const idToken = response.idToken;

        try {
          console.log('🔄 Solicitando datos del usuario desde:', `${config.portalApiUrl}/api/v1/users/me`);

          const apiResponse = await fetch(`${config.portalApiUrl}/api/v1/users/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${idToken}`,
              'Content-Type': 'application/json',
            },
          });

          console.log('📡 Respuesta del backend:', {
            status: apiResponse.status,
            statusText: apiResponse.statusText,
            ok: apiResponse.ok,
          });

          if (apiResponse.ok) {
            const data = await apiResponse.json();
            console.log('✅ Datos recibidos del backend:', data);

            // Asegurar que siempre tengamos el campo id
            const mergedData = {
              ...parsed,
              ...data,
            };

            // Si el backend no retorna id, usar el que extrajimos del email
            if (!mergedData.id && parsed.id) {
              mergedData.id = parsed.id;
            }

            console.log('✅ Contexto de usuario final:', mergedData);
            setUserContext(mergedData);
          } else {
            const errorText = await apiResponse.text();
            console.error('❌ Error en la respuesta del backend:', {
              status: apiResponse.status,
              statusText: apiResponse.statusText,
              body: errorText,
            });
            console.log('⚠️ Usando datos parseados del token como fallback');
            setUserContext(parsed);
          }
        } catch (error) {
          console.error('❌ Error obteniendo user-context:', error);
          console.log('⚠️ Usando datos parseados del token como fallback');
          setUserContext(parsed);
        }
      } else {
        setUserContext({ error: 'No tienes acceso asignado' });
      }
    } catch (error) {
      console.error('Auth error:', error);
      setUserContext({ error: 'Error de autenticación' });
    } finally {
        setLoading(false);
    }
  };

  // Parsear roles personalizados
  const parseUserRole = (roleValue, email) => {
    const parts = roleValue.split('.');
    // Extraer el id del email (parte antes del @)
    const id = email ? email.split('@')[0] : null;

    if (parts.length >= 5) {
      const [prefix, environment, type, tenantSlug, workspaceSlug] = parts;
      return {
        id,
        email,
        environment,
        userType: type,
        tenantSlug,
        workspaceSlug,
        rawRole: roleValue,
        isAdmin: type === 'admin'
      };
    }
    return {
      id,
      email, 
      error: 'Formato de role inválido', 
      rawRole: roleValue 
    };
  };

  // Funciones de login y logout
  const login = async () => {
    await instance.loginRedirect({
        ...loginRequest,
        prompt: 'select_account'
    });
  };

  const logout = () => {
    instance.logoutRedirect();
  };

  // Valores del contexto
  const contextValue = {
    userContext,
    loading,
    login,
    logout,
    isAuthenticated: !!userContext && !userContext.error,
    isAdmin: userContext?.isAdmin || false
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};