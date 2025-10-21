# services/sumas_saldos_service.py
"""
Sumas y Saldos Service - Complete logic from balance_sumarias.py
"""
import pandas as pd
import re
import unicodedata
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter

from services.storage.azure_storage_service import get_azure_storage_service
from services.storage.temp_file_manager import get_temp_file_manager
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Sumas y Saldos columns for staging
SUMAS_SALDOS_COLUMNS = [
    'gl_account_number',
    'reporting_account',
    'fiscal_year',
    'period_number',
    'period_ending_balance',
    'period_activity_debit',
    'period_activity_credit',
    'period_beginning_balance',
    'period_ending_date',
    'business_unit',
    'cost_center',
    'department',
    'user_defined_01',
    'user_defined_02',
    'user_defined_03'
]

class SumasSaldosService:
    """Service for processing Sumas y Saldos (Trial Balance) files"""
    
    def __init__(self):
        self.settings = get_settings()
        self.azure_service = get_azure_storage_service() if self.settings.use_azure_storage else None
        self.temp_manager = get_temp_file_manager()
    
    # ==========================================
    # Utility Functions from balance_sumarias.py
    # ==========================================
    
    @staticmethod
    def clean_number(value):
        """Clean and convert number values"""
        if pd.isna(value):
            return None
        
        value = str(value).strip()
        is_negative = False
        
        # Negative numbers in parentheses
        if value.startswith("(") and value.endswith(")"):
            is_negative = True
            value = value[1:-1]
        
        # Remove spaces and strange characters
        value = value.replace(" ", "").replace("\u200b", "")
        
        # Detect thousand and decimal separators
        last_comma = value.rfind(",")
        last_dot = value.rfind(".")
        
        if last_comma > last_dot:
            # Comma as decimal, dot as thousands
            value = value.replace(".", "").replace(",", ".")
        elif last_dot > last_comma:
            # Dot as decimal, comma as thousands
            value = value.replace(",", "")
        
        try:
            num = float(value)
            return -num if is_negative else num
        except ValueError:
            return None
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison"""
        text = str(text).strip().upper()
        text = "".join(c for c in unicodedata.normalize("NFD", text) 
                      if unicodedata.category(c) != "Mn")
        text = re.sub(r"\s+", " ", text)
        return text
    
    @staticmethod
    def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Find column containing all keywords"""
        normalized_cols = {SumasSaldosService.normalize_text(c): c for c in df.columns}
        for norm_name, orig_name in normalized_cols.items():
            if all(k in norm_name for k in keywords):
                return orig_name
        return None
    
    @staticmethod
    def detectar_fila_cabecera(file_path: str) -> int:
        """Detect header row in Excel file"""
        df_preview = pd.read_excel(file_path, header=None, nrows=20)
        for i, row in df_preview.iterrows():
            normalized = row.astype(str).apply(SumasSaldosService.normalize_text).tolist()
            if any("CUENTA" in c for c in normalized) and any("SALDO" in c for c in normalized):
                return i
        raise ValueError("No se encontró la fila de cabecera con columnas tipo 'CUENTA' y 'SALDO'")
    
    @staticmethod
    def clean_account_number(value):
        """Clean account number"""
        if pd.isna(value):
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        val_str = str(value).strip()
        if re.fullmatch(r"\d+\.0+", val_str):
            return str(int(float(val_str)))
        return val_str
    
    @staticmethod
    def _ensure_all_columns_sumas_saldos(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns exist"""
        for col in SUMAS_SALDOS_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[SUMAS_SALDOS_COLUMNS]
    
    # ==========================================
    # Main Service Methods
    # ==========================================
    
    async def detect_automatic_mapping(self, file_path: str) -> Dict[str, Any]:
        """
        Detect automatic mapping for Sumas y Saldos file.
        Returns suggested mapping and available columns.
        """
        try:
            logger.info(f"Detecting automatic mapping for Sumas y Saldos: {file_path}")
            
            # Download from Azure if needed
            if file_path.startswith("azure://") and self.azure_service:
                with self.temp_manager.get_local_file(file_path) as local_file:
                    return await self._detect_mapping_from_local(local_file)
            else:
                return await self._detect_mapping_from_local(file_path)
                
        except Exception as e:
            logger.error(f"Error detecting mapping: {e}")
            raise
    
    async def _detect_mapping_from_local(self, file_path: str) -> Dict[str, Any]:
        """Detect mapping from local file"""
        # Detect header row
        header_row = self.detectar_fila_cabecera(file_path)
        
        # Read Excel
        df = pd.read_excel(file_path, header=header_row)
        
        # Detect account columns (excluding those with "#")
        account_cols = [
            c for c in df.columns
            if any(k in self.normalize_text(c) for k in ["CUENTA", "CTA"])
            and "#" not in self.normalize_text(c)
        ]
        
        if len(account_cols) < 3:
            raise ValueError("No se encontraron suficientes columnas de cuenta (mÃ­nimo 3).")
        
        # Apply strict logic for gl_account and reporting_account
        if len(account_cols) == 3:
            gl_account_number_col = account_cols[2]
            reporting_account_col = None
        else:
            gl_account_number_col = account_cols[-2]
            reporting_account_col = account_cols[-1]
        
        # Find ending balance column
        col_ending_balance = self.find_column(df, ["SALDO", "FINAL"])
        if not col_ending_balance:
            raise ValueError("No se encontró la columna de saldo final (SALDO FINAL).")
        
        # Find historical balance columns (SALDO 31/12/20XX)
        saldo_cols = [c for c in df.columns if re.match(r"SALDO 31/12/20\d{2,4}", self.normalize_text(c))]
        oldest_col = None
        if saldo_cols:
            years = [(c, int(re.search(r"(20\d{2})", c).group(1))) for c in saldo_cols if re.search(r"(20\d{2})", c)]
            if years:
                oldest_col = min(years, key=lambda x: x[1])[0]
        
        # If no oldest_col, look for SALDO INICIAL
        beginning_col = oldest_col or self.find_column(df, ["SALDO", "INICIAL"])
        
        # Find debit and credit columns
        debit_col = self.find_column(df, ["DEBE"]) or self.find_column(df, ["DEBITO"])
        credit_col = self.find_column(df, ["HABER"]) or self.find_column(df, ["CREDITO"])
        
        # Build mapping result
        mapping = {
            "gl_account_number": gl_account_number_col,
            "reporting_account": reporting_account_col,
            "period_ending_balance": col_ending_balance,
            "period_beginning_balance": beginning_col,
            "period_activity_debit": debit_col,
            "period_activity_credit": credit_col
        }
        
        return {
            "mapping": mapping,
            "available_columns": list(df.columns),
            "header_row": header_row
        }
    
    async def process_sumas_saldos(
        self, 
        raw_file_path: str, 
        mapping: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Process Sumas y Saldos file with confirmed mapping.
        Returns processed file path and statistics.
        """
        try:
            logger.info(f"Processing Sumas y Saldos for execution: {execution_id}")
            
            # Download from Azure if needed
            if raw_file_path.startswith("azure://") and self.azure_service:
                with self.temp_manager.get_local_file(raw_file_path) as local_file:
                    return await self._process_from_local(local_file, mapping, execution_id)
            else:
                return await self._process_from_local(raw_file_path, mapping, execution_id)
                
        except Exception as e:
            logger.error(f"Error processing Sumas y Saldos: {e}")
            raise
    
    async def _process_from_local(
        self, 
        file_path: str, 
        mapping: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Process Sumas y Saldos from local file"""
        # Detect header row
        header_row = self.detectar_fila_cabecera(file_path)
        
        # Read Excel
        df = pd.read_excel(file_path, header=header_row)
        
        # Build result DataFrame
        result = pd.DataFrame()
        
        # Map columns according to configuration
        if mapping.get("gl_account_number"):
            result["gl_account_number"] = df[mapping["gl_account_number"]].apply(self.clean_account_number)
        
        if mapping.get("reporting_account"):
            result["reporting_account"] = df[mapping["reporting_account"]].apply(self.clean_account_number)
        else:
            result["reporting_account"] = ""
        
        if mapping.get("period_ending_balance"):
            result["period_ending_balance"] = df[mapping["period_ending_balance"]].apply(self.clean_number)
        
        if mapping.get("period_beginning_balance"):
            result["period_beginning_balance"] = df[mapping["period_beginning_balance"]].apply(self.clean_number)
        else:
            result["period_beginning_balance"] = None
        
        if mapping.get("period_activity_debit"):
            result["period_activity_debit"] = df[mapping["period_activity_debit"]].apply(self.clean_number)
        
        if mapping.get("period_activity_credit"):
            result["period_activity_credit"] = df[mapping["period_activity_credit"]].apply(self.clean_number)
        
        try:
            from procesos_mapeo.type_transformer import get_type_transformer
            type_transformer = get_type_transformer()
            result = type_transformer.transform_dataframe(result)
            logger.info(" Type transformations applied to Sumas y Saldos")
        except Exception as e:
            logger.warning(f"⚠️ Type transformations failed for Sumas y Saldos: {e}")

        # Ensure all columns
        result = self._ensure_all_columns_sumas_saldos(result)

        # Ensure all columns
        result = self._ensure_all_columns_sumas_saldos(result)
        
        # Save to CSV
        if self.settings.use_azure_storage:
            # Save to temp file then upload
            with self.temp_manager.create_temp_file('.csv') as temp_csv:
                result.to_csv(temp_csv, index=False, sep=",", float_format="%.2f")
                
                # Upload with Sys type
                csv_path = self.azure_service.upload_file_chunked(
                    temp_csv,
                    container_type="mapeos",
                    execution_id=execution_id,
                    file_type="Sys"
                )
        else:
            # Save locally
            output_dir = f"uploads/{execution_id}"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            csv_path = f"{output_dir}/{execution_id}_sumas_saldos.csv"
            result.to_csv(csv_path, index=False, sep=",", float_format="%.2f")
        
        # Calculate statistics
        stats = {
            "total_rows": len(result),
            "total_accounts": result["gl_account_number"].nunique(),
            "has_reporting_account": bool(mapping.get("reporting_account")),
            "has_beginning_balance": bool(mapping.get("period_beginning_balance")),
            "has_debit_credit": bool(mapping.get("period_activity_debit") or mapping.get("period_activity_credit")),
            "columns_mapped": sum(1 for v in mapping.values() if v)
        }
        
        logger.info(f"Sumas y Saldos processed: {stats['total_rows']} rows, {stats['total_accounts']} accounts")
        
        return {
            "csv_path": csv_path,
            "stats": stats
        }
    
    async def get_preview(self, csv_path: str, rows: int = 10) -> Dict[str, Any]:
        """Get preview of processed Sumas y Saldos"""
        try:
            # Download from Azure if needed
            if csv_path.startswith("azure://") and self.azure_service:
                with self.temp_manager.get_local_file(csv_path) as local_file:
                    return self._get_preview_from_local(local_file, rows)
            else:
                return self._get_preview_from_local(csv_path, rows)
                
        except Exception as e:
            logger.error(f"Error getting preview: {e}")
            raise
    
    def _get_preview_from_local(self, file_path: str, rows: int) -> Dict[str, Any]:
        """Get preview from local file"""
        # Read preview rows
        df_preview = pd.read_csv(file_path, nrows=rows)
        
        # Read full file for total count
        df_full = pd.read_csv(file_path)
        
        return {
            "data": df_preview.fillna("").to_dict(orient='records'),
            "columns": list(df_preview.columns),
            "total_rows": len(df_full)
        }
    
    async def get_unmapped_fields_analysis(
        self, 
        raw_file_path: str, 
        current_mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze unmapped fields in the Sumas y Saldos Excel.
        Returns fields that are not yet mapped with suggestions.
        """
        try:
            logger.info(f"Analyzing unmapped fields for Sumas y Saldos: {raw_file_path}")
            
            # Download from Azure if needed
            if raw_file_path.startswith("azure://") and self.azure_service:
                with self.temp_manager.get_local_file(raw_file_path) as local_file:
                    return self._analyze_unmapped_from_local(local_file, current_mapping)
            else:
                return self._analyze_unmapped_from_local(raw_file_path, current_mapping)
                
        except Exception as e:
            logger.error(f"Error analyzing unmapped fields: {e}")
            return {
                'unmapped_fields': {},
                'available_standard_fields': [],
                'total_unmapped': 0,
                'total_available_fields': 0,
                'error': str(e)
            }
    
    def _analyze_unmapped_from_local(
        self, 
        file_path: str, 
        current_mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze unmapped fields from local file"""
        # Detect header row
        header_row = self.detectar_fila_cabecera(file_path)
        
        # Read Excel
        df = pd.read_excel(file_path, header=header_row)
        
        # Get mapped columns
        mapped_columns = set(v for v in current_mapping.values() if v is not None)
        
        # Get all columns from the file
        all_columns = set(df.columns)
        
        # Find unmapped columns
        unmapped_columns = all_columns - mapped_columns
        
        # Analyze unmapped fields
        unmapped_fields = {}
        for col in unmapped_columns:
            col_data = df[col].dropna()
            
            # Get sample data (up to 5 non-null values)
            sample_data = col_data.head(5).astype(str).tolist()
            
            # Generate suggestions
            suggestions = self._generate_field_suggestions_for_column(
                col,
                sample_data,
                str(df[col].dtype),
                list(current_mapping.values())
            )
            
            unmapped_fields[col] = {
                'column_name': col,
                'sample_data': sample_data,
                'data_type': str(df[col].dtype),
                'suggestions': suggestions,
                'total_values': len(df[col]),
                'non_null_values': int(col_data.count()),
                'unique_values': int(col_data.nunique())
            }
        
        # Get available fields (not yet used)
        used_fields = set(v for v in current_mapping.values() if v is not None)
        available_fields = [f for f in SUMAS_SALDOS_COLUMNS if f not in used_fields]
        
        return {
            'unmapped_fields': unmapped_fields,
            'available_standard_fields': available_fields,
            'total_unmapped': len(unmapped_fields),
            'total_available_fields': len(available_fields)
        }
    
    def _generate_field_suggestions_for_column(
        self,
        column_name: str,
        sample_data: List[str],
        data_type: str,
        already_used_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate field suggestions based on column name and data"""
        suggestions = []
        
        # Normalize column name for comparison
        norm_col = self.normalize_text(column_name)
        
        # Available fields (not yet used)
        available_fields = [f for f in SUMAS_SALDOS_COLUMNS if f not in already_used_fields]
        
        # Suggestion rules for Sumas y Saldos
        suggestion_rules = {
            'fiscal_year': (['AÃ‘O', 'YEAR', 'EJERCICIO', 'FISCAL'], 'Contains year information'),
            'period_number': (['PERIODO', 'PERIOD', 'MES', 'MONTH'], 'Contains period/month number'),
            'period_ending_date': (['FECHA', 'DATE', 'CIERRE'], 'Contains date information'),
            'business_unit': (['UNIDAD', 'NEGOCIO', 'BUSINESS', 'UNIT', 'DIVISION'], 'Business unit identifier'),
            'cost_center': (['CENTRO', 'COSTE', 'COST', 'CENTER'], 'Cost center code'),
            'department': (['DEPARTAMENTO', 'DEPTO', 'DEPT', 'AREA'], 'Department information'),
            'user_defined_01': (['CAMPO1', 'FIELD1', 'AUX1', 'EXTRA1'], 'Custom field 1'),
            'user_defined_02': (['CAMPO2', 'FIELD2', 'AUX2', 'EXTRA2'], 'Custom field 2'),
            'user_defined_03': (['CAMPO3', 'FIELD3', 'AUX3', 'EXTRA3'], 'Custom field 3'),
        }
        
        # Check each rule
        for field_name, (keywords, reason) in suggestion_rules.items():
            if field_name not in available_fields:
                continue
                
            # Check if any keyword matches
            confidence = 0.0
            for keyword in keywords:
                if keyword in norm_col:
                    confidence = max(confidence, 0.7)
            
            if confidence > 0:
                suggestions.append({
                    'field': field_name,
                    'reason': reason,
                    'confidence': confidence
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # If no specific suggestions, offer generic user_defined fields
        if not suggestions and available_fields:
            for field in ['user_defined_01', 'user_defined_02', 'user_defined_03']:
                if field in available_fields:
                    suggestions.append({
                        'field': field,
                        'reason': 'Generic custom field',
                        'confidence': 0.3
                    })
                    break
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def get_original_preview(self, raw_file_path: str, rows: int = 10) -> Dict[str, Any]:
        """Get preview of ORIGINAL Excel file (antes del mapeo)"""
        try:
            # Download from Azure if needed
            if raw_file_path.startswith("azure://") and self.azure_service:
                with self.temp_manager.get_local_file(raw_file_path) as local_file:
                    return self._get_original_preview_from_local(local_file, rows)
            else:
                return self._get_original_preview_from_local(raw_file_path, rows)
                
        except Exception as e:
            logger.error(f"Error getting original preview: {e}")
            raise

    def _get_original_preview_from_local(self, file_path: str, rows: int) -> Dict[str, Any]:
        """Get preview from original Excel file"""
        # Detect header row
        header_row = self.detectar_fila_cabecera(file_path)
        
        # Read Excel with original column names
        df = pd.read_excel(file_path, header=header_row, nrows=rows)
        
        # Read full file for total count
        df_full = pd.read_excel(file_path, header=header_row)
        
        return {
            "data": df.fillna("").to_dict(orient='records'),
            "columns": list(df.columns),  # Columnas ORIGINALES del Excel
            "total_rows": len(df_full)
        }

# Singleton pattern
_sumas_saldos_service = None

def get_sumas_saldos_service() -> SumasSaldosService:
    """Get Sumas y Saldos service singleton"""
    global _sumas_saldos_service
    if _sumas_saldos_service is None:
        _sumas_saldos_service = SumasSaldosService()
    return _sumas_saldos_service