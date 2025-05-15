// frontend/src/components/Footer.jsx
import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 p-4 mt-auto">
      <div className="container mx-auto text-center text-sm text-gray-600">
        © {new Date().getFullYear()} Grant Thornton • Todos los derechos reservados
      </div>
    </footer>
  );
};

export default Footer;