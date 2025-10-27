# routes/upload.py 
"""
Upload routes with Azure Storage integration optimized for large files
Con nombres estructurados y coordinación de IDs
"""
import os
import shutil
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks, Form

from models.execution import UploadResponse
from services.execution_service import get_execution_service
from services.storage.azure_storage_service import get_azure_storage_service
from services.audit_test_service import get_audit_test_service
from config.settings import get_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Prefijo correcto que espera el frontend
router = APIRouter(prefix="/smau-proto/api/import", tags=["upload"])

class ProgressTracker:
    """Simple progress tracker for large file uploads"""
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.progress = 0
        self.uploaded_bytes = 0
        self.total_bytes = 0
        self.status = "starting"
    
    def update(self, progress: float, uploaded: int, total: int):
        self.progress = progress
        self.uploaded_bytes = uploaded
        self.total_bytes = total
        self.status = "uploading"

# Global progress tracker
upload_progress = {}

async def upload_large_file_background(execution_id: str, file_path: str, 
                                     file_type: str, azure_service, settings):
    """Background task for uploading large files to Azure Storage with structured names"""
    execution_service = get_execution_service()
    
    try:
        progress_tracker = ProgressTracker(execution_id)
        upload_progress[execution_id] = progress_tracker
        
        def progress_callback(progress: float, uploaded: int, total: int):
            progress_tracker.update(progress, uploaded, total)
        
        # Usar el nuevo método con nomenclatura simplificada
        blob_url = azure_service.upload_file_chunked(
            file_path, 
            execution_id=execution_id,
            container_type="upload",
            file_type=file_type,
            stage="upload",
            keep_original_name=True,  # Mantener nombre original
            progress_callback=progress_callback
        )
        
        execution_service.update_execution(execution_id, file_path=blob_url)
        progress_tracker.status = "completed"
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove temp file {file_path}: {e}")
        
    except Exception as e:
        if execution_id in upload_progress:
            upload_progress[execution_id].status = f"failed: {str(e)}"
        
        execution_service.update_execution(execution_id, error=f"Upload failed: {str(e)}")
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

def determine_file_type_from_test_type(test_type: str) -> str:
    """
    Determinar el tipo de archivo basado en test_type
    
    Returns:
        "Je" para Journal Entries (Libro Diario)
        "Sys" para Sumas y Saldos
    """
    if test_type and 'sumas' in test_type.lower():
        return "Sys"
    else:
        return "Je"  # Default para libro diario

def get_original_filename(upload_file: UploadFile) -> str:
    """
    Extraer nombre de archivo original limpio
    """
    if not upload_file.filename:
        return "unknown_file"

    # Limpiar el nombre de archivo de caracteres especiales si es necesario
    filename = upload_file.filename.strip()

    # Remover path si viene incluido
    if '/' in filename:
        filename = filename.split('/')[-1]
    if '\\' in filename:
        filename = filename.split('\\')[-1]

    return filename


async def try_execute_audit_test_sp(
    execution_id: str,
    file_type: str,
    parent_execution_id: Optional[str],
    auth_user_id: int,
    tenant_id: int,
    workspace_id: int,
    project_id: int,
    period_beginning_date: str,
    period_ending_date: str,
    fiscal_year: int,
    language_code: str = "es-ES"
):
    """
    Intenta ejecutar el SP de audit test si ambos archivos (JE y TB) están listos

    Args:
        execution_id: ID de la ejecución actual
        file_type: Tipo de archivo ("Je" o "Sys")
        parent_execution_id: ID del parent execution (si es TB)
        ... demás parámetros necesarios para el SP
    """
    try:
        execution_service = get_execution_service()

        # Determinar los IDs de JE y TB
        je_execution_id = None
        tb_execution_id = None

        if file_type == "Je":
            # Este es el Journal Entry
            je_execution_id = execution_id
            # Buscar si ya existe el Trial Balance
            tb_execution_id = f"{execution_id}-ss"
            try:
                tb_execution = execution_service.get_execution(tb_execution_id)
                # TB existe, verificar que esté completo
                if not tb_execution.file_path or tb_execution.file_path.startswith("uploading_to_azure://"):
                    logger.info(f"TB {tb_execution_id} aún no está completo, esperando...")
                    return None
            except:
                # TB no existe aún
                logger.info(f"TB {tb_execution_id} no existe aún, esperando...")
                return None

        elif file_type == "Sys":
            # Este es el Trial Balance
            tb_execution_id = execution_id
            # El parent debe ser el Journal Entry
            if not parent_execution_id:
                logger.warning(f"TB {execution_id} no tiene parent_execution_id, no se puede ejecutar SP")
                return None
            je_execution_id = parent_execution_id

            # Verificar que JE esté completo
            try:
                je_execution = execution_service.get_execution(je_execution_id)
                if not je_execution.file_path or je_execution.file_path.startswith("uploading_to_azure://"):
                    logger.info(f"JE {je_execution_id} aún no está completo, esperando...")
                    return None
            except:
                logger.warning(f"JE {je_execution_id} no existe, no se puede ejecutar SP")
                return None

        # Ambos archivos están listos, obtener sus metadatos
        je_execution = execution_service.get_execution(je_execution_id)
        tb_execution = execution_service.get_execution(tb_execution_id)

        logger.info(f"✅ Ambos archivos listos: JE={je_execution_id}, TB={tb_execution_id}")
        logger.info(f"Ejecutando SP para project_id={project_id}")

        # Preparar parámetros para el SP
        audit_service = get_audit_test_service()

        # Convertir fechas
        period_begin = datetime.strptime(period_beginning_date, "%Y-%m-%d").date()
        period_end = datetime.strptime(period_ending_date, "%Y-%m-%d").date()

        # Determinar file_type_code basado en la extensión
        je_ext = getattr(je_execution, 'file_extension', '.csv').lower()
        # Por ahora usar CSV para todos los archivos
        je_file_type_code = 'CSV'

        tb_ext = getattr(tb_execution, 'file_extension', '.csv').lower()
        # Por ahora usar CSV para todos los archivos
        tb_file_type_code = 'CSV'

        # Ejecutar el SP
        result = audit_service.insert_audit_test_exec_je_analysis(
            auth_user_id=auth_user_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=int(project_id),
            period_beginning_date=period_begin,
            period_ending_date=period_end,
            fiscal_year=fiscal_year,
            je_original_file_name=getattr(je_execution, 'file_name', ''),
            je_file_name=getattr(je_execution, 'file_name', '').lower().replace(' ', '_'),
            je_file_size_bytes=getattr(je_execution, 'file_size', 0) or 0,
            tb_original_file_name=getattr(tb_execution, 'file_name', ''),
            tb_file_name=getattr(tb_execution, 'file_name', '').lower().replace(' ', '_'),
            tb_file_size_bytes=getattr(tb_execution, 'file_size', 0) or 0,
            je_file_type_code=je_file_type_code,
            je_file_data_structure_type_code='TABULAR',
            je_file_extension=je_ext.lstrip('.'),
            tb_file_type_code=tb_file_type_code,
            tb_file_data_structure_type_code='TABULAR',
            tb_file_extension=tb_ext.lstrip('.'),
            language_code=language_code,
            correlation_id=f"upload-{je_execution_id}"
        )

        if result['has_error']:
            logger.error(f"❌ Error en SP: {result['error_code']} - {result['error_message']}")
        else:
            logger.info(f"✅ SP ejecutado exitosamente. audit_test_exec.id = {result['new_id']}")

        return result

    except Exception as e:
        logger.error(f"❌ Error al ejecutar SP: {e}", exc_info=True)
        return None

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    test_type: Optional[str] = Form("libro_diario_import"),
    project_id: Optional[str] = Form(None),
    period: Optional[str] = Form(None),
    parent_execution_id: Optional[str] = Form(None),  # Para coordinar IDs entre LD y SS
    # Nuevos parámetros para el SP
    auth_user_id: Optional[int] = Form(None),
    tenant_id: Optional[int] = Form(None),
    workspace_id: Optional[int] = Form(None),
    period_beginning_date: Optional[str] = Form(None),  # YYYY-MM-DD
    period_ending_date: Optional[str] = Form(None),     # YYYY-MM-DD
    fiscal_year: Optional[int] = Form(None),
    language_code: Optional[str] = Form("es-ES")
):
    """
    Upload a file for processing with structured naming and coordinated IDs

    Args:
        file: El archivo a subir
        test_type: Tipo de test (libro_diario_import, sumas_saldos_import)
        project_id: ID del proyecto
        period: Período de la prueba
        parent_execution_id: ID de ejecución padre para coordinar con Sumas y Saldos
        auth_user_id: ID del usuario autenticado (desde /api/v1/users/me)
        tenant_id: ID del tenant (desde /api/v1/users/me)
        workspace_id: ID del workspace (desde /api/v1/users/me)
        period_beginning_date: Fecha de inicio del período (YYYY-MM-DD)
        period_ending_date: Fecha de fin del período (YYYY-MM-DD)
        fiscal_year: Año fiscal
        language_code: Código de idioma (default: es-ES)
    """
    settings = get_settings()
    execution_service = get_execution_service()
    
    original_filename = get_original_filename(file)
    file_ext = os.path.splitext(original_filename)[1].lower()
    
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {settings.allowed_extensions}"
        )
    
    # Determinar el tipo de archivo para la estructura de nombres
    file_type = determine_file_type_from_test_type(test_type or "libro_diario_import")
    
    # Usar el método coordinado del ExecutionService
    if parent_execution_id and file_type == "Sys":
        # Para Sumas y Saldos, crear con parent_execution_id
        execution_id = execution_service.create_coordinated_execution(
            file_name=original_filename,
            file_path="",  # Se actualizará después
            file_type=file_type,
            test_type=test_type,
            project_id=project_id,
            period=period,
            parent_execution_id=parent_execution_id
        )
        
        # Verificar que el parent existe
        try:
            parent_execution = execution_service.get_execution(parent_execution_id)
            print(f" Parent execution found: {parent_execution_id}")
        except:
            print(f"⚠️  Warning: Parent execution {parent_execution_id} not found, proceeding anyway")
    else:
        # Para Libro Diario o casos sin parent
        execution_id = execution_service.create_coordinated_execution(
            file_name=original_filename,
            file_path="",  # Se actualizará después
            file_type=file_type,
            test_type=test_type,
            project_id=project_id,
            period=period,
            parent_execution_id=None
        )
    
    try:
        # Extraer extensión del archivo original
        file_extension = os.path.splitext(original_filename)[1]

        # Variable para almacenar el tamaño final del archivo
        final_file_size = None

        if settings.use_azure_storage:
            azure_service = get_azure_storage_service()

            # Calcular tamaño del archivo
            file_size = None
            if hasattr(file, 'size') and file.size:
                file_size = file.size
            elif hasattr(file.file, 'seek'):
                try:
                    current_pos = file.file.tell()
                    file.file.seek(0, 2)
                    file_size = file.file.tell()
                    file.file.seek(current_pos)
                except:
                    file_size = None
            
            if file_size and file_size > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size {file_size} exceeds maximum allowed size {settings.max_file_size}"
                )
            
            large_file_threshold = 500 * 1024 * 1024  # 500MB
            
            if file_size and file_size > large_file_threshold:
                # Archivos grandes: usar background processing
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"temp_upload_{execution_id}_{original_filename}")

                with open(temp_file_path, "wb") as buffer:
                    while True:
                        chunk = await file.read(8 * 1024 * 1024)  # 8MB chunks
                        if not chunk:
                            break
                        buffer.write(chunk)

                actual_size = os.path.getsize(temp_file_path)
                final_file_size = actual_size  # Guardar tamaño final
                if actual_size > settings.max_file_size:
                    os.remove(temp_file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size {actual_size} exceeds maximum allowed size {settings.max_file_size}"
                    )

                background_tasks.add_task(
                    upload_large_file_background,
                    execution_id,
                    temp_file_path,
                    file_type,
                    azure_service,
                    settings
                )

                file_path = f"uploading_to_azure://{execution_id}"
                
            else:
                # Archivos pequeños: subida inmediata con nombres estructurados
                file_content = await file.read()

                file_size = len(file_content)
                final_file_size = file_size  # Guardar tamaño final
                if file_size > settings.max_file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size {file_size} exceeds maximum allowed size {settings.max_file_size}"
                    )

                # Usar el método con nueva nomenclatura simplificada
                blob_url = azure_service.upload_from_memory(
                    file_content,
                    original_filename,
                    container_type="upload",
                    execution_id=execution_id,
                    file_type=file_type,
                    stage="upload",
                    keep_original_name=True  # Mantener el nombre original
                )

                file_path = blob_url
        else:
            # Local filesystem fallback
            file_content = await file.read()

            file_size = len(file_content)
            final_file_size = file_size  # Guardar tamaño final
            if file_size > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size {file_size} exceeds maximum allowed size {settings.max_file_size}"
                )

            os.makedirs(settings.full_upload_dir, exist_ok=True)

            # Aplicar naming estructurado también en local
            name_without_ext = os.path.splitext(original_filename)[0]
            extension = os.path.splitext(original_filename)[1]
            local_filename = f"{execution_id}_{name_without_ext}_{file_type}{extension}"
            file_path = os.path.join(settings.full_upload_dir, local_filename)

            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
        
        # Actualizar la ejecución con metadata adicional
        execution_service.update_execution(
            execution_id,
            file_path=file_path,
            file_name=original_filename,
            file_type=file_type,
            test_type=test_type,
            project_id=project_id,
            period=period,
            parent_execution_id=parent_execution_id,
            file_size=final_file_size,
            file_extension=file_extension
        )
        
        # Para Sumas y Saldos, también actualizar sumas_saldos_raw_path
        if file_type == "Sys":
            execution_service.update_execution(
                execution_id,
                sumas_saldos_raw_path=file_path
            )
        
        message = "Large file upload started in background" if file_path.startswith("uploading_to_azure://") else "File uploaded successfully"

        # Obtener nombre y extensión para el log
        name_without_ext = os.path.splitext(original_filename)[0]
        extension = os.path.splitext(original_filename)[1]

        print(f" Upload completed: {execution_id}")
        print(f"   Original: {original_filename}")
        print(f"   Blob name: {execution_id}_{name_without_ext}_{file_type}{extension}")
        print(f"   Storage path: {file_path}")
        if parent_execution_id:
            print(f"   Parent execution: {parent_execution_id}")

        # ===================================================================
        # INTENTAR EJECUTAR EL SP SI AMBOS ARCHIVOS ESTÁN LISTOS
        # ===================================================================
        # Solo intentar si:
        # 1. No es upload en background
        # 2. Tenemos todos los datos necesarios para el SP
        if (not file_path.startswith("uploading_to_azure://") and
            auth_user_id and tenant_id and workspace_id and project_id and
            period_beginning_date and period_ending_date and fiscal_year):

            logger.info(f"🔍 Verificando si ambos archivos están listos para ejecutar SP...")

            sp_result = await try_execute_audit_test_sp(
                execution_id=execution_id,
                file_type=file_type,
                parent_execution_id=parent_execution_id,
                auth_user_id=auth_user_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                project_id=project_id,
                period_beginning_date=period_beginning_date,
                period_ending_date=period_ending_date,
                fiscal_year=fiscal_year,
                language_code=language_code
            )

            if sp_result:
                if sp_result['has_error']:
                    logger.warning(f"⚠️  SP ejecutado pero devolvió error: {sp_result['error_message']}")
                    message += f" | SP ejecutado con error: {sp_result['error_code']}"
                else:
                    logger.info(f"✅ SP ejecutado exitosamente. audit_test_exec.id = {sp_result['new_id']}")
                    message += f" | audit_test_exec creado (ID: {sp_result['new_id']})"
        else:
            if file_path.startswith("uploading_to_azure://"):
                logger.info("⏳ Upload en background, SP se ejecutará cuando termine")
            else:
                logger.warning(f"⚠️  Faltan datos para ejecutar SP - auth_user_id: {auth_user_id}, tenant_id: {tenant_id}, workspace_id: {workspace_id}, project_id: {project_id}, dates: {period_beginning_date}/{period_ending_date}, fiscal_year: {fiscal_year}")

        return UploadResponse(
            execution_id=execution_id,
            file_name=original_filename,
            message=message
        )
        
    except Exception as e:
        # Limpiar en caso de error
        try:
            execution_service.delete_execution(execution_id)
        except:
            pass
        
        if execution_id in upload_progress:
            del upload_progress[execution_id]
        
        print(f"❌ Upload failed: {execution_id} - {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@router.get("/upload/{execution_id}/progress")
async def get_upload_progress(execution_id: str):
    """Get upload progress for large files"""
    if execution_id not in upload_progress:
        raise HTTPException(
            status_code=404,
            detail="Upload not found or already completed"
        )
    
    progress = upload_progress[execution_id]
    return {
        "execution_id": execution_id,
        "progress": progress.progress,
        "uploaded_bytes": progress.uploaded_bytes,
        "total_bytes": progress.total_bytes,
        "status": progress.status
    }

@router.get("/upload/{execution_id}/info")
async def get_upload_info(execution_id: str):
    """Get upload information and file details"""
    execution_service = get_execution_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        return {
            "execution_id": execution_id,
            "file_name": getattr(execution, 'file_name', None),
            "file_type": getattr(execution, 'file_type', None),
            "test_type": getattr(execution, 'test_type', None),
            "file_path": execution.file_path,
            "status": execution.status,
            "created_at": execution.created_at,
            "updated_at": execution.updated_at,
            "project_id": getattr(execution, 'project_id', None),
            "period": getattr(execution, 'period', None),
            "parent_execution_id": getattr(execution, 'parent_execution_id', None)
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_id}"
        )