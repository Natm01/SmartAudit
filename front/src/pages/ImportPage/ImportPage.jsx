// frontend/src/pages/ImportPage/ImportPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ImportForm from '../../components/ImportForm/ImportForm';
import ImportHistory from '../../components/ImportHistory/ImportHistory';
import StatusModal from '../../components/StatusModal/StatusModal';
import projectService from '../../services/projectService';
import importService from '../../services/importService';

const ImportPage = ({ filteredProjects, loadingProjects, currentUserId }) => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [importHistory, setImportHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [statusModal, setStatusModal] = useState({
    open: false,
    title: '',
    subtitle: '',
    status: 'info',
    executionId: null,
  });

  // Función para limpiar cache de validaciones anteriores
  const cleanupValidationCache = () => {
    try {
      const keys = Object.keys(sessionStorage);
      const validationKeys = keys.filter(key => 
        key.startsWith('validation_') || 
        key.startsWith('fieldmapper_')
      );
      
      validationKeys.forEach(key => {
        sessionStorage.removeItem(key);
      });
      
      console.log('🧹 Cleaned up validation cache:', validationKeys.length, 'items removed');
    } catch (error) {
      console.warn('Could not cleanup validation cache:', error);
    }
  };

  useEffect(() => {
    // Limpiar cache al cargar la página de importación
    cleanupValidationCache();
    loadInitialData();
  }, []);

  // Usar proyectos filtrados recibidos como props
  useEffect(() => {
    if (filteredProjects) {
      setProjects(filteredProjects);
    }
  }, [filteredProjects]);

  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const historyResponse = await importService.getImportHistory();
      if (historyResponse.success) setImportHistory(historyResponse.executions);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Error al cargar la información inicial');
    } finally {
      setLoading(false);
    }
  };

  const showUserChangeNotification = (userName) => {
    const n = document.createElement('div');
    n.className = 'fixed top-4 right-4 bg-purple-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 transform transition-all duration-300';
    n.innerHTML = `
      <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
        </svg>
        <span>Cambiado a ${userName}</span>
      </div>`;
    document.body.appendChild(n);
    setTimeout(() => {
      n.style.transform = 'translateX(100%)';
      setTimeout(() => document.body.contains(n) && document.body.removeChild(n), 300);
    }, 3000);
  };

  const handleUserChange = async (newUser) => {
    try { 
      setUser(newUser); 
      showUserChangeNotification(newUser.name); 
    } catch { 
      setError('Error al cambiar de usuario'); 
    }
  };

  // === Subir y validar (LD + SS si existe) ===
  const handleImportSubmit = async ({ projectId, period, libroDiarioFiles, sumasSaldosFile }) => {
    try {
      setError(null);
      
      // Limpiar cache antes de empezar nueva importación
      cleanupValidationCache();
      
      setStatusModal({
        open: true,
        title: 'Subiendo archivos…',
        subtitle: 'Cargando Libro Diario' + (sumasSaldosFile ? ' y Sumas y Saldos' : ''),
        status: 'loading',
        executionId: null,
      });

      const uploadRes = await importService.uploadLibroDiarioYSumas(
        libroDiarioFiles, sumasSaldosFile, projectId, period
      );
      if (!uploadRes.success) {
        setStatusModal({
          open: true, 
          title: 'Error al subir archivos',
          subtitle: uploadRes.error || 'Revisa los formatos y vuelve a intentar.',
          status: 'error', 
          executionId: null,
        });
        return;
      }

      const executionIdLD = uploadRes.executionId;
      const executionIdSS = uploadRes.executionIdSS || null;

      if (executionIdLD && executionIdSS) {
        try { 
          sessionStorage.setItem(`ss_execution_for_${executionIdLD}`, executionIdSS); 
        } catch {}
      }

      setStatusModal({
        open: true, 
        title: 'Archivo(s) subido(s) correctamente',
        subtitle: 'Iniciando validación de Libro Diario…',
        status: 'info', 
        executionId: executionIdLD,
      });

      const startValLD = await importService.startValidation(executionIdLD);
      if (!startValLD.success) {
        setStatusModal({
          open: true, 
          title: 'Error al iniciar validación de Libro Diario',
          subtitle: startValLD.error || 'Intenta validar desde la página de Validación.',
          status: 'error', 
          executionId: executionIdLD,
        });
        return;
      }

      setStatusModal({
        open: true,
        title: 'Importando archivos...',
        subtitle: 'Libro Diario en proceso de validación. Esto puede tardar unos momentos.',
        status: 'loading',
        executionId: executionIdLD,
      });

      const pollLD = await importService.pollValidationStatus(executionIdLD, {
        intervalMs: 2000,
        timeoutMs: 180000,
        onProgress: (statusData) => {
          if (statusData?.status) {
            setStatusModal(prev => ({
              ...prev,
              subtitle: `Estado: ${statusData.status}. Procesando validación…`,
            }));
          }
        }
      });

      if (pollLD.success && pollLD.finalStatus === 'completed') {
        await loadInitialData();
        setStatusModal({
          open: true,
          title: 'Importación completada',
          subtitle: 'Libro Diario y Sumas y saldos subidos correctamente.',
          status: 'success',
          executionId: executionIdLD
        });
      } else {
        setStatusModal({ 
          open: true, 
          title: 'La validación no se completó', 
          subtitle: pollLD.error || `Estado final: ${pollLD.finalStatus || 'desconocido'}`, 
          status: 'error', 
          executionId: executionIdLD 
        });
      }
    } catch (err) {
      setStatusModal({ 
        open: true, 
        title: 'Error inesperado', 
        subtitle: err?.message || 'Ocurrió un problema al procesar tu solicitud.', 
        status: 'error', 
        executionId: null 
      });
    }
  };

  const handleHistoryItemClick = (execution) => {
    // Limpiar cache antes de navegar a validación existente
    cleanupValidationCache();
    
    if (execution?.executionId) navigate(`/libro-diario/validation/${execution.executionId}`);
  };

  if (loading || loadingProjects) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-purple-600"></div>
            <span className="ml-4 text-lg text-gray-600">Cargando información...</span>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="flex-1 [&_*]:text-xs [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm">
        <div className="space-y-6 max-w-full mx-auto px-6 sm:px-8 lg:px-12 xl:px-16 py-8">
          {/* Breadcrumb */}
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-4">
              <li>
                <div>
                  <a href="/" className="text-gray-400 hover:text-gray-500">
                    <svg className="flex-shrink-0 w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
                    </svg>
                    <span className="sr-only">Inicio</span>
                  </a>
                </div>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="flex-shrink-0 w-4 h-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"></path>
                  </svg>
                  <a href="/libro-diario" className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">Importación Libro Diario</a>
                </div>
              </li>
            </ol>
          </nav>

          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Importación Libro Diario</h1>
            <p className="mt-2 text-sm text-gray-600">Carga y valida tus archivos contables de forma automática</p>
          </div>

          {/* Steps */}
          <div className="p-6">
            <div className="flex items-center justify-center">
              <div className="flex items-center text-purple-600">
                <div className="flex items-center justify-center w-8 h-8 border-2 border-purple-600 rounded-full bg-purple-600 text-white text-sm font-medium">1</div>
                <span className="ml-2 text-sm font-medium">Importación</span>
              </div>
              <div className="flex-1 h-px bg-gray-200 mx-4"></div>
              <div className="flex items-center text-gray-400">
                <div className="flex items-center justify-center w-8 h-8 border-2 border-gray-300 rounded-full text-sm font-medium">2</div>
                <span className="ml-2 text-sm font-medium">Validación</span>
              </div>
              <div className="flex-1 h-px bg-gray-200 mx-4"></div>
              <div className="flex items-center text-gray-400">
                <div className="flex items-center justify-center w-8 h-8 border-2 border-gray-300 rounded-full text-sm font-medium">3</div>
                <span className="ml-2 text-sm font-medium">Resultados</span>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
              <span className="block sm:inline">{error}</span>
            </div>
          )}

          {/* Contenido */}
          <div className="space-y-6">
            <ImportForm
              key={currentUserId}
              projects={projects}
              loading={false}
              onSubmit={handleImportSubmit}
            />
            <ImportHistory 
              executions={importHistory} 
              onItemClick={handleHistoryItemClick} 
              loading={false} 
            />
          </div>
        </div>
      </main>

      <StatusModal
        isOpen={statusModal.open}
        title={statusModal.title}
        subtitle={statusModal.subtitle}
        status={statusModal.status}
        onClose={() => {
          if (statusModal.status === 'success' && statusModal.executionId) {
            const id = statusModal.executionId;
            setStatusModal(s => ({ ...s, open: false }));
            navigate(`/libro-diario/validation/${id}`);
          } else {
            setStatusModal(s => ({ ...s, open: false }));
          }
        }}
        actions={(statusModal.status === 'success' && statusModal.executionId) ? (
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setStatusModal(s => ({ ...s, open: false }))} 
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-300 bg-white hover:bg-gray-50"
            >
              Seguir aquí
            </button>
            <button 
              onClick={() => { 
                const id = statusModal.executionId; 
                setStatusModal(s => ({ ...s, open: false })); 
                navigate(`/libro-diario/validation/${id}`); 
              }} 
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-600 text-white hover:bg-purple-700"
            >
              Ir a Validación
            </button>
          </div>
        ) : null}
      />
    </div>
  );
};

export default ImportPage;