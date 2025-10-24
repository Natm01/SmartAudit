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
                <p className="text-sm text-red-700">
                  {result.error || 'Error desconocido'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseTestButton;
