//propuesta LoginPage en desuso

// frontend/src/pages/HomePage/LoginPage.jsx - Login con entraid
import React from "react";
import { useAuth } from "../../context/AuthContext";

const LoginPage = () => {
    const { login } = useAuth();
    
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="bg-white shadow-md rounded-lg p-8 text-center border border-gray-200">
                <div className ="flex items-center justify-center mb-4">
                    <img src="/logo.png" alt="Logo" className="h-16 w-16"/>
                    <div className="hidden sm:block">
                    <h1 className="text-xl font-bold text-gradient">SmartAudit</h1>
                    </div>
                    <h2 className="text-xl font-semibold mb-2">Bienvenido</h2>
                    <button
                        onClick={() => login()}
                        className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition"
                    >
                    Iniciar sesión
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;