// frontend/src/App.jsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ImportacionPage from './pages/ImportacionPage';
import AnalisisObsolescenciaPage from './pages/AnalisisObsolescenciaPage';

function App() {
  // Efecto para ajustar el escalado basado en el ancho de la ventana
  useEffect(() => {
    function handleResize() {
      // Este efecto solo se ejecuta en el cliente, no durante SSR
      if (typeof window !== 'undefined') {
        const mainContent = document.querySelector('.app-content');
        if (!mainContent) return;
        
        // Lógica para mantener la escala cuando cambia el tamaño de la ventana
        // ya está manejada en CSS con media queries
      }
    }

    window.addEventListener('resize', handleResize);
    handleResize(); // Ejecutar al montar el componente
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Header />
        <main className="flex-grow app-content">
          <div className="container mx-auto px-2 py-4 max-w-screen-2xl">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/importacion/*" element={<ImportacionPage />} />
              <Route path="/analisis-jet" element={<div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">Módulo de Análisis JET en desarrollo</div>} />
              <Route path="/analisis-riesgos" element={<div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">Módulo de Análisis de Riesgos en desarrollo</div>} />
              {/* Agrupar todas las rutas relacionadas con análisis de obsolescencia */}
              <Route path="/analisis-obsolescencia" element={<AnalisisObsolescenciaPage />} />
              <Route path="/analisis-obsolescencia/step1" element={<AnalisisObsolescenciaPage />} />
              <Route path="/analisis-obsolescencia/step2" element={<AnalisisObsolescenciaPage />} />
              <Route path="/analisis-obsolescencia/step3" element={<AnalisisObsolescenciaPage />} />
            </Routes>
          </div>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;