// frontend/src/components/importacion/StepIndicator.jsx
import React from 'react';


const StepIndicator = ({ currentStep, handleStepChange }) => {
  return (
    <div className="relative mb-8">
      <div className="flex justify-between items-center">
        <div 
          className={`flex flex-col items-center cursor-pointer ${currentStep >= 1 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(1)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 1 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            1
          </div>
          <span className="text-sm mt-1">Importación</span>
        </div>
        
        <div 
          className={`flex flex-col items-center cursor-pointer ${currentStep >= 2 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(2)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 2 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            2
          </div>
          <span className="text-sm mt-1">Validación</span>
        </div>
        
        <div 
          className={`flex flex-col items-center cursor-pointer ${currentStep >= 3 ? 'text-purple-700' : 'text-gray-400'}`}
          onClick={() => handleStepChange(3)}
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${currentStep >= 3 ? 'bg-purple-700' : 'bg-gray-300'}`}>
            3
          </div>
          <span className="text-sm mt-1">Resultado</span>
        </div>
      </div>
      
      {/* Progress bar - positioned to precisely match the reference design */}
      <div className="absolute top-4 h-1 left-0 right-0 -z-10">
        {/* Background bar */}
        <div className="absolute top-0 left-14 right-14 h-0.5 bg-gray-200"></div>
        {/* Purple progress overlay */}
        <div 
          className="absolute top-0 left-14 h-0.5 bg-purple-700 transition-all duration-300" 
          style={{ 
            width: currentStep === 1 ? '0%' : 
                   currentStep === 2 ? '50%' : '100%'
          }}
        ></div>
      </div>
    </div>
  );
};

export default StepIndicator;