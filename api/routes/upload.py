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
from models.project import ProjectDataMinimal
from services.execution_service import get_execution_service
from services.storage.azure_storage_service import get_azure_storage_service
from services.audit_service import get_audit_service
from config.settings import get_settings
import json

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

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    test_type: Optional[str] = Form("libro_diario_import"),
    project_id: Optional[str] = Form(None),
    period: Optional[str] = Form(None),
    parent_execution_id: Optional[str] = Form(None),  # Para coordinar IDs entre LD y SS
    project_data: Optional[str] = Form(None)  # JSON string con datos del proyecto del Portal API
):
    """
    Upload a file for processing with structured naming and coordinated IDs

    Args:
        file: El archivo a subir
        test_type: Tipo de test (libro_diario_import, sumas_saldos_import)
        project_id: ID del proyecto
        period: Período de la prueba
        parent_execution_id: ID de ejecución padre para coordinar con Sumas y Saldos
        project_data: JSON string con datos del proyecto del Portal API (/api/v1/users/me/projects)
                     Debe contener: tenant_id, workspace_id, user_id, project_id, etc.
    """
    settings = get_settings()
    execution_service = get_execution_service()

    # Parsear datos del proyecto si se proporcionan
    parsed_project_data: Optional[ProjectDataMinimal] = None
    if project_data:
        try:
            project_data_dict = json.loads(project_data)
            parsed_project_data = ProjectDataMinimal(**project_data_dict)
        except Exception as e:
            print(f"⚠️  Error parseando project_data: {e}")
            # Continuar sin project_data si falla el parseo

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
        update_data = {
            "file_path": file_path,
            "file_name": original_filename,
            "file_type": file_type,
            "test_type": test_type,
            "project_id": project_id,
            "period": period,
            "parent_execution_id": parent_execution_id,
            "file_size": final_file_size,
            "file_extension": file_extension
        }

        # Agregar datos del proyecto si están disponibles
        if parsed_project_data:
            update_data.update({
                "tenant_id": parsed_project_data.tenant_id,
                "workspace_id": parsed_project_data.workspace_id,
                "user_id": parsed_project_data.user_id,
                "username": parsed_project_data.username,
                "project_code": parsed_project_data.project_code,
                "project_name": parsed_project_data.project_name,
                "main_entity_name": parsed_project_data.main_entity_name
            })

        execution_service.update_execution(execution_id, **update_data)

        # Para Sumas y Saldos, también actualizar sumas_saldos_raw_path
        if file_type == "Sys":
            execution_service.update_execution(
                execution_id,
                sumas_saldos_raw_path=file_path
            )

        # Registrar en auditoría si está habilitado
        if settings.azure_sql_audit_enabled and project_id and period and final_file_size:
            try:
                audit_service = get_audit_service()

                # Preparar datos comunes
                je_original_name = None
                je_file_name = None
                je_extension = None
                je_size = None
                tb_original_name = None
                tb_file_name = None
                tb_extension = None
                tb_size = None

                # Obtener datos del proyecto (si están disponibles)
                audit_tenant_id = parsed_project_data.tenant_id if parsed_project_data else None
                audit_workspace_id = parsed_project_data.workspace_id if parsed_project_data else None
                audit_user_id = parsed_project_data.user_id if parsed_project_data else None
                audit_project_id = parsed_project_data.project_id if parsed_project_data else int(project_id) if project_id and project_id.isdigit() else None

                if file_type == "Je":
                    # Libro Diario (Journal Entry)
                    je_original_name = original_filename
                    je_file_name = f"{execution_id}_{os.path.splitext(original_filename)[0]}_{file_type}"
                    je_extension = file_extension.lstrip('.')
                    je_size = final_file_size

                    # Registrar auditoría para JE con datos reales del proyecto
                    if audit_project_id:
                        audit_id = audit_service.register_import_execution(
                            project_id=audit_project_id,
                            period=period,
                            je_original_file_name=je_original_name,
                            je_file_name=je_file_name,
                            je_file_extension=je_extension,
                            je_file_size_bytes=je_size,
                            tenant_id=audit_tenant_id,
                            workspace_id=audit_workspace_id,
                            auth_user_id=audit_user_id,
                            external_gid=execution_id,
                            correlation_id=execution_id
                        )

                        if audit_id:
                            print(f"✓ Auditoría registrada con ID: {audit_id}")
                    else:
                        print(f"⚠️  No se pudo determinar project_id para auditoría")

                elif file_type == "Sys" and parent_execution_id:
                    # Trial Balance con parent - obtener datos del JE
                    try:
                        parent_execution = execution_service.get_execution(parent_execution_id)

                        # Datos del Journal Entry (del padre)
                        je_original_name = parent_execution.file_name
                        je_file_name = f"{parent_execution_id}_{os.path.splitext(parent_execution.file_name)[0]}_Je"
                        je_extension = parent_execution.file_extension.lstrip('.') if parent_execution.file_extension else 'csv'
                        je_size = parent_execution.file_size or 0

                        # Datos del Trial Balance (actual)
                        tb_original_name = original_filename
                        tb_file_name = f"{execution_id}_{os.path.splitext(original_filename)[0]}_{file_type}"
                        tb_extension = file_extension.lstrip('.')
                        tb_size = final_file_size

                        # Usar datos del proyecto del padre si no están disponibles aquí
                        if not audit_tenant_id and hasattr(parent_execution, 'tenant_id') and parent_execution.tenant_id:
                            audit_tenant_id = parent_execution.tenant_id
                        if not audit_workspace_id and hasattr(parent_execution, 'workspace_id') and parent_execution.workspace_id:
                            audit_workspace_id = parent_execution.workspace_id
                        if not audit_user_id and hasattr(parent_execution, 'user_id') and parent_execution.user_id:
                            audit_user_id = parent_execution.user_id
                        if not audit_project_id and hasattr(parent_execution, 'project_id') and parent_execution.project_id:
                            # El project_id en parent_execution puede ser string
                            try:
                                audit_project_id = int(parent_execution.project_id) if isinstance(parent_execution.project_id, str) and parent_execution.project_id.isdigit() else parent_execution.project_id
                            except:
                                pass

                        # Registrar auditoría con ambos archivos
                        if audit_project_id:
                            audit_id = audit_service.register_import_execution(
                                project_id=audit_project_id,
                                period=period,
                                je_original_file_name=je_original_name,
                                je_file_name=je_file_name,
                                je_file_extension=je_extension,
                                je_file_size_bytes=je_size,
                                tb_original_file_name=tb_original_name,
                                tb_file_name=tb_file_name,
                                tb_file_extension=tb_extension,
                                tb_file_size_bytes=tb_size,
                                tenant_id=audit_tenant_id,
                                workspace_id=audit_workspace_id,
                                auth_user_id=audit_user_id,
                                external_gid=parent_execution_id,  # Usar el ID del padre como GUID
                                correlation_id=execution_id
                            )

                            if audit_id:
                                print(f"✓ Auditoría JE+TB registrada con ID: {audit_id}")
                        else:
                            print(f"⚠️  No se pudo determinar project_id para auditoría JE+TB")

                    except Exception as e:
                        print(f"⚠️  No se pudo obtener datos del parent para auditoría: {e}")

            except Exception as e:
                # No fallar el upload si la auditoría falla
                print(f"⚠️  Error registrando auditoría: {e}")

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