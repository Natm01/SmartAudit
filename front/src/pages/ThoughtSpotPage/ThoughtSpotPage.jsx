import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LiveboardEmbed } from '@thoughtspot/visual-embed-sdk/react';
import { init, AuthType, prefetch } from '@thoughtspot/visual-embed-sdk';
import config from '../../config/env';

const ThoughtSpotPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [thoughtSpotInitialized, setThoughtSpotInitialized] = useState(false);

  useEffect(() => {
    initializeThoughtSpot();
    loadInitialData();
  }, []);

  const initializeThoughtSpot = async () => {
    try {
      await init({
        thoughtSpotHost: config.thoughtSpotHost,
        authType: AuthType.None,
        
        // MEJORA 1: Solución para cookies de terceros en Chrome/Edge
        enablePartitionedCookies: true,
        
        corsEnabled: true,
        developmentMode: true,
        preRenderId: 'f1f1312f-af0d-40d2-b94f-85f75f154bb4',
        suppressNoCookieAccessAlert: true,
        suppressErrorAlerts: true,
        detectCookieAccessError: false,
        callPrefetch: true,
        customizations: {
          style: {
            customCSS: {
              variables: {
                '--ts-var-root-background': '#ffffff',
                '--ts-var-root-color': '#000000',
              }
            }
          }
        }
      });
      
      try {
        await prefetch({
          liveboardId: 'f1f1312f-af0d-40d2-b94f-85f75f154bb4'
        });
      } catch (prefetchError) {
        console.warn('Prefetch warning:', prefetchError);
      }
      
      setThoughtSpotInitialized(true);
    } catch (error) {
      console.error('Error initializing ThoughtSpot:', error);
      setError('Error al inicializar ThoughtSpot. Verifica la configuración.');
    }
  };

  const loadInitialData = async () => {
    try {
      setLoading(true);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Error al cargar la información inicial');
    } finally {
      setLoading(false);
    }
  };


  if (loading || !thoughtSpotInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-purple-600 mb-4"></div>
            <p className="text-gray-600">
              {!thoughtSpotInitialized ? 'Inicializando ThoughtSpot...' : 'Cargando dashboard...'}
            </p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-xl shadow-sm p-8 text-center border border-red-100">
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error de acceso</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-y-2">
              <button 
                onClick={() => window.location.reload()} 
                className="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                Reintentar
              </button>
              <button 
                onClick={() => navigate('/')} 
                className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
              >
                Volver al inicio
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      
      
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Breadcrumb */}
        <div className="w-full px-4 sm:px-6 lg:px-8 py-4 flex-shrink-0">
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="inline-flex items-center space-x-1 md:space-x-3">
              <li className="inline-flex items-center">
                <button
                  onClick={() => navigate('/')}
                  className="inline-flex items-center text-sm font-medium text-gray-700 hover:text-purple-600 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
                  </svg>
                  Inicio
                </button>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"></path>
                  </svg>
                  <span className="ml-1 text-sm font-medium text-gray-500 md:ml-2">ThoughtSpot</span>
                </div>
              </li>
            </ol>
          </nav>
        </div>

        <div className="w-full px-4 sm:px-6 lg:px-8 mb-4 flex-shrink-0">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m0 0h2M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 8h1m-1-4h1m4 4h1m-1-4h1" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-gray-900">
                    Proyecto: OPERADOR INTEGRAL DE VEHICULOS, S.L.U
                  </h2>
                  <p className="text-xs text-gray-600">
                    Dashboard de análisis y visualización de datos 
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 px-4 sm:px-6 lg:px-8 pb-4 min-h-0">
          <div className="w-full h-full bg-white rounded-xl shadow-sm border border-gray-200">
            <LiveboardEmbed
              liveboardId="f1f1312f-af0d-40d2-b94f-85f75f154bb4"
              frameParams={{
                height: '100vh',
                width: '100%'
              }}
              className="w-full h-full"
              style={{
                width: '100%',
                height: '100%',
                minHeight: '600px'
              }}
              preRenderId="f1f1312f-af0d-40d2-b94f-85f75f154bb4"
              disableSDKTracking={true}
              hideLiveboardHeader={true}
              hideTabPanel={true}
              hideActions={[
                'save', 'saveAsView', 'makeACopy', 'edit', 'present', 
                'schedule', 'share', 'download', 'export', 'subscribe'
              ]}
              hiddenActions={[
                'contextMenu', 'explore', 'exploreChart', 
                'drill', 'drillDown', 'drillUp'
              ]}
              runtimeFilterOptions={{
                enableRuntimeFilters: false
              }}
              enableSearchAssist={false}
              hideDataSources={true}
              hideObjects={true}
              onLoad={() => console.log('Liveboard cargado')}
              onError={(error) => console.error('Error en Liveboard:', error)}
              onLiveboardRendered={() => console.log('Liveboard renderizado')}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default ThoughtSpotPage;