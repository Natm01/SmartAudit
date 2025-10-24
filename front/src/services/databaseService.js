// frontend/src/services/databaseService.js
import api from './api';

const databaseService = {
  /**
   * Prueba la conexión a la base de datos
   * @returns {Promise} Respuesta con el estado de la conexión
   */
  testConnection: async () => {
    try {
      const response = await api.get('/api/database/test-connection');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  }
};

export default databaseService;
