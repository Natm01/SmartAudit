// frontend/src/services/projectService.js
import portalApi from './portalApi';

class ProjectService {
  /**
   * Obtener todos los proyectos del usuario autenticado desde el Portal API
   * @returns {Promise<Array>} Lista de proyectos transformados
   */
  async getAllProjects() {
    try {
      let allProjects = [];
      let currentPage = 1;
      let hasMorePages = true;

      // Obtener todas las páginas de proyectos
      while (hasMorePages) {
        console.log(`📥 Obteniendo página ${currentPage} de proyectos...`);

        const response = await portalApi.get('/api/v1/users/me/projects', {
          params: {
            pageNumber: currentPage,
            pageSize: 100 // Solicitar 100 proyectos por página
          }
        });

        const projectsData = response.data.items || [];

        // Transformar y agregar los proyectos de esta página
        const transformedProjects = projectsData.map(project => ({
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

        allProjects = [...allProjects, ...transformedProjects];

        // Verificar si hay más páginas
        hasMorePages = response.data.hasNextPage;
        currentPage++;

        console.log(`✅ Página ${currentPage - 1}: ${transformedProjects.length} proyectos (Total acumulado: ${allProjects.length})`);
      }

      console.log(`🎉 Total de proyectos cargados: ${allProjects.length}`);

      return {
        success: true,
        projects: allProjects,
        total: allProjects.length
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