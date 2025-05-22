// frontend/src/components/Header.jsx
import React from 'react';
import { User } from 'lucide-react';
import logoPositivo from '../assets/images/logo-positivo.png';

const Header = () => {
  return (
    <header className="bg-white shadow-sm py-0 px-12 pl-0 mb-3">
      <div className="container mx-auto flex justify-between items-center max-w-screen-xl">
        <div className="flex items-center space-x-10">
          <img 
            src={logoPositivo} 
            alt="Grant Thornton Logo" 
            className="h-20 w-auto " 
          />
          <h1 className="text-2xl font-bold text-gray-800 "> SmartAudit</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <User className="text-purple-800" size={16} />
          <span>Carlos Rodríguez</span>
        </div>
      </div>
    </header>
  );
};

export default Header;