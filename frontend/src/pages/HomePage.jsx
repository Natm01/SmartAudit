// frontend/src/pages/HomePage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, BarChart2, Users, CheckCircle, ArrowRight } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  const handleNavigation = (screen) => {
    navigate(screen);
  };

  const applications = [
    {
      id: 'importacion',
      title: 'Importación Libro Diario',
      description: 'Cargar y validar archivos contables de forma automática',
      icon: <FileText size={28} className="text-white" />,
      color: 'from-purple-600 to-purple-800',
      accentColor: 'bg-purple-100',
      textColor: 'text-purple-700'
    },
    {
      id: 'analisis-jet',
      title: 'Análisis JET',
      description: 'Ejecutar filtros avanzados sobre el libro diario',
      icon: <BarChart2 size={28} className="text-white" />,
      color: 'from-purple-700 to-purple-900',
      accentColor: 'bg-purple-50',
      textColor: 'text-purple-800'
    },
    {
      id: 'analisis-riesgos',
      title: 'Análisis de Riesgos',
      description: 'Evaluación y detección de riesgos contables',
      icon: <Users size={28} className="text-white" />,
      color: 'from-purple-600 to-purple-800',
      accentColor: 'bg-purple-100',
      textColor: 'text-purple-700'
    },
    {
      id: 'analisis-obsolescencia',
      title: 'Análisis de Obsolescencia',
      description: 'Identificación de inventario obsoleto y patrones',
      icon: <CheckCircle size={28} className="text-white" />,
      color: 'from-purple-700 to-purple-900',
      accentColor: 'bg-purple-50',
      textColor: 'text-purple-800'
    }
  ];

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Aplicaciones</h1>
      </div>
      
      <div className="grid md:grid-cols-4 gap-4">
        {applications.map((app) => (
          <div
            key={app.id}
            className="group relative bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer overflow-hidden border border-gray-100"
            onClick={() => handleNavigation(app.id)}
          >
            {/* Gradient Background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${app.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
            
            {/* Content */}
            <div className="relative p-4">
              {/* Icon with gradient background */}
              <div className={`bg-gradient-to-br ${app.color} rounded-2xl w-14 h-14 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                {app.icon}
              </div>
              
              {/* Title and Description */}
              <h3 className="text-2m font-bold text-gray-800 mb-3 group-hover:text-purple-700 transition-colors duration-300">
                {app.title}
              </h3>
              <p className="text-xs text-gray-600 mb-6 leading-relaxed">
                {app.description}
              </p>
              
              {/* Action Button */}
              <div className="flex items-center justify-between">
                <div className="flex items-center text-purple-700 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-4 group-hover:translate-x-0">
                  <span className="text-sm font-semibold mr-2">Acceder</span>
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform duration-300" />
                </div>
              </div>
            </div>
            
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-24 h-24 opacity-5">
              <div className={`w-full h-full bg-gradient-to-br ${app.color} rounded-full transform translate-x-8 -translate-y-8`}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HomePage;