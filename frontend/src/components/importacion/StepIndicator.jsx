// frontend/src/components/importacion/StepIndicator.jsx
import React from 'react';

const StepIndicator = ({ activeStep, handleStepChange }) => {
  return (
    <div className="relative">
      <div className="flex justify-between items-center mb-2">
        <div 
          className={`flex flex-col items-center cursor-pointer ${activeStep >= 1 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(1)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${activeStep >= 1 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            1
          </div>
          <span className="text-sm mt-1">Importación</span>
        </div>
        
        <div 
          className={`flex flex-col items-center cursor-pointer ${activeStep >= 2 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(2)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${activeStep >= 2 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            2
          </div>
          <span className="text-sm mt-1">Validación</span>
        </div>
        
        <div 
          className={`flex flex-col items-center cursor-pointer ${activeStep >= 3 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(3)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${activeStep >= 3 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            3
          </div>
          <span className="text-sm mt-1">Resultado</span>
        </div>
      </div>
      
      <div className="absolute top-4 left-0 right-0 h-2 bg-gray-200 -z-10 rounded-full">
        <div 
          className="h-2 bg-purple-700 transition-all duration-300 rounded-full" 
          style={{ width: `${(activeStep - 1) * 50}%` }}
        ></div>
      </div>
    </div>
  );
};

export default StepIndicator;