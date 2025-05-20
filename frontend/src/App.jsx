// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ImportacionPage from './pages/ImportacionPage';
import AnalisisObsolescenciaPage from './pages/AnalisisObsolescenciaPage';

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Header />
        <main className="flex-grow container mx-auto p-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/importacion/*" element={<ImportacionPage />} />
            <Route path="/analisis-jet" element={<div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">Módulo de Análisis JET en desarrollo</div>} />
            <Route path="/analisis-riesgos" element={<div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">Módulo de Análisis de Riesgos en desarrollo</div>} />
            <Route path="/analisis-obsolescencia" element={<AnalisisObsolescenciaPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;