# models/project.py
"""
Project data models from Portal API
"""
from pydantic import BaseModel
from typing import Optional


class ProjectData(BaseModel):
    """
    Project data from /api/v1/users/me/projects endpoint
    """
    id: int
    tenant_id: int
    workspace_id: int
    user_id: int
    username: str
    role_code: str
    role_name: str
    project_id: int
    project_code: str
    project_name: str
    office_name: str
    department_name: str
    main_entity_code: str
    main_entity_name: str
    service_code: str
    service_name: str
    service_category_code: str
    service_category_name: str
    project_state_code: str
    project_state_name: str
    project_state_category_code: str
    project_state_category_name: str
    project_analysis_state_code: str
    project_analysis_state_name: str


class ProjectDataMinimal(BaseModel):
    """
    Minimal project data needed for audit registration
    """
    tenant_id: int
    workspace_id: int
    user_id: int
    username: Optional[str] = None
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    main_entity_name: Optional[str] = None
