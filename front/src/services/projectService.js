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
      let totalCount = 0;
      const MAX_PAGES = 20; // Límite de seguridad para evitar bucle infinito

      console.log('📥 Obteniendo todos los proyectos del usuario...');

      // Obtener todas las páginas de proyectos
      while (currentPage <= MAX_PAGES) {
        const response = await portalApi.get(`/api/v1/users/me/projects?pageSize=100&pageNumber=${currentPage}`);

        const projectsData = response.data.items || [];
        totalCount = response.data.totalCount || 0;

        // Si no hay proyectos en esta página, salir del bucle
        if (projectsData.length === 0) {
          console.log('✅ No hay más proyectos');
          break;
        }

        console.log(`📥 Página ${currentPage}: ${projectsData.length} proyectos`);

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

        // Verificar si ya tenemos todos los proyectos
        if (allProjects.length >= totalCount) {
          console.log(`✅ Obtenidos todos los proyectos: ${allProjects.length}/${totalCount}`);
          break;
        }

        // Verificar si hay más páginas
        if (!response.data.hasNextPage) {
          console.log('✅ No hay más páginas');
          break;
        }

        currentPage++;
      }

      if (currentPage > MAX_PAGES) {
        console.warn(`⚠️ Se alcanzó el límite de seguridad de ${MAX_PAGES} páginas`);
      }

      console.log(`🎉 Total de proyectos cargados: ${allProjects.length} de ${totalCount}`);

      return {
        success: true,
        projects: allProjects,
        total: totalCount || allProjects.length
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