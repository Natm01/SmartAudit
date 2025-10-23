// frontend/src/services/projectService.js
import portalApi from './portalApi';

class ProjectService {
  /**
   * Obtener todos los proyectos del usuario autenticado desde el Portal API
   * @returns {Promise<Array>} Lista de proyectos transformados
   */
  async getAllProjects() {
    try {
      const response = await portalApi.get('/api/v1/users/me/projects');

      // Transformar los datos de la respuesta al formato esperado por el frontend
      // Respuesta del API: [{ project_id, project_name, ... }]
      // Formato esperado: [{ _id, name, ... }]
      const projects = response.data.map(project => ({
        _id: project.project_id.toString(),
        id: project.project_code,
        name: project.project_name,
        // Datos adicionales que pueden ser útiles
        role: project.role_name,
        office: project.office_name,
        department: project.department_name,
        client: project.main_entity_name,
        service: project.service_name,
        status: project.project_state_name,
        stateCategory: project.project_state_category_name,
        // Mantener todos los datos originales por si se necesitan
        ...project
      }));

      console.log(`✅ Loaded ${projects.length} projects from Portal API`);

      return {
        success: true,
        projects: projects,
        total: projects.length
      };
    } catch (error) {
      console.error('❌ Error fetching projects from Portal API:', error);
      throw error;
    }
  }

  /**
   * Obtener un proyecto específico por ID
   * @param {string} projectId - ID del proyecto
   * @returns {Promise<Object>} Datos del proyecto
   */
  async getProjectById(projectId) {
    try {
      // Como el API no tiene un endpoint específico para un proyecto,
      // obtenemos todos y filtramos
      const allProjects = await this.getAllProjects();
      const project = allProjects.projects.find(p => p._id === projectId || p.id === projectId);

      if (!project) {
        throw new Error(`Project with ID '${projectId}' not found`);
      }

      return {
        success: true,
        project: project
      };
    } catch (error) {
      console.error('❌ Error fetching project by ID:', error);
      throw error;
    }
  }
}

export default new ProjectService();