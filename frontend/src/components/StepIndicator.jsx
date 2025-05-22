// frontend/src/components/StepIndicator.jsx
import React from 'react';

const StepIndicator = ({ currentStep, handleStepChange, canNavigateToStep }) => {
  
  // Función para determinar si se puede navegar a un paso específico
  const canNavigateTo = (step) => {
    // Si se proporciona una función personalizada, usarla
    if (canNavigateToStep) {
      return canNavigateToStep(step);
    }
    
    // Lógica por defecto: solo se puede navegar hacia atrás o al paso actual
    return step <= currentStep;
  };

  const handleStepClick = (step) => {
    if (canNavigateTo(step) && step !== currentStep) {
      handleStepChange(step);
    }
  };

  return (
    <div className="flex justify-center mt-0">
      <div className="inline-flex items-center max-w-md">
        {/* Step 1 */}
        <div 
          className={`flex flex-col items-center transition-all duration-200 ${
            canNavigateTo(1) && currentStep !== 1 
              ? 'cursor-pointer hover:scale-105' 
              : currentStep === 1 
                ? 'cursor-default' 
                : 'cursor-not-allowed opacity-60'
          } ${currentStep >= 1 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepClick(1)}
          title={canNavigateTo(1) ? 'Ir a Importación' : 'No disponible'}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold transition-all duration-200 ${
            currentStep >= 1 ? 'bg-purple-700' : 'bg-gray-300'
          } ${canNavigateTo(1) && currentStep !== 1 ? 'hover:bg-purple-800' : ''}`}>
            1
          </div>
          <span className="text-xs mt-1">Importación</span>
        </div>
        
        {/* Connection line 1-2 */}
        <div className="w-40 mx-1 h-1 relative rounded-full">
          <div className="absolute inset-0 bg-gray-200 rounded-full"></div>
          <div 
            className="absolute inset-0 bg-purple-700 transition-all duration-300 rounded-full"
            style={{ width: currentStep >= 2 ? '100%' : '0%' }}
          ></div>
        </div>
        
        {/* Step 2 */}
        <div 
          className={`flex flex-col items-center transition-all duration-200 ${
            canNavigateTo(2) && currentStep !== 2 
              ? 'cursor-pointer hover:scale-105' 
              : currentStep === 2 
                ? 'cursor-default' 
                : 'cursor-not-allowed opacity-60'
          } ${currentStep >= 2 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepClick(2)}
          title={canNavigateTo(2) ? 'Ir a Validación' : 'Complete el paso anterior'}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold transition-all duration-200 ${
            currentStep >= 2 ? 'bg-purple-700' : 'bg-gray-300'
          } ${canNavigateTo(2) && currentStep !== 2 ? 'hover:bg-purple-800' : ''}`}>
            2
          </div>
          <span className="text-xs mt-1">Validación</span>
        </div>
        
        {/* Connection line 2-3 */}
        <div className="w-40 mx-1 h-1 relative rounded-full">
          <div className="absolute inset-0 bg-gray-200 rounded-full"></div>
          <div 
            className="absolute inset-0 bg-purple-700 transition-all duration-300 rounded-full"
            style={{ width: currentStep >= 3 ? '100%' : '0%' }}
          ></div>
        </div>
        
        {/* Step 3 */}
        <div 
          className={`flex flex-col items-center transition-all duration-200 ${
            canNavigateTo(3) && currentStep !== 3 
              ? 'cursor-pointer hover:scale-105' 
              : currentStep === 3 
                ? 'cursor-default' 
                : 'cursor-not-allowed opacity-60'
          } ${currentStep >= 3 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepClick(3)}
          title={canNavigateTo(3) ? 'Ir a Resultado' : 'Complete los pasos anteriores'}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold transition-all duration-200 ${
            currentStep >= 3 ? 'bg-purple-700' : 'bg-gray-300'
          } ${canNavigateTo(3) && currentStep !== 3 ? 'hover:bg-purple-800' : ''}`}>
            3
          </div>
          <span className="text-xs mt-1">Resultado</span>
        </div>
      </div>
    </div>
  );
};

export default StepIndicator;