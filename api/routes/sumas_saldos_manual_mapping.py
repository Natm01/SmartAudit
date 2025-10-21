# routes/sumas_saldos_manual_mapping.py

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.execution_service import get_execution_service
from services.sumas_saldos_service import get_sumas_saldos_service

router = APIRouter(prefix="/smau-proto/api/import", tags=["sumas_saldos"])

# ==========================================
# Pydantic Models
# ==========================================

class MappingDecision(BaseModel):
    """User's mapping decision for Sumas y Saldos"""
    column_name: str
    selected_field: str
    confidence: float = 0.8
    force_override: bool = False  #  Soporte para re-mapeo

class ManualSumasSaldosMappingRequest(BaseModel):
    """Request to apply manual mappings to Sumas y Saldos"""
    mappings: List[MappingDecision]

class ApplySumasSaldosMappingResponse(BaseModel):
    """Response after applying Sumas y Saldos mappings"""
    execution_id: str
    applied_mappings: int
    updated_mapping: Dict[str, str]  #  Solo strings, no None
    csv_path: str
    stats: Dict[str, int]
    message: str

# ==========================================
# ENDPOINT: Apply Manual Mappings
# ==========================================

@router.post("/mapeo-sumas-saldos/{execution_id}/apply-manual-mapping", response_model=ApplySumasSaldosMappingResponse)
async def apply_sumas_saldos_manual_mapping(
    execution_id: str, 
    mapping_request: ManualSumasSaldosMappingRequest
):
    """
    Apply manual mappings selected by user for Sumas y Saldos.
    Regenerates the CSV file with the complete mapping.
    WITH FORCE_OVERRIDE SUPPORT FOR RE-MAPPING.
    """
    execution_service = get_execution_service()
    sumas_saldos_service = get_sumas_saldos_service()
    
    try:
        execution = execution_service.get_execution(execution_id)
        
        # Verify Sumas y Saldos mapping exists
        if not hasattr(execution, 'sumas_saldos_mapping') or not execution.sumas_saldos_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sumas y Saldos automatic mapping not completed yet"
            )
        
        # Get current mapping
        current_mapping = execution.sumas_saldos_mapping.copy()
        
        # Validate and apply new mappings
        applied_mappings = {}
        validation_errors = []
        
        #  Construir used_fields EXCLUYENDO los que se van a re-mapear
        columns_to_remap = {m.column_name for m in mapping_request.mappings if m.force_override}
        
        print(f"SUMAS Y SALDOS: Columns to remap (force_override=True): {columns_to_remap}")

        # Get already used fields, excluyendo los que vamos a re-mapear
        used_fields = set()
        for col_name, field_name in current_mapping.items():
            if field_name and col_name not in columns_to_remap:
                used_fields.add(field_name)
        
        print(f"SUMAS Y SALDOS: Used fields (excluding columns to remap): {used_fields}")

        for mapping in mapping_request.mappings:
            print(f"SUMAS Y SALDOS: Processing mapping: {mapping.column_name} -> {mapping.selected_field} (force_override={mapping.force_override})")
            
            #  Si force_override=True, permitir el re-mapeo
            if not mapping.force_override and mapping.selected_field in used_fields:
                error_msg = f"Field '{mapping.selected_field}' is already mapped to another column"
                print(f"SUMAS Y SALDOS: Validation error: {error_msg}")
                validation_errors.append(error_msg)
                continue
            
            #  Si re-mapeando, eliminar mapeo anterior
            if mapping.force_override:
                keys_to_remove = [
                    col for col, field in current_mapping.items() 
                    if field == mapping.selected_field and col != mapping.column_name
                ]
                for key in keys_to_remove:
                    print(f"🔄 SUMAS Y SALDOS: Removiendo mapeo anterior: {key} -> {mapping.selected_field}")
                    current_mapping[key] = None
            
            # Add new mapping
            current_mapping[mapping.column_name] = mapping.selected_field
            applied_mappings[mapping.column_name] = mapping.selected_field
            used_fields.add(mapping.selected_field)
            print(f" SUMAS Y SALDOS: Applied mapping: {mapping.column_name} -> {mapping.selected_field}")
        
        if validation_errors:
            error_detail = f"Validation errors: {'; '.join(validation_errors)}"
            print(f"SUMAS Y SALDOS: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
        if not applied_mappings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid mappings provided"
            )
        
        #  CRÍTICO: Limpiar mapeos None ANTES de procesar
        current_mapping = {k: v for k, v in current_mapping.items() if v is not None}
        print(f"SUMAS Y SALDOS: Cleaned mapping (removed None values): {current_mapping}")
        
        #  IMPORTANTE: Remover sufijo -ss del execution_id para Azure Storage
        # El execution_id viene como "xxx-ss" pero Azure necesita solo "xxx"
        clean_execution_id = execution_id.replace('-ss', '')
        print(f"SUMAS Y SALDOS: Using execution_id for storage: {clean_execution_id}")
        
        # Process Sumas y Saldos with updated mapping
        result = await sumas_saldos_service.process_sumas_saldos(
            execution.sumas_saldos_raw_path,
            current_mapping,
            clean_execution_id  #  Usar ID limpio
        )
        
        # Update execution with new mapping and results
        execution_service.update_execution(
            execution_id,
            sumas_saldos_mapping=current_mapping,
            sumas_saldos_csv_path=result["csv_path"],
            sumas_saldos_stats=result["stats"],
            sumas_saldos_status="completed",
            sumas_saldos_manual_mapping_required=False,
            sumas_saldos_unmapped_count=0
        )
        
        print(f"SUMAS Y SALDOS: Successfully applied {len(applied_mappings)} mappings")
        
        return ApplySumasSaldosMappingResponse(
            execution_id=execution_id,
            applied_mappings=len(applied_mappings),
            updated_mapping=current_mapping,  #  Ya limpio, sin None
            csv_path=result["csv_path"],
            stats=result["stats"],
            message=f"Successfully applied {len(applied_mappings)} manual mappings and regenerated Sumas y Saldos CSV"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"SUMAS Y SALDOS: Error applying manual mappings: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying manual Sumas y Saldos mappings: {str(e)}"
        )