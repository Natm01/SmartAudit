// frontend/src/App.jsx
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header/Header';
import HomePage from './pages/HomePage/HomePage';
import ImportPage from './pages/ImportPage/ImportPage';
import ValidationPage from './pages/ValidationPage/ValidationPage';
import ResultsPage from './pages/ResultsPage/ResultsPage';
import ThoughtSpotPage from './pages/ThoughtSpotPage/ThoughtSpotPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { MsalProvider } from '@azure/msal-react';
import { PublicClientApplication } from '@azure/msal-browser';
import projectService from './services/projectService';

function ProtectedRoute({children}) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div>Cargando...</div>;
  if (!isAuthenticated) return <div>Redirigiendo a Microsoft...</div>; // MSAL redirigirá automáticamente

  return children;
}

function AppContent() {
  const { userContext } = useAuth();
  const [allProjects, setAllProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Cargar proyectos SOLO cuando tengamos el usuario
  useEffect(() => {
    const fetchProjects = async () => {
      if (!userContext) return; // Espera al usuario
      try {
        const response = await projectService.getAllProjects();
        setAllProjects(response.projects || response || []);
      } catch (error) {
        console.error('Error cargando proyectos:', error);
        setAllProjects([]);
      } finally {
        setLoadingProjects(false);
      }
    };

    fetchProjects();
  }, [userContext]); // se ejecuta cuando userContext cambia

  // Filtrar proyectos por usuario
  const filteredProjects = React.useMemo(() => {
    if (!userContext || !userContext.id) return [];

    // Normalizamos para evitar problemas de espacios o mayúsculas/minúsculas
    const userId = userContext.id.trim().toLowerCase();

    return allProjects.filter(
      (project) => project.idUser?.trim().toLowerCase() === userId
    );
  }, [allProjects, userContext]);

  console.log('Usuario actual:', userContext?.id);
  console.log('Total proyectos:', allProjects.length);
  console.log('Proyectos filtrados:', filteredProjects.length);

  return (
    <Router>
      <Header user={userContext} />
      <Routes>
        {/* Página principal */}
        <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />

        {/* Rutas del módulo de Importación de Libro Diario */}
        <Route
          path="/libro-diario"
          element={
            <ProtectedRoute>
              <ImportPage
                filteredProjects={filteredProjects}
                loadingProjects={loadingProjects}
                currentUserId={userContext?.id}
              />
            </ProtectedRoute>
          }
        />

        <Route path="/libro-diario/validation/:executionId" element={<ProtectedRoute><ValidationPage /></ProtectedRoute>} />
        <Route path="/libro-diario/results/:executionId" element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />

        {/* Ruta para ThoughtSpot */}
        <Route path="/thoughtspot" element={<ProtectedRoute><ThoughtSpotPage /></ProtectedRoute>} />

        {/* Redirección para rutas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;