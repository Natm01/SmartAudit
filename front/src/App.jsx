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
import userService from './services/userService';
import projectService from './services/projectService';

function ProtectedRoute({children}) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div>Cargando...</div>;
  if (!isAuthenticated) return <div>Redirigiendo a Microsoft...</div>; // MSAL redirigirá automáticamente

  return children;
}

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [allProjects, setAllProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Cargar usuario actual
  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const response = await userService.getCurrentUser();
        if (response.success && response.user) {
          setCurrentUser(response.user);
          console.log('Usuario actual:', response.user);
        }
      } catch (error) {
        console.error('Error cargando usuario actual:', error);
      }
    };

    loadCurrentUser();
  }, []);

  // Cargar proyectos SOLO cuando tengamos el usuario
  useEffect(() => {
    const fetchProjects = async () => {
      if (!currentUser) return; // 👈 Espera al usuario
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
  }, [currentUser]); // se ejecuta cuando currentUser cambia

  // Filtrar proyectos por usuario
  const filteredProjects = React.useMemo(() => {
    if (!currentUser || !currentUser.id) return [];

    // Normalizamos para evitar problemas de espacios o mayúsculas/minúsculas
    const userId = currentUser.id.trim().toLowerCase();

    return allProjects.filter(
      (project) => project.idUser?.trim().toLowerCase() === userId
    );
  }, [allProjects, currentUser]);

  console.log('Usuario actual:', currentUser?.id);
  console.log('Total proyectos:', allProjects.length);
  console.log('Proyectos filtrados:', filteredProjects.length);

  return (
    <AuthProvider>
      <Router>
        <Header user={currentUser} onUserChange={setCurrentUser} />
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
                  currentUserId={currentUser?.id}
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
    </AuthProvider>
  );
}

export default App;