// frontend/src/components/DatabaseTestButton/DatabaseTestButton.jsx
import React, { useState } from 'react';
import databaseService from '../../services/databaseService';

const DatabaseTestButton = () => {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const handleTestConnection = async () => {
    setTesting(true);
    setShowResult(false);

    try {
      const response = await databaseService.testConnection();
      setResult(response);
      setShowResult(true);
    } catch (error) {
      setResult({
        success: false,
        error: 'Error inesperado al probar la conexión'
      });
      setShowResult(true);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="inline-block">
      <button
        onClick={handleTestConnection}
        disabled={testing}
        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 flex items-center gap-2"
      >
        {testing ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            <span>Probando conexión...</span>
          </>
        ) : (
          <>
            <span>🔌</span>
            <span>Probar Conexión BD</span>
          </>
        )}
      </button>

      {showResult && result && (
        <div className={`mt-4 p-4 rounded-lg border ${
          result.success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">
              {result.success ? '✅' : '❌'}
            </span>
            <div className="flex-1">
              <h4 className={`font-semibold mb-2 ${
                result.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {result.success ? 'Conexión exitosa' : 'Error de conexión'}
              </h4>

              {result.success && result.data && (
                <div className="space-y-1 text-sm text-gray-700">
                  <p><strong>Estado:</strong> {result.data.status}</p>
                  <p><strong>Servidor:</strong> {result.data.server}</p>
                  <p><strong>Base de datos:</strong> {result.data.database}</p>
                  <details className="mt-2">
                    <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                      Ver versión SQL
                    </summary>
                    <p className="mt-2 text-xs text-gray-600 font-mono bg-white p-2 rounded border border-gray-200 overflow-auto">
                      {result.data.sql_version}
                    </p>
                  </details>
                </div>
              )}

              {!result.success && (
                <div className="text-sm text-red-700 space-y-2">
                  <p className="font-semibold">
                    {typeof result.error === 'string'
                      ? result.error
                      : result.error?.error_message || 'Error desconocido'}
                  </p>

                  {typeof result.error === 'object' && result.error?.diagnostics && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-red-600 hover:text-red-800 font-semibold">
                        Ver información de diagnóstico
                      </summary>
                      <div className="mt-3 text-xs bg-gray-50 p-3 rounded border border-gray-200 space-y-2">
                        <div>
                          <strong>Ambiente:</strong> {result.error.diagnostics.environment}
                        </div>
                        <div>
                          <strong>Tipo de autenticación:</strong> {result.error.diagnostics.auth_type}
                        </div>
                        <div>
                          <strong>Servidor:</strong> {result.error.diagnostics.server}
                        </div>
                        <div>
                          <strong>Base de datos:</strong> {result.error.diagnostics.database}
                        </div>
                        <div>
                          <strong>Drivers ODBC disponibles:</strong>
                          <ul className="list-disc list-inside ml-2">
                            {result.error.diagnostics.odbc_drivers?.map((driver, idx) => (
                              <li key={idx}>{driver}</li>
                            ))}
                          </ul>
                        </div>
                        <details className="mt-2">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                            Variables de entorno
                          </summary>
                          <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto">
                            {JSON.stringify(result.error.diagnostics.env_vars, null, 2)}
                          </pre>
                        </details>
                        {result.error.traceback && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                              Stack trace completo
                            </summary>
                            <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-48 font-mono">
                              {result.error.traceback}
                            </pre>
                          </details>
                        )}
                      </div>
                    </details>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseTestButton;
