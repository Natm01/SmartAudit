// frontend/src/services/projectService.js
import portalApi from './portalApi';

class ProjectService {
  /**
   * Obtener todos los proyectos del usuario autenticado desde el Portal API
   * @returns {Promise<Array>} Lista de proyectos transformados
   */
  async getAllProjects() {
    try {
      // Solicitar todos los proyectos en una sola llamada con pageSize grande
      console.log('📥 Obteniendo todos los proyectos del usuario...');

      const response = await portalApi.get('/api/v1/users/me/projects?pageSize=1000&pageNumber=1');

      const projectsData = response.data.items || [];

      console.log(`📦 Total de proyectos en respuesta: ${projectsData.length} de ${response.data.totalCount}`);

      // Transformar los datos de la respuesta al formato esperado por el frontend
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

      // Si hay más proyectos que el límite, mostrar advertencia
      if (response.data.hasNextPage) {
        console.warn(`⚠️ Hay más proyectos disponibles (${response.data.totalCount} en total). Considera aumentar el pageSize o implementar paginación completa.`);
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