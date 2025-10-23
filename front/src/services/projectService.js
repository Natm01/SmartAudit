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

      // La respuesta es un objeto paginado con la estructura:
      // { items: [...], totalCount, pageNumber, pageSize, totalPages, hasNextPage, hasPreviousPage }
      const projectsData = response.data.items || [];

      // Debug: ver un ejemplo de proyecto
      if (projectsData.length > 0) {
        console.log('📦 Ejemplo de proyecto:', projectsData[0]);
      }

      // Transformar los datos de la respuesta al formato esperado por el frontend
      // Respuesta del API usa camelCase: { projectId, projectName, ... }
      // Formato esperado: { _id, name, ... }
      const projects = projectsData.map(project => ({
        _id: project.projectId.toString(),
        id: project.projectCode,
        name: project.projectName,
        // Datos adicionales que pueden ser útiles
        role: project.roleName,
        office: project.officeName,
        department: project.departmentName,
        client: project.mainEntityName,
        service: project.serviceName,
        status: project.projectStateName,
        stateCategory: project.projectStateCategoryName,
        // Mantener todos los datos originales por si se necesitan
        ...project
      }));

      console.log(`✅ Loaded ${projects.length} of ${response.data.totalCount} projects from Portal API`);

      if (response.data.hasNextPage) {
        console.log(`⚠️ Nota: Hay más proyectos disponibles (${response.data.totalCount} en total, mostrando ${projects.length})`);
      }

      return {
        success: true,
        projects: projects,
        total: response.data.totalCount || projects.length
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