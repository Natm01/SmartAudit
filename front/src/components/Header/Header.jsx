// frontend/src/components/Header/Header.jsx
import React, { useState } from 'react';
import logo from '../../assets/images/logo-positivo.png';
import { useAuth } from '../../context/AuthContext';

const Header = () => {
  const { userContext, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Función para generar iniciales del usuario
  const getUserInitials = (userName) => {
    if (!userName || typeof userName !== 'string') {
      return '??';
    }
    
    try {
      return userName
        .split(' ')
        .map(n => n && n.length > 0 ? n[0].toUpperCase() : '')
        .filter(initial => initial !== '')
        .join('')
        .substring(0, 2);
    } catch (error) {
      console.error('Error generating initials for:', userName, error);
      return '??';
    }
  };

  // Función para obtener el nombre desde el email
  const getNameFromEmail = (email) => {
    if (!email) return 'Usuario';
    
    // Extraer la parte antes del @
    const namePart = email.split('@')[0];
    
    // Reemplazar puntos por espacios y capitalizar
    const name = namePart
      .split('.')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
    
    return name;
  };

  // Función auxiliar para obtener nombre seguro
  const getSafeName = (name) => {
    if (!name || typeof name !== 'string') {
      return 'Usuario Desconocido';
    }
    return name.trim() || 'Usuario Desconocido';
  };

  // Usuario autenticado desde Azure AD
  const displayUser = userContext && !userContext.error
    ? {
        name: getNameFromEmail(userContext.email),
        email: userContext.email,
        roleName: userContext.isAdmin ? 'Administrador' : 'Colaborador',
        environment: userContext.environment,
        userType: userContext.userType
      }
    : null;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-10">
        <div className="flex justify-between items-center h-16">
          {/* Logo y título */}
          <div className="flex items-center space-x-4">
            <img src={logo} alt="SmartAudit" className="h-16 w-auto" />
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-gradient">SmartAudit</h1>
            </div>
          </div>

          {/* Usuario actual y selector */}
          <div className="flex items-center space-x-4">
            {/* Información del usuario actual */}
            {displayUser && (
              <div className="hidden sm:flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {getSafeName(displayUser.name)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {displayUser.email || displayUser.roleName || 'Rol no especificado'}
                  </p>
                </div>
              </div>
            )}

            {/* Menú de usuario */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                  {getUserInitials(displayUser?.name)}
                </div>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown del menú de usuario */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  {/* Información del usuario autenticado */}
                  {userContext && !userContext.error && (
                    <div className="p-4 bg-purple-50">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                          {getUserInitials(getNameFromEmail(userContext.email))}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {getNameFromEmail(userContext.email)}
                          </p>
                          <p className="text-xs text-gray-600">{userContext.email}</p>
                          <p className="text-xs text-purple-600 mt-1">
                            {userContext.userType} • {userContext.environment}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Botón de cerrar sesión */}
                  <div className="p-3 border-t border-gray-200">
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        logout();
                      }}
                      className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center justify-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      <span>Cerrar sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;