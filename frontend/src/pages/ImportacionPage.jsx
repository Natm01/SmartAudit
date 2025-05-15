// frontend/src/pages/ImportacionPage.jsx
import React, { useState } from 'react';
import { useNavigate, Routes, Route } from 'react-router-dom';
import ImportacionStep1 from '../components/importacion/ImportacionStep1';
import ImportacionStep2 from '../components/importacion/ImportacionStep2';
import ImportacionStep3 from '../components/importacion/ImportacionStep3';
import StepIndicator from '../components/importacion/StepIndicator';

const ImportacionPage = () => {
  const [activeStep, setActiveStep] = useState(1);
  const [formData, setFormData] = useState({
    project: '',
    year: '',
    startDate: '',
    endDate: '',
    libroFiles: [],
    sumasFiles: []
  });
  const [validationData, setValidationData] = useState(null);
  const [processData, setProcessData] = useState(null);
  const [tempDir, setTempDir] = useState('');
  const [validationId, setValidationId] = useState('');
  
  const navigate = useNavigate();

  const handleNavigation = (screen) => {
    navigate(`/${screen}`);
  };

  const handleStepChange = (step) => {
    if (step >= 1 && step <= 3) {
      setActiveStep(step);
      navigate(step === 1 ? '' : `/importacion/step${step}`);
    }
  };

  const handleFormChange = (newData) => {
    setFormData({ ...formData, ...newData });
  };

  const handleUploadSuccess = (response) => {
    setTempDir(response.temp_dir);
    handleStepChange(2);
  };

  const handleValidationComplete = (validationResult) => {
    setValidationData(validationResult);
    setValidationId(validationResult.validation_id);
  };

  const handleProcessComplete = (processResult) => {
    setProcessData(processResult);
    handleStepChange(3);
  };

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-semibold text-gray-800">Importación Libro Diario</h2>
          <button
            onClick={() => handleNavigation('')}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Volver al inicio
          </button>
        </div>
        
        <StepIndicator activeStep={activeStep} handleStepChange={handleStepChange} />
      </div>
      
      <Routes>
        <Route
          path="/"
          element={
            <ImportacionStep1
              formData={formData}
              onFormChange={handleFormChange}
              onUploadSuccess={handleUploadSuccess}
              onNext={() => handleStepChange(2)}
            />
          }
        />
        <Route
          path="/step2"
          element={
            <ImportacionStep2
              tempDir={tempDir}
              formData={formData}
              validationData={validationData}
              onValidationComplete={handleValidationComplete}
              onNext={() => handleStepChange(3)}
              onPrev={() => handleStepChange(1)}
            />
          }
        />
        <Route
          path="/step3"
          element={
            <ImportacionStep3
              tempDir={tempDir}
              validationId={validationId}
              processData={processData}
              onProcessComplete={handleProcessComplete}
              onPrev={() => handleStepChange(2)}
              onFinish={() => handleNavigation('')}
            />
          }
        />
      </Routes>
    </div>
  );
};

export default ImportacionPage;