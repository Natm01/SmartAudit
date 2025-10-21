# services/execution_service.py - Con persistencia para Azure
import os
import uuid
import json
import tempfile
import logging
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import HTTPException
from pathlib import Path

from models.execution import ExecutionStatus
from config.settings import get_settings
from utils.serialization import safe_json_response

logger = logging.getLogger(__name__)

class ExecutionService:
    def __init__(self):
        self.settings = get_settings()
        
        # Detectar si estamos en Azure
        self.is_azure = os.getenv("CONTAINER_APP_NAME") is not None
        
        if self.is_azure:
            # En Azure, usar persistencia en disco
            self.storage_type = "file"
            self.storage_path = "/tmp/executions"
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info(f"Azure detected - using file storage at {self.storage_path}")
        else:
            # En local, usar memoria como antes
            self.storage_type = "memory"
            self.execution_store: Dict[str, ExecutionStatus] = {}
            logger.info("Local environment - using memory storage")
    
    def _get_execution_file_path(self, execution_id: str) -> str:
        """Get file path for execution data"""
        return os.path.join(self.storage_path, f"{execution_id}.json")
    
    def _save_execution_to_file(self, execution_id: str, execution: ExecutionStatus):
        """Save execution to file"""
        try:
            file_path = self._get_execution_file_path(execution_id)
            execution_data = execution.dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(execution_data, f, indent=2, default=str)
            
            logger.debug(f"Saved execution {execution_id} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save execution {execution_id}: {e}")
            raise
    
    def _load_execution_from_file(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Load execution from file"""
        try:
            file_path = self._get_execution_file_path(execution_id)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                execution_data = json.load(f)
            
            # Ensure all required fields exist
            required_fields = ['id', 'status', 'created_at', 'updated_at']
            for field in required_fields:
                if field not in execution_data:
                    logger.warning(f"Missing field {field} in execution {execution_id}")
                    if field == 'id':
                        execution_data['id'] = execution_id
                    elif field in ['created_at', 'updated_at']:
                        execution_data[field] = datetime.now().isoformat()
                    elif field == 'status':
                        execution_data['status'] = 'pending'
            
            execution = ExecutionStatus(**execution_data)
            logger.debug(f"Loaded execution {execution_id} from {file_path}")
            return execution
            
        except Exception as e:
            logger.error(f"Failed to load execution {execution_id}: {e}")
            return None
    
    def _delete_execution_file(self, execution_id: str):
        """Delete execution file"""
        try:
            file_path = self._get_execution_file_path(execution_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted execution file {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete execution file {execution_id}: {e}")
    
    def create_execution(self, file_name: str, file_path: str, execution_id: str = None) -> str:
        """Create a new execution record with persistence"""
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        now = datetime.now().isoformat()
        
        execution = ExecutionStatus(
            id=execution_id,
            status="pending",
            created_at=now,
            updated_at=now,
            file_name=file_name,
            file_path=file_path
        )
        
        if self.storage_type == "file":
            self._save_execution_to_file(execution_id, execution)
        else:
            self.execution_store[execution_id] = execution
        
        logger.info(f"Created execution: {execution_id} for file: {file_name}")
        return execution_id
    
    def create_coordinated_execution(self, file_name: str, file_path: str, 
                                   file_type: str, test_type: str,
                                   project_id: str = None, period: str = None,
                                   parent_execution_id: str = None) -> str:
        """Create execution with full coordination metadata and persistence"""
        # Para Sumas y Saldos, crear ID derivado del parent
        if parent_execution_id and file_type == "Sys":
            execution_id = f"{parent_execution_id}-ss"
        else:
            execution_id = str(uuid.uuid4())
        
        now = datetime.now().isoformat()
        
        execution = ExecutionStatus(
            id=execution_id,
            status="pending",
            created_at=now,
            updated_at=now,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            test_type=test_type,
            project_id=project_id,
            period=period,
            parent_execution_id=parent_execution_id
        )
        
        if self.storage_type == "file":
            self._save_execution_to_file(execution_id, execution)
        else:
            self.execution_store[execution_id] = execution
        
        logger.info(f"Created coordinated execution: {execution_id}")
        logger.info(f"   File: {file_name} (Type: {file_type})")
        logger.info(f"   Storage: {self.storage_type}")
        if parent_execution_id:
            logger.info(f"   Parent: {parent_execution_id}")
        
        return execution_id
    
    def get_execution(self, execution_id: str) -> ExecutionStatus:
        """Get execution by ID with persistence support"""
        logger.debug(f"Looking for execution {execution_id} in {self.storage_type} storage")
        
        if self.storage_type == "file":
            execution = self._load_execution_from_file(execution_id)
            if execution is None:
                logger.warning(f"Execution {execution_id} not found in file storage")
                raise HTTPException(status_code=404, detail=f"Execution ID {execution_id} not found")
            return execution
        else:
            if execution_id not in self.execution_store:
                logger.warning(f"Execution {execution_id} not found in memory storage")
                raise HTTPException(status_code=404, detail=f"Execution ID {execution_id} not found")
            return self.execution_store[execution_id]
    
    def update_execution(self, execution_id: str, **kwargs) -> None:
        """Update execution status with persistence"""
        logger.debug(f"Updating execution {execution_id} with: {list(kwargs.keys())}")
        
        # Get current execution
        execution = self.get_execution(execution_id)
        execution_dict = execution.dict()
        
        # Lista de campos permitidos para actualización
        allowed_fields = {
            'status', 'step', 'file_path', 'result_path', 'error', 'stats',
            'file_type', 'test_type', 'project_id', 'period', 'parent_execution_id',
            'mapeo_results', 'manual_mapping_required', 'unmapped_fields_count',
            'file_name', 
            'output_file',  # 🆕 AGREGAR ESTA LÍNEA
            'validation_rules_results',  # 🆕 AGREGAR ESTA LÍNEA
            'sumas_saldos_raw_path', 'sumas_saldos_status', 'sumas_saldos_mapping',
            'sumas_saldos_csv_path', 'sumas_saldos_stats', 'sumas_saldos_error',
            'sumas_saldos_manual_mapping_required', 'sumas_saldos_unmapped_count'
        }
        
        updated_fields = []
        for key, value in kwargs.items():
            if key in allowed_fields and key in execution_dict:
                execution_dict[key] = value
                updated_fields.append(key)
        
        execution_dict["updated_at"] = datetime.now().isoformat()
        updated_execution = ExecutionStatus(**execution_dict)
        
        # Save updated execution
        if self.storage_type == "file":
            self._save_execution_to_file(execution_id, updated_execution)
        else:
            self.execution_store[execution_id] = updated_execution
        
        if updated_fields:
            logger.info(f"📝 Updated execution {execution_id}: {', '.join(updated_fields)}")
    
    def get_execution_safe(self, execution_id: str) -> Dict:
        """Get execution with safe JSON serialization"""
        try:
            execution = self.get_execution(execution_id)
            return safe_json_response(execution.dict())
        except HTTPException:
            # Return a more informative error for debugging
            logger.error(f"Execution {execution_id} not found - available executions:")
            if self.storage_type == "file":
                try:
                    files = os.listdir(self.storage_path)
                    execution_files = [f for f in files if f.endswith('.json')]
                    logger.error(f"Available execution files: {execution_files}")
                except:
                    logger.error("Could not list execution files")
            else:
                logger.error(f"Available executions: {list(self.execution_store.keys())}")
            raise
    
    def list_executions(self, file_type: str = None, 
                       parent_execution_id: str = None) -> List[dict]:
        """List executions with optional filtering and persistence support"""
        executions = []
        
        if self.storage_type == "file":
            try:
                files = os.listdir(self.storage_path)
                execution_files = [f for f in files if f.endswith('.json')]
                
                for file_name in execution_files:
                    execution_id = file_name[:-5]  # Remove .json
                    try:
                        execution = self._load_execution_from_file(execution_id)
                        if execution:
                            executions.append(execution)
                    except Exception as e:
                        logger.warning(f"Could not load execution {execution_id}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Could not list executions from file storage: {e}")
                return []
        else:
            executions = list(self.execution_store.values())
        
        # Apply filters
        filtered_executions = []
        for execution in executions:
            if file_type and getattr(execution, 'file_type', None) != file_type:
                continue
            if parent_execution_id and getattr(execution, 'parent_execution_id', None) != parent_execution_id:
                continue
            filtered_executions.append(execution)
        
        # Convert to dict and sort by creation date
        result = [exec.dict() if hasattr(exec, 'dict') else exec for exec in filtered_executions]
        result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return result
    
    def delete_execution(self, execution_id: str) -> bool:
        """Delete execution record with persistence"""
        try:
            execution = self.get_execution(execution_id)  # Verify it exists
            
            if self.storage_type == "file":
                self._delete_execution_file(execution_id)
            else:
                if execution_id in self.execution_store:
                    del self.execution_store[execution_id]
            
            logger.info(f"Deleted execution: {execution_id} ({execution.file_name})")
            return True
        except HTTPException:
            logger.warning(f"Execution {execution_id} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Error deleting execution {execution_id}: {e}")
            return False
    
    def get_coordinated_executions(self, execution_id: str) -> Dict[str, Optional[ExecutionStatus]]:
        """Get related executions (parent and children) with persistence"""
        result = {
            'libro_diario': None,
            'sumas_saldos': None
        }
        
        try:
            base_execution = self.get_execution(execution_id)
            
            if getattr(base_execution, 'file_type', None) == 'Je':
                result['libro_diario'] = base_execution
                
                ss_id = f"{execution_id}-ss"
                try:
                    ss_execution = self.get_execution(ss_id)
                    result['sumas_saldos'] = ss_execution
                except:
                    pass
                    
            elif getattr(base_execution, 'file_type', None) == 'Sys':
                result['sumas_saldos'] = base_execution
                
                parent_id = getattr(base_execution, 'parent_execution_id', None)
                if parent_id:
                    try:
                        ld_execution = self.get_execution(parent_id)
                        result['libro_diario'] = ld_execution
                    except:
                        pass
            else:
                result['libro_diario'] = base_execution
                
        except Exception as e:
            logger.error(f"Error getting coordinated executions for {execution_id}: {e}")
        
        return result

# Global service instance
_execution_service = None

def get_execution_service() -> ExecutionService:
    """Get global execution service instance"""
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService()
        logger.info(f"Initialized ExecutionService with {_execution_service.storage_type} storage")
    return _execution_service