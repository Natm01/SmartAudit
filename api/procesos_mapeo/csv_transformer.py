# procesos_mapeo/csv_transformer.py
import pandas as pd
import tempfile
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from procesos_mapeo.accounting_data_processor import AccountingDataProcessor

logger = logging.getLogger(__name__)

class CSVTransformer:
    """Clean CSV transformer working only with local files"""
    
    def __init__(self, output_prefix: str = "transformed", sort_by_journal_id: bool = True,
                 apply_numeric_processing: bool = True):
        self.output_prefix = output_prefix
        self.sort_by_journal_id = sort_by_journal_id
        self.apply_numeric_processing = apply_numeric_processing
        
        self.accounting_processor = AccountingDataProcessor()
        
        self.transformation_stats = {
            'original_columns': 0,
            'transformed_columns': 0,
            'header_columns': 0,
            'detail_columns': 0,
            'rows_processed': 0,
            'numeric_processing_applied': False,
            'numeric_fields_processed': 0,
            'duplicates_removed': 0
        }
    
    def _ensure_all_columns(self, df: pd.DataFrame, required_fields: List[str]) -> pd.DataFrame:
        """Garantiza que todas las columnas requeridas existan, creando vacías si es necesario"""
        result_df = df.copy()
        
        for col in required_fields:
            if col not in result_df.columns:
                result_df[col] = ""
            elif col == 'debit_credit_indicator' and result_df[col].isna().all():
                # Si debit_credit_indicator existe pero está completamente vacío,
                # intentar crearlo desde amount si existe
                if 'amount' in result_df.columns:
                    logger.info(f"Regenerating empty debit_credit_indicator from amount")
                    result_df[col] = ''
                    mask_positive = result_df['amount'] > 0
                    mask_negative = result_df['amount'] < 0
                    result_df.loc[mask_positive, col] = 'D'
                    result_df.loc[mask_negative, col] = 'H'
        
        # Retornar DataFrame con columnas en el orden especificado
        return result_df[required_fields]
    
    def create_header_detail_csvs(self, df: pd.DataFrame, user_decisions: Dict, 
                                 standard_fields: List[str]) -> Dict[str, Any]:
        """Creates separate header and detail CSV files with integrated numeric processing"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self.transformation_stats['original_columns'] = len(df.columns)
            self.transformation_stats['rows_processed'] = len(df)
            
            transformed_df = df.copy()
            column_mapping = {}
            
            for column_name, decision in user_decisions.items():
                standard_field = decision['field_type']
                column_mapping[column_name] = standard_field
            
            transformed_df = transformed_df.rename(columns=column_mapping)
            
            if self.apply_numeric_processing:
                transformed_df, numeric_stats = self._apply_numeric_processing(transformed_df)
                self.transformation_stats['numeric_processing_applied'] = True
                self.transformation_stats['numeric_fields_processed'] = numeric_stats.get('fields_cleaned', 0)
            
            transformed_df = self.accounting_processor.separate_datetime_fields(transformed_df)
            
            if self.sort_by_journal_id and 'journal_entry_id' in transformed_df.columns:
                try:
                    transformed_df = transformed_df.sort_values('journal_entry_id', ascending=True)
                except TypeError:
                    transformed_df['journal_entry_id'] = transformed_df['journal_entry_id'].astype(str)
                    transformed_df = transformed_df.sort_values('journal_entry_id', ascending=True)
            
            # Definiciones completas de campos según staging
            header_field_definitions = [
                'journal_entry_id', 'journal_id', 'entry_date', 'entry_time',
                'posting_date', 'reversal_date', 'effective_date', 'description',
                'reference_number', 'source', 'entry_type', 'recurring_entry',
                'manual_entry', 'adjustment_entry', 'prepared_by', 'approved_by',
                'approval_date', 'entry_status', 'total_debit_amount', 'total_credit_amount',
                'line_count', 'fiscal_year', 'period_number', 'user_defined_01', 
                'user_defined_02', 'user_defined_03'
            ]
            
            detail_field_definitions = [
                'journal_entry_id', 'line_number', 'gl_account_number', 'amount',
                'debit_credit_indicator', 'business_unit', 'cost_center', 'department',
                'project_code', 'location', 'line_description', 'reference_number',
                'customer_id', 'vendor_id', 'product_id', 'user_defined_01',
                'user_defined_02', 'user_defined_03'
            ]
            
            # CAMBIO CLAVE: Usar _ensure_all_columns para garantizar todas las columnas
            header_df = self._ensure_all_columns(transformed_df, header_field_definitions)
            detail_df = self._ensure_all_columns(transformed_df, detail_field_definitions)
            
            # Usar las definiciones completas como columnas disponibles
            available_header_fields = header_field_definitions.copy()
            available_detail_fields = detail_field_definitions.copy()
            
            header_file = self._create_header_csv(header_df, available_header_fields, timestamp)
            detail_file = self._create_detail_csv(detail_df, available_detail_fields, timestamp)
            
            self.transformation_stats['transformed_columns'] = len(column_mapping)
            self.transformation_stats['header_columns'] = len(available_header_fields)
            self.transformation_stats['detail_columns'] = len(available_detail_fields)
            
            result = {
                'success': True,
                'header_file': header_file,
                'detail_file': detail_file,
                'header_columns': available_header_fields,
                'detail_columns': available_detail_fields,
                'transformation_stats': self.transformation_stats,
                'total_standard_fields_mapped': len(user_decisions),
                'unmapped_standard_fields': [
                    f for f in standard_fields 
                    if f not in [d['field_type'] for d in user_decisions.values()]
                ],
                'numeric_processing_stats': getattr(self, '_last_numeric_stats', {})
            }
            
            self._show_transformation_summary(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in CSV transformation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_header_csv(self, df: pd.DataFrame, header_fields: List[str], timestamp: str) -> Optional[str]:
        """Creates header CSV file with deduplication"""
        if not header_fields:
            return None
        
        # El DataFrame ya viene con todas las columnas desde _ensure_all_columns
        header_df = df.copy()
        
        if 'journal_entry_id' in header_fields and 'journal_entry_id' in df.columns:
            original_count = len(header_df)
            
            # Deduplicar por journal_entry_id, conservando el primer registro
            header_df = header_df.drop_duplicates(subset=['journal_entry_id'], keep='first')
            
            deduplicated_count = len(header_df)
            duplicates_removed = original_count - deduplicated_count
            self.transformation_stats['duplicates_removed'] = duplicates_removed
            
            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed:,} duplicate journal_entry_id records")
                logger.info(f"Unique header records: {deduplicated_count:,}")
            
            if self.sort_by_journal_id:
                try:
                    header_df = header_df.sort_values('journal_entry_id', ascending=True)
                except TypeError:
                    header_df['journal_entry_id'] = header_df['journal_entry_id'].astype(str)
                    header_df = header_df.sort_values('journal_entry_id', ascending=True)
        
        header_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name
        header_df.to_csv(header_file, index=False, encoding='utf-8')
        
        logger.info(f"Header CSV created: {header_file} ({len(header_df):,} records)")
        return header_file
    
    def _create_detail_csv(self, df: pd.DataFrame, detail_fields: List[str], timestamp: str) -> Optional[str]:
        """Creates detail CSV file maintaining all records"""
        if not detail_fields:
            return None
        
        # El DataFrame ya viene con todas las columnas desde _ensure_all_columns
        detail_df = df.copy()
        
        if self.sort_by_journal_id and 'journal_entry_id' in detail_df.columns:
            try:
                detail_df = detail_df.sort_values('journal_entry_id', ascending=True)
            except TypeError:
                detail_df['journal_entry_id'] = detail_df['journal_entry_id'].astype(str)
                detail_df = detail_df.sort_values('journal_entry_id', ascending=True)
        
        detail_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name
        detail_df.to_csv(detail_file, index=False, encoding='utf-8')
        
        logger.info(f"Detail CSV created: {detail_file} ({len(detail_df):,} records)")
        return detail_file
    
    def _apply_numeric_processing(self, df: pd.DataFrame):
        """Applies numeric processing using AccountingDataProcessor"""
        potential_numeric_fields = [
            'amount', 'debit_amount', 'credit_amount', 'line_number',
            'fiscal_year', 'period_number', 'gl_account_number'
        ]
        
        available_numeric_fields = [field for field in potential_numeric_fields 
                                  if field in df.columns]
        
        if not available_numeric_fields:
            return df, {}
        
        processed_df, processing_stats = self.accounting_processor.process_numeric_fields_and_calculate_amounts(df)
        
        self._last_numeric_stats = processing_stats
        
        return processed_df, processing_stats
    
    def _show_transformation_summary(self, result: Dict[str, Any]):
        """Shows transformation summary with numeric statistics"""
        stats = result['transformation_stats']
        
        if stats['numeric_processing_applied']:
            numeric_stats = result.get('numeric_processing_stats', {})
        
        files_created = 0
        if result.get('header_file'):
            files_created += 1
        if result.get('detail_file'):
            files_created += 1
        
        logger.info(f"Transformation completed: {files_created} files created")
    
    def create_single_transformed_csv(self, df: pd.DataFrame, user_decisions: Dict, 
                                    suffix: str = "transformed", execution_id: str = None) -> Dict[str, Any]:
        """Creates a single transformed CSV with numeric cleaning and type transformations"""
        try:
            # 1. Aplicar mapeo de columnas
            column_mapping = {col: decision['field_type'] for col, decision in user_decisions.items()}
            transformed_df = df.rename(columns=column_mapping)
            
            # 2. Aplicar procesamiento numérico (limpieza de formatos)
            if self.apply_numeric_processing:
                transformed_df, numeric_stats = self._apply_numeric_processing(transformed_df)
                numeric_processing_applied = True
            else:
                numeric_stats = {}
                numeric_processing_applied = False
            
            # 3. NUEVO: Aplicar transformaciones de tipo según JSON
            try:
                from procesos_mapeo.type_transformer import get_type_transformer
                type_transformer = get_type_transformer()
                transformed_df = type_transformer.transform_dataframe(transformed_df)
                type_transformations_applied = True
                logger.info(" Type transformations applied successfully")
            except Exception as e:
                logger.warning(f" Type transformations failed: {e}")
                type_transformations_applied = False
            
            # 4. Ordenar por journal_entry_id si existe
            if self.sort_by_journal_id and 'journal_entry_id' in transformed_df.columns:
                transformed_df = transformed_df.sort_values('journal_entry_id').reset_index(drop=True)
            
            # 5. Guardar a CSV
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name
            transformed_df.to_csv(output_file, index=False, encoding='utf-8')
            
            result = {
                'success': True,
                'output_file': output_file,
                'rows': len(transformed_df),
                'columns': len(transformed_df.columns),
                'mapped_fields': len(user_decisions),
                'numeric_processing_applied': numeric_processing_applied,
                'numeric_processing_stats': numeric_stats,
                'type_transformations_applied': type_transformations_applied  #  NUEVO
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating single transformed CSV: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}