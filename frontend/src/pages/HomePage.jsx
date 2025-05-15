// frontend/src/pages/HomePage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  const navigate = useNavigate();

  const handleNavigation = (screen) => {
    navigate(screen);
  };

  const applications = [
    {
      id: 'importacion',
      title: 'Importación Libro Diario',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-700">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      )
    },
    {
      id: 'analisis-jet',
      title: 'Análisis JET',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-700">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
      )
    },
    {
      id: 'analisis-riesgos',
      title: 'Análisis de riesgos',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-700">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      )
    },
    {
      id: 'analisis-obsolescencia',
      title: 'Análisis de obsolescencia',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-700">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
      )
    }
  ];

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-8">Aplicaciones</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {applications.map((app) => (
          <div
            key={app.id}
            className="bg-white rounded-lg shadow-sm p-4 cursor-pointer hover:shadow transition-shadow"
            onClick={() => handleNavigation(app.id)}
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                {app.icon}
              </div>
              <h3 className="font-medium text-gray-800 text-sm">{app.title}</h3>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HomePage;