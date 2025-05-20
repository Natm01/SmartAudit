// frontend/src/components/Header.jsx
import React from 'react';
import { User } from 'lucide-react';
import logoPositivo from '../assets/images/logo-positivo.png';

const Header = () => {
  return (
    <header className="bg-white shadow-sm p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center gap-3">
          {/* Use h-8 or h-9 to match the height of the SmartAudit text */}
          <img src={logoPositivo} alt="Grant Thornton Logo" className="h-16" />
          <h1 className="text-xl font-bold text-gray-800">SmartAudit</h1>
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