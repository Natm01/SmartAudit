# models/execution.py
"""
Execution models with additional fields for file coordination
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ExecutionStatus(BaseModel):
    """Execution status model with enhanced metadata"""
    id: str
    status: str = "pending"
    step: Optional[str] = None
    created_at: str
    updated_at: str
    file_name: str
    file_path: str
    result_path: Optional[str] = None
    error: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None

    # Metadatos del archivo
    file_size: Optional[int] = None  # Tamaño del archivo en bytes
    file_extension: Optional[str] = None  # Extensión del archivo (.csv, .xlsx, etc.)

    # Campos para coordinación
    file_type: Optional[str] = None  # "Je" para Journal Entries, "Sys" para Sumas y Saldos
    test_type: Optional[str] = None  # "libro_diario_import", "sumas_saldos_import"
    project_id: Optional[str] = None
    period: Optional[str] = None
    parent_execution_id: Optional[str] = None  # Para vincular SS con LD
    
    # Campos para mapeo manual (Libro Diario)
    mapeo_results: Optional[Dict[str, Any]] = None
    manual_mapping_required: bool = False
    unmapped_fields_count: int = 0
    output_file: Optional[str] = None  # Path del archivo final mapeado (última versión)
    auto_mapeo_output_file: Optional[str] = None  # 🆕 Path del archivo AUTO-MAPEADO
    manual_mapeo_output_file: Optional[str] = None  # 🆕 Path del archivo MANUAL-MAPEADO
    manual_mapeo_report_file: Optional[str] = None  # 🆕 Path del reporte de mapeo manual

    # Campos para Sumas y Saldos (Trial Balance)
    sumas_saldos_raw_path: Optional[str] = None  # Path del Excel original de Sumas y Saldos
    sumas_saldos_status: Optional[str] = None  # "uploaded", "processing", "completed", "failed"
    sumas_saldos_mapping: Optional[Dict[str, Any]] = None  # Mapeo de columnas de Sumas y Saldos
    sumas_saldos_csv_path: Optional[str] = None  # Path del CSV procesado (última versión)
    sumas_saldos_auto_csv_path: Optional[str] = None  # 🆕 Path del CSV AUTO-MAPEADO
    sumas_saldos_manual_csv_path: Optional[str] = None  # 🆕 Path del CSV MANUAL-MAPEADO
    sumas_saldos_stats: Optional[Dict[str, Any]] = None  # Estadísticas del procesamiento
    sumas_saldos_error: Optional[str] = None  # Error si el procesamiento falla
    sumas_saldos_manual_mapping_required: Optional[bool] = False  # Si necesita mapeo manual
    sumas_saldos_unmapped_count: Optional[int] = 0  # Número de campos sin mapear
    
    # ==========================================
    # 🆕 NUEVO CAMPO PARA VALIDACIONES CONTABLES
    # ==========================================
    validation_rules_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from the 4-phase accounting validation rules process"
    )

class UploadResponse(BaseModel):
    """Upload response model"""
    execution_id: str
    file_name: str
    message: str
    sp_params: Optional[Dict[str, Any]] = None  # Parámetros enviados al SP para debugging

class ValidationResponse(BaseModel):
    """Validation response model"""
    execution_id: str
    message: str

class ConversionResponse(BaseModel):
    """Conversion response model"""
    execution_id: str
    message: str

class ExecutionSummary(BaseModel):
    """Summary model for execution lists"""
    execution_id: str
    file_name: str
    file_type: Optional[str] = None
    test_type: Optional[str] = None
    status: str
    step: Optional[str] = None
    created_at: str
    updated_at: str
    project_id: Optional[str] = None
    period: Optional[str] = None
    parent_execution_id: Optional[str] = None
    error: Optional[str] = None
    # Añadir resumen de Trial Balance
    trial_balance_status: Optional[str] = None
    trial_balance_file_name: Optional[str] = None

class CoordinatedUploadRequest(BaseModel):
    """Request model for coordinated uploads (LD + SS)"""
    libro_diario_files: List[str] = Field(description="List of Libro Diario file names")
    sumas_saldos_file: Optional[str] = Field(None, description="Sumas y Saldos file name")
    project_id: str
    period: str
    test_type: str = "libro_diario_import"

class CoordinatedUploadResponse(BaseModel):
    """Response for coordinated uploads"""
    libro_diario_execution_id: str
    sumas_saldos_execution_id: Optional[str] = None
    files_uploaded: Dict[str, str]  # filename -> execution_id mapping
    message: str

class FileStructureInfo(BaseModel):
    """Information about file structure in storage"""
    execution_id: str
    original_filename: str
    structured_filename: str  # execution_id_filename_filetype.ext
    file_type: str  # "Je" or "Sys"
    container: str
    blob_url: str
    size_bytes: Optional[int] = None
    upload_date: str

# NUEVOS MODELOS para Trial Balance

class TrialBalanceMappingRequest(BaseModel):
    """Request for trial balance field mapping"""
    mapping: Dict[str, str] = Field(
        description="Column mapping: source_column -> standard_field"
    )

class TrialBalanceMappingResponse(BaseModel):
    """Response for trial balance mapping operation"""
    execution_id: str
    mapping_applied: Dict[str, str]
    csv_path: str
    stats: Dict[str, Any]
    manual_mapping_required: bool
    unmapped_fields_count: int
    message: str

class TrialBalanceUnmappedField(BaseModel):
    """Unmapped field information for trial balance"""
    column_name: str
    sample_data: List[str]
    data_type: str
    suggestions: List[Dict[str, Any]]
    total_values: int
    non_null_values: int
    unique_values: int

# NUEVOS MODELOS para Audit Test Execution

class AuditTestExecRequest(BaseModel):
    """Request model for creating an audit test execution"""
    # Parámetros de usuario y contexto
    auth_user_id: int
    tenant_id: int
    workspace_id: int
    project_id: int

    # Parámetros globales
    period_beginning_date: str = Field(description="Fecha de inicio del período (YYYY-MM-DD)")
    period_ending_date: str = Field(description="Fecha de fin del período (YYYY-MM-DD)")
    fiscal_year: int

    # Parámetros de Journal Entry
    je_original_file_name: str
    je_file_name: str
    je_file_size_bytes: int
    je_file_type_code: str = 'CSV'
    je_file_data_structure_type_code: str = 'TABULAR'
    je_file_extension: str = 'csv'

    # Parámetros de Trial Balance
    tb_original_file_name: str
    tb_file_name: str
    tb_file_size_bytes: int
    tb_file_type_code: str = 'CSV'
    tb_file_data_structure_type_code: str = 'TABULAR'
    tb_file_extension: str = 'csv'

    # Parámetros opcionales
    external_gid: Optional[str] = None
    correlation_id: Optional[str] = None
    language_code: str = 'es-ES'

class AuditTestExecResponse(BaseModel):
    """Response model for audit test execution creation"""
    new_id: Optional[int] = Field(description="ID del registro creado en audit_test_exec")
    has_error: bool = Field(description="Indica si hubo error")
    error_code: Optional[str] = Field(None, description="Código del error")
    error_message: Optional[str] = Field(None, description="Mensaje del error")
    error_title: Optional[str] = Field(None, description="Título del error")
    error_severity: Optional[str] = Field(None, description="Severidad del error")
    error_category: Optional[str] = Field(None, description="Categoría del error")