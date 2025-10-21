# routes/manual_mapping.py - FIXED WITH FORCE_OVERRIDE SUPPORT
"""
Manual mapping routes for unmapped fields - WITH RE-MAPPING SUPPORT
"""
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import pandas as pd
import tempfile
import os

from services.execution_service import get_execution_service
from services.mapeo_service import get_mapeo_service
from services.storage.azure_storage_service import get_azure_storage_service
from config.settings import get_settings
from utils.serialization import safe_json_response

router = APIRouter(prefix="/smau-proto/api/import", tags=["mapeo"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class FieldSuggestion(BaseModel):
    """Individual field suggestion"""
    field: str
    reason: str
    confidence: float

class UnmappedField(BaseModel):
    """Unmapped field information"""
    column_name: str
    sample_data: List[str]
    data_type: str
    suggestions: List[FieldSuggestion]
    total_values: int
    non_null_values: int
    unique_values: int

class MappingDecision(BaseModel):
    """User's mapping decision - WITH FORCE_OVERRIDE SUPPORT"""
    column_name: str
    selected_field: str
    confidence: float = 0.8
    force_override: bool = False  #  NUEVO: Permite re-mapeo

class ManualMappingRequest(BaseModel):
    """Request to apply manual mappings"""
    mappings: List[MappingDecision]

class ManualMappingResponse(BaseModel):
    """Response with unmapped fields"""
    execution_id: str
    unmapped_fields: List[UnmappedField]
    available_standard_fields: List[str]
    message: str

class ApplyMappingResponse(BaseModel):
    """Response after applying mappings"""
    execution_id: str
    applied_mappings: int
    updated_decisions: Dict[str, str]
    regenerated_files: Dict[str, Optional[str]]
    message: str

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/mapeo/{execution_id}/unmapped", response_model=ManualMappingResponse)
async def get_unmapped_fields(execution_id: str):
    """Get fields that couldn't be mapped automatically for manual mapping"""
    execution_service = get_execution_service()
    mapeo_service = get_mapeo_service()
    
    try:
        print(f"BUGS - MANUAL MAPPING: Getting unmapped fields for execution {execution_id}")
        
        execution = execution_service.get_execution(execution_id)
        
        # Check if mapeo has been completed
        if not hasattr(execution, 'mapeo_results') or not execution.mapeo_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mapeo not completed yet"
            )
        
        if not execution.mapeo_results.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mapeo failed, cannot get unmapped fields"
            )
        
        print(f"BUGS - MANUAL MAPPING: Mapeo results found, checking for unmapped fields")
        
        # Get the source file for analysis
        source_file = execution.result_path
        if not source_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No result file available for analysis"
            )
        
        print(f"BUGS - MANUAL MAPPING: Analyzing unmapped fields from file: {source_file}")
        
        # Get unmapped fields analysis
        analysis = mapeo_service.get_unmapped_fields_analysis(source_file, execution.mapeo_results)
        
        if 'error' in analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error analyzing unmapped fields: {analysis['error']}"
            )
        
        # Convert analysis to proper Pydantic models
        unmapped_fields_list = []
        for field_data in analysis['unmapped_fields']:
            # Convert suggestions to proper FieldSuggestion models
            suggestions = []
            for suggestion in field_data.get('suggestions', []):
                if isinstance(suggestion, dict) and 'field' in suggestion:
                    suggestions.append(FieldSuggestion(
                        field=suggestion['field'],
                        reason=suggestion.get('reason', 'unknown'),
                        confidence=suggestion.get('confidence', 0.5)
                    ))
            
            unmapped_fields_list.append(UnmappedField(
                column_name=field_data['column_name'],
                sample_data=field_data['sample_data'],
                data_type=field_data['data_type'],
                suggestions=suggestions,
                total_values=field_data['total_values'],
                non_null_values=field_data['non_null_values'],
                unique_values=field_data['unique_values']
            ))
        
        response_message = f"Found {analysis['total_unmapped']} unmapped fields"
        if analysis['total_unmapped'] == 0:
            response_message = "All fields have been mapped successfully"
        
        print(f"BUGS - MANUAL MAPPING: {response_message}")
        
        return ManualMappingResponse(
            execution_id=execution_id,
            unmapped_fields=unmapped_fields_list,
            available_standard_fields=analysis['available_standard_fields'],
            message=response_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"BUGS - MANUAL MAPPING: Error in get_unmapped_fields: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing unmapped fields: {str(e)}"
        )

@router.post("/mapeo/{execution_id}/apply-manual-mapping", response_model=ApplyMappingResponse)
async def apply_manual_mapping(execution_id: str, mapping_request: ManualMappingRequest):
    """Apply manual mappings selected by user - WITH FORCE_OVERRIDE SUPPORT"""
    execution_service = get_execution_service()
    
    try:
        print(f"BUGS - MANUAL MAPPING: Applying manual mappings for execution {execution_id}")
        print(f"BUGS - MANUAL MAPPING: Received {len(mapping_request.mappings)} mappings")
        
        execution = execution_service.get_execution(execution_id)
        
        if not hasattr(execution, 'mapeo_results') or not execution.mapeo_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mapeo not completed yet"
            )
        
        # Get current user decisions
        current_decisions = execution.mapeo_results.get('user_decisions', {}).copy()
        
        # Validate and apply new mappings
        applied_mappings = {}
        validation_errors = []
        
        #  CAMBIO CRÍTICO: Construir used_fields EXCLUYENDO los que se van a re-mapear
        columns_to_remap = {m.column_name for m in mapping_request.mappings if m.force_override}
        print(f"BUGS - MANUAL MAPPING: Columns to remap (force_override=True): {columns_to_remap}")
        
        # Get already used fields, pero excluir los que vamos a re-mapear
        used_fields = set()
        for col_name, decision in current_decisions.items():
            # Si esta columna NO va a ser re-mapeada, incluir su field_type en used_fields
            if col_name not in columns_to_remap:
                used_fields.add(decision['field_type'])
        
        print(f"BUGS - MANUAL MAPPING: Used fields (excluding columns to remap): {used_fields}")
        
        # Validate and apply new mappings
        for mapping in mapping_request.mappings:
            print(f"BUGS - MANUAL MAPPING: Processing mapping: {mapping.column_name} -> {mapping.selected_field} (force_override={mapping.force_override})")
            
            #  Si force_override=True, permitir el re-mapeo sin validar duplicados
            if not mapping.force_override and mapping.selected_field in used_fields:
                error_msg = f"Field '{mapping.selected_field}' is already mapped to another column"
                print(f"BUGS - MANUAL MAPPING: Validation error: {error_msg}")
                validation_errors.append(error_msg)
                continue
            
            #  Si estamos re-mapeando, primero eliminar el mapeo anterior de ese selected_field
            if mapping.force_override:
                # Buscar y eliminar cualquier decisión previa que use este selected_field
                keys_to_remove = [
                    col for col, dec in current_decisions.items() 
                    if dec['field_type'] == mapping.selected_field and col != mapping.column_name
                ]
                for key in keys_to_remove:
                    print(f"🔄 MANUAL MAPPING: Removiendo mapeo anterior: {key} -> {mapping.selected_field}")
                    del current_decisions[key]
            
            # Add new mapping decision
            current_decisions[mapping.column_name] = {
                'field_type': mapping.selected_field,
                'confidence': mapping.confidence,
                'decision_type': 'manual_mapping',
                'resolution_type': 'manual_selection'
            }
            
            applied_mappings[mapping.column_name] = mapping.selected_field
            used_fields.add(mapping.selected_field)
            print(f" MANUAL MAPPING: Applied mapping: {mapping.column_name} -> {mapping.selected_field}")
        
        if validation_errors:
            error_detail = f"Validation errors: {'; '.join(validation_errors)}"
            print(f"BUGS - MANUAL MAPPING: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
        # Update mapeo results with new decisions
        updated_mapeo_results = execution.mapeo_results.copy()
        updated_mapeo_results['user_decisions'] = current_decisions
        
        # Update statistics
        mapeo_stats = updated_mapeo_results.get('mapeo_stats', {})
        mapeo_stats['manual_mappings'] = mapeo_stats.get('manual_mappings', 0) + len(applied_mappings)
        mapeo_stats['columns_processed'] = mapeo_stats.get('columns_processed', 0) + len(applied_mappings)
        updated_mapeo_results['mapeo_stats'] = mapeo_stats
        
        # Regenerate CSV files with new mappings
        regenerated_files = await _regenerate_mapeo_files(execution, current_decisions)
        
        # Update mapeo results with new file paths
        if regenerated_files.get('output_file'):
            updated_mapeo_results['output_file'] = regenerated_files['output_file']
        if regenerated_files.get('report_file'):
            updated_mapeo_results['report_file'] = regenerated_files['report_file']
        
        # Update execution
        execution_service.update_execution(
            execution_id,
            mapeo_results=updated_mapeo_results,
            manual_mapping_required=False,  # Manual mapping completed
            unmapped_fields_count=0
        )
        
        print(f"BUGS - MANUAL MAPPING: Applied {len(applied_mappings)} manual mappings successfully")
        
        return ApplyMappingResponse(
            execution_id=execution_id,
            applied_mappings=len(applied_mappings),
            updated_decisions=applied_mappings,
            regenerated_files=regenerated_files,
            message=f"Successfully applied {len(applied_mappings)} manual mappings and regenerated output files"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"BUGS - MANUAL MAPPING: Error applying manual mappings: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying manual mappings: {str(e)}"
        )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def _regenerate_mapeo_files(execution, user_decisions: Dict) -> Dict[str, Optional[str]]:
    """Regenerate mapeo CSV files with updated mappings"""
    try:
        settings = get_settings()
        azure_service = get_azure_storage_service() if settings.use_azure_storage else None
        
        # Get source file
        source_file = execution.result_path
        if not source_file:
            raise RuntimeError("No source file available for regeneration")
        
        # Download source file if it's in Azure
        local_source_file = source_file
        temp_file_created = False
        
        if source_file.startswith("azure://"):
            if not azure_service:
                raise RuntimeError("Azure Storage not configured")
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                local_source_file = temp_file.name
                temp_file_created = True
            
            #  CORREGIDO: usar download_file en lugar de download_file_to_path
            azure_service.download_file(source_file, local_source_file)
            print(f"BUGS - MANUAL MAPPING: Downloaded source file from Azure to: {local_source_file}")
        
        try:
            # Read source data
            df = pd.read_csv(local_source_file)
            
            # Import CSVTransformer
            from procesos_mapeo.csv_transformer import CSVTransformer
            
            # Create transformer instance
            transformer = CSVTransformer(
                output_prefix="manual_mapeo",
                apply_numeric_processing=True
            )
            
            # Generate single CSV file with updated mappings
            csv_result = transformer.create_single_transformed_csv(
                df, 
                user_decisions,
                suffix="manual_mapped",
                execution_id=execution.id
            )
            
            if not csv_result.get('success'):
                raise RuntimeError(f"Failed to regenerate file: {csv_result.get('error')}")
            
            #  NUEVO: Subir archivo a Azure Storage
            output_file_azure = None
            if azure_service and csv_result.get('output_file'):
                local_output_file = csv_result['output_file']
                
                print(f"BUGS - MANUAL MAPPING: Checking output file: {local_output_file}")
                print(f"BUGS - MANUAL MAPPING: File exists: {os.path.exists(local_output_file)}")
                
                if os.path.exists(local_output_file):
                    print(f"BUGS - MANUAL MAPPING: File size: {os.path.getsize(local_output_file)} bytes")
                    print(f"BUGS - MANUAL MAPPING: Uploading output file to Azure...")
                    
                    try:
                        # Upload with Je type (Journal Entries)
                        output_file_azure = azure_service.upload_file_chunked(
                            local_output_file,
                            container_type="mapeos",
                            execution_id=execution.id,
                            file_type="Je",
                            stage="mapeo",
                            description="manual_mapped"
                        )
                        
                        print(f"BUGS - MANUAL MAPPING:  Uploaded to Azure: {output_file_azure}")
                    except Exception as upload_error:
                        print(f"BUGS - MANUAL MAPPING: ❌ Error uploading to Azure: {upload_error}")
                        import traceback
                        traceback.print_exc()
                    
                    # Cleanup local file after upload
                    try:
                        os.remove(local_output_file)
                        print(f"BUGS - MANUAL MAPPING: Cleaned up local output file: {local_output_file}")
                    except Exception as e:
                        print(f"BUGS - MANUAL MAPPING: Warning - could not clean up local file: {e}")
                else:
                    print(f"BUGS - MANUAL MAPPING: ⚠️ Output file does not exist: {local_output_file}")
            else:
                if not azure_service:
                    print(f"BUGS - MANUAL MAPPING: ⚠️ Azure service not configured")
                if not csv_result.get('output_file'):
                    print(f"BUGS - MANUAL MAPPING: ⚠️ No output_file in csv_result: {csv_result}")
            
            # Generate report
            report_file_azure = None
            report_file = await _generate_updated_report(execution, user_decisions, csv_result)
            
            #  NUEVO: Subir reporte a Azure Storage
            if azure_service and report_file and os.path.exists(report_file):
                print(f"BUGS - MANUAL MAPPING: Uploading report to Azure: {report_file}")
                
                with open(report_file, 'rb') as f:
                    report_data = f.read()
                
                report_file_azure = azure_service.upload_from_memory(
                    report_data,
                    "manual_mapping_report.txt",
                    container_type="mapeos",
                    execution_id=execution.id,
                    file_type="Je",
                    stage="mapeo",
                    description="report"
                )
                
                print(f"BUGS - MANUAL MAPPING: Uploaded report to Azure: {report_file_azure}")
                
                # Cleanup local report after upload
                try:
                    os.remove(report_file)
                    print(f"BUGS - MANUAL MAPPING: Cleaned up local report file: {report_file}")
                except Exception as e:
                    print(f"BUGS - MANUAL MAPPING: Warning - could not clean up report: {e}")
            
            regenerated_files = {
                'output_file': output_file_azure or csv_result.get('output_file'),
                'report_file': report_file_azure
            }
            
            print(f"BUGS - MANUAL MAPPING: Regenerated files: {regenerated_files}")
            return regenerated_files
            
        except Exception as e:
            print(f"BUGS - MANUAL MAPPING: Error during file regeneration: {e}")
            import traceback
            traceback.print_exc()
            return {
                'header_file': None,
                'detail_file': None,
                'report_file': None
            }
            
        finally:
            # Clean up temporary source file
            if temp_file_created and os.path.exists(local_source_file):
                try:
                    os.remove(local_source_file)
                    print(f"BUGS - MANUAL MAPPING: Cleaned up temp source file: {local_source_file}")
                except Exception as e:
                    print(f"BUGS - MANUAL MAPPING: Warning - could not clean up temp file: {e}")
        
    except Exception as e:
        print(f"BUGS - MANUAL MAPPING: Error regenerating files: {e}")
        return {
            'header_file': None,
            'detail_file': None,
            'report_file': None
        }

async def _generate_updated_report(execution, user_decisions: Dict, csv_result: Dict) -> Optional[str]:
    """Generate updated report with manual mappings"""
    try:
        from datetime import datetime
        
        settings = get_settings()
        
        # Calculate statistics
        manual_mappings = sum(1 for d in user_decisions.values() if d.get('decision_type') == 'manual_mapping')
        automatic_mappings = len(user_decisions) - manual_mappings
        
        # Generate report content
        report_content = f"""MANUAL MAPPING COMPLETION REPORT
{'=' * 50}

Execution ID: {execution.id}
File: {execution.file_name}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MAPPING STATISTICS:
{'-' * 20}
Total Mappings: {len(user_decisions)}
Automatic Mappings: {automatic_mappings}
Manual Mappings: {manual_mappings}

FINAL FIELD MAPPINGS:
{'-' * 20}"""

        for column, decision in user_decisions.items():
            mapping_type = "MANUAL" if decision.get('decision_type') == 'manual_mapping' else "AUTO"
            confidence = decision.get('confidence', 0.0)
            report_content += f"\n{column} -> {decision['field_type']} ({mapping_type}, {confidence:.3f})"

        report_content += f"""

OUTPUT FILE GENERATED:
{'-' * 23}
Output CSV: {csv_result.get('output_file', 'Not generated')}

PROCESS COMPLETED SUCCESSFULLY
Manual mapping process completed. All unmapped fields have been resolved.
"""

        # Save report to temporary file
        report_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
        report_file.write(report_content)
        report_file.close()
        
        return report_file.name
        
    except Exception as e:
        print(f"BUGS - MANUAL MAPPING: Error generating report: {e}")
        return None