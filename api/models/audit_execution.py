"""
Modelos Pydantic para la ejecución de auditoría y análisis de asientos contables
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
import uuid


class FileMetadata(BaseModel):
    """Metadatos de archivo cargado"""
    original_file_name: str = Field(..., description="Nombre original del archivo subido por el usuario")
    file_name: str = Field(..., description="Nombre normalizado del archivo para almacenamiento")
    file_extension: str = Field(..., description="Extensión del archivo (csv, xlsx, xls, txt)")
    file_size_bytes: int = Field(..., description="Tamaño del archivo en bytes", ge=0)
    file_type_code: str = Field(default="CSV", description="Tipo de archivo: CSV, XLS, XLSX")
    file_data_structure_type_code: str = Field(
        default="TABULAR",
        description="Estructura de datos: TABULAR, HEADER_AND_LINES"
    )

    @validator('file_extension')
    def validate_extension(cls, v):
        allowed_extensions = ['csv', 'xlsx', 'xls', 'txt']
        if v.lower() not in allowed_extensions:
            raise ValueError(f"Extensión debe ser una de: {', '.join(allowed_extensions)}")
        return v.lower()

    @validator('file_type_code')
    def validate_file_type(cls, v):
        allowed_types = ['CSV', 'XLS', 'XLSX', 'TXT']
        if v.upper() not in allowed_types:
            raise ValueError(f"Tipo de archivo debe ser uno de: {', '.join(allowed_types)}")
        return v.upper()


class AuditExecutionRequest(BaseModel):
    """
    Request para crear una nueva ejecución de análisis de asientos contables.

    Todos los datos vienen del front-end y se usan para ejecutar el stored procedure
    sp_insert_audit_test_exec_je_analysis
    """

    # Identificadores de proyecto (vienen del JSON users-me-projects)
    tenant_id: int = Field(..., description="ID del tenant", example=100)
    workspace_id: int = Field(..., description="ID del workspace", example=100)
    project_id: int = Field(..., description="ID del proyecto", example=1150)

    # Usuario autenticado
    auth_user_id: int = Field(..., description="ID del usuario autenticado", example=1186)

    # ID de ejecución (generado por el front o por nosotros)
    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="ID único de la ejecución"
    )

    # Parámetros de período fiscal
    fiscal_year: int = Field(..., description="Año fiscal", example=2024, ge=2000, le=2100)
    period_beginning_date: date = Field(..., description="Fecha de inicio del período", example="2024-01-01")
    period_ending_date: date = Field(..., description="Fecha de fin del período", example="2024-12-31")

    # Metadatos del archivo Libro Diario (Journal Entries)
    journal_entry_file: FileMetadata = Field(..., description="Metadatos del archivo Libro Diario")

    # Metadatos del archivo Sumas y Saldos (Trial Balance)
    trial_balance_file: FileMetadata = Field(..., description="Metadatos del archivo Sumas y Saldos")

    # Parámetros opcionales
    storage_relative_path: Optional[str] = Field(
        None,
        description="Ruta relativa de almacenamiento en Azure Storage. Si no se proporciona, se genera automáticamente"
    )
    external_gid: Optional[str] = Field(None, description="GUID externo para tracking")
    correlation_id: Optional[str] = Field(None, description="ID de correlación para logs")
    language_code: str = Field(default="es-ES", description="Código de idioma")

    @validator('period_ending_date')
    def validate_period_dates(cls, v, values):
        """Validar que la fecha final sea posterior a la inicial"""
        if 'period_beginning_date' in values and v < values['period_beginning_date']:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return v

    @validator('storage_relative_path', always=True)
    def generate_storage_path(cls, v, values):
        """Generar ruta de almacenamiento si no se proporciona"""
        if v is None and 'tenant_id' in values and 'workspace_id' in values:
            tenant_id = values['tenant_id']
            workspace_id = values['workspace_id']
            return f"tenants/{tenant_id}/workspaces/{workspace_id}/"
        return v


class AuditExecutionResponse(BaseModel):
    """Respuesta del endpoint de creación de ejecución"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    execution_id: str = Field(..., description="ID de la ejecución creada")
    audit_test_exec_id: Optional[int] = Field(None, description="ID generado en la base de datos")
    message: str = Field(..., description="Mensaje descriptivo del resultado")

    # Información de error (si aplica)
    error_code: Optional[str] = Field(None, description="Código de error")
    error_message: Optional[str] = Field(None, description="Mensaje de error detallado")
    error_title: Optional[str] = Field(None, description="Título del error")
    error_severity: Optional[str] = Field(None, description="Severidad del error")
    error_category: Optional[str] = Field(None, description="Categoría del error")

    # Metadatos de la respuesta
    timestamp: str = Field(..., description="Timestamp de la respuesta")


class StoredProcedureResult(BaseModel):
    """Resultado interno del stored procedure"""
    new_id: Optional[int] = None
    has_error: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_title: Optional[str] = None
    error_severity: Optional[str] = None
    error_category: Optional[str] = None
