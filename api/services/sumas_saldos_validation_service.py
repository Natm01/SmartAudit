# services/sumas_saldos_validation_service.py
"""
Servicio de validación para Sumas y Saldos
Solo ejecuta Fase 1 (validaciones de formato) adaptado para las columnas específicas
"""
import pandas as pd
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SumasSaldosValidationService:
    """
    Servicio para validar archivos de Sumas y Saldos DESPUÉS del mapeo.
    Solo ejecuta Fase 1 con las columnas específicas de sumas y saldos.
    """
    
    def __init__(self):
        self.validation_stats = {
            'validations_performed': 0,
            'total_rows_validated': 0,
            'total_issues_found': 0
        }
    
    def run_validation_fase_1(self, csv_path: str) -> Dict[str, Any]:
        """
        Ejecuta solo la Fase 1 de validaciones sobre el archivo CSV de Sumas y Saldos.
        
        Args:
            csv_path: Ruta al archivo de sumas y saldos procesado
        
        Returns:
            Dict con resultados de la fase 1
        """
        try:
            # Leer CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded Sumas y Saldos CSV: {len(df)} rows, {len(df.columns)} columns")
            
            self.validation_stats['validations_performed'] += 1
            self.validation_stats['total_rows_validated'] += len(df)
            
            results = {
                'file_info': {
                    'path': csv_path,
                    'rows': len(df),
                    'columns': list(df.columns)
                },
                'validation_timestamp': datetime.now().isoformat(),
                'file_type': 'sumas_saldos',
                'fase_1_formato': self.validate_format_sumas_saldos(df),
                'summary': {}
            }
            
            # Calcular resumen
            results['summary'] = self._calculate_summary(results)
            
            # Contar issues totales
            total_issues = self._count_total_issues(results)
            self.validation_stats['total_issues_found'] += total_issues
            
            return results
            
        except Exception as e:
            logger.error(f"Error running validations: {e}", exc_info=True)
            return {
                'error': str(e),
                'validation_timestamp': datetime.now().isoformat(),
                'file_type': 'sumas_saldos',
                'fase_1_formato': {'error': str(e)},
                'summary': {
                    'total_phases': 1,
                    'completed_phases': 0,
                    'all_passed': False,
                    'has_errors': True
                }
            }
    
    def validate_format_sumas_saldos(self, df: pd.DataFrame) -> Dict:
        """
        Valida formato de campos específicos de Sumas y Saldos.
        Solo valida las columnas que existen y son relevantes.
        """
        results = {
            'phase_name': 'Validaciones de Formato - Sumas y Saldos',
            'description': 'Verifica formato de campos en archivo de sumas y saldos',
            'validations': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }
        
        # 1. Validar gl_account_number (obligatorio)
        if 'gl_account_number' in df.columns:
            gl_validation = self._validate_gl_account_number(df)
            results['validations']['gl_account_number'] = gl_validation
            results['summary']['total_checks'] += 1
            if gl_validation['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # 2. Validar period_beginning_balance (si existe)
        if 'period_beginning_balance' in df.columns:
            beginning_validation = self._validate_numeric_field(
                df, 
                'period_beginning_balance',
                'Saldo Inicial'
            )
            results['validations']['period_beginning_balance'] = beginning_validation
            results['summary']['total_checks'] += 1
            if beginning_validation['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # 3. Validar period_ending_balance (obligatorio)
        if 'period_ending_balance' in df.columns:
            ending_validation = self._validate_numeric_field(
                df, 
                'period_ending_balance',
                'Saldo Final'
            )
            results['validations']['period_ending_balance'] = ending_validation
            results['summary']['total_checks'] += 1
            if ending_validation['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # 4. Validar period_activity_debit (si existe)
        if 'period_activity_debit' in df.columns:
            debit_validation = self._validate_numeric_field(
                df, 
                'period_activity_debit',
                'Debe'
            )
            results['validations']['period_activity_debit'] = debit_validation
            results['summary']['total_checks'] += 1
            if debit_validation['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # 5. Validar period_activity_credit (si existe)
        if 'period_activity_credit' in df.columns:
            credit_validation = self._validate_numeric_field(
                df, 
                'period_activity_credit',
                'Haber'
            )
            results['validations']['period_activity_credit'] = credit_validation
            results['summary']['total_checks'] += 1
            if credit_validation['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # Determinar si la fase es válida
        results['is_phase_valid'] = results['summary']['failed_checks'] == 0
        
        return results
    
    def _validate_gl_account_number(self, df: pd.DataFrame) -> Dict:
        """Valida que gl_account_number esté presente y no vacío"""
        column = 'gl_account_number'
        
        if column not in df.columns:
            return {
                'validation': 'Número de cuenta contable',
                'error': f'Column {column} not found',
                'is_valid': False
            }
        
        # Contar valores vacíos o nulos
        null_count = df[column].isna().sum()
        empty_count = (df[column].astype(str).str.strip() == '').sum()
        total_invalid = null_count + empty_count
        
        invalid_samples = []
        for idx, row in df[df[column].isna() | (df[column].astype(str).str.strip() == '')].head(5).iterrows():
            invalid_samples.append({
                'row': int(idx) + 2,
                'value': str(row[column]) if pd.notna(row[column]) else 'NULL',
                'issue': 'Empty or null account number'
            })
        
        return {
            'validation': 'Número de cuenta contable',
            'description': 'Verifica que todas las cuentas tengan un número válido',
            'total_rows': len(df),
            'valid_rows': len(df) - total_invalid,
            'invalid_rows': int(total_invalid),
            'invalid_samples': invalid_samples,
            'is_valid': total_invalid == 0
        }
    
    def _validate_numeric_field(self, df: pd.DataFrame, column: str, field_name: str) -> Dict:
        """Valida que un campo numérico tenga formato correcto"""
        if column not in df.columns:
            return {
                'validation': f'{field_name} - Formato numérico',
                'warning': f'Column {column} not found in file',
                'is_valid': True  # No invalidamos si la columna no existe
            }
        
        # Intentar convertir a numérico
        numeric_series = pd.to_numeric(df[column], errors='coerce')
        invalid_mask = numeric_series.isna() & df[column].notna()
        invalid_count = invalid_mask.sum()
        
        invalid_samples = []
        for idx, row in df[invalid_mask].head(5).iterrows():
            invalid_samples.append({
                'row': int(idx) + 2,
                'value': str(row[column]),
                'issue': 'Invalid numeric format'
            })
        
        return {
            'validation': f'{field_name} - Formato numérico',
            'description': f'Verifica que {field_name} tenga formato numérico correcto',
            'total_rows': len(df),
            'valid_rows': len(df) - int(invalid_count),
            'invalid_rows': int(invalid_count),
            'invalid_samples': invalid_samples,
            'is_valid': invalid_count == 0
        }
    
    def _calculate_summary(self, results: Dict) -> Dict:
        """Calcula resumen general de las validaciones"""
        fase_1 = results.get('fase_1_formato', {})
        
        completed = 0
        passed = 0
        
        if fase_1 and 'error' not in fase_1:
            completed = 1
            if fase_1.get('is_phase_valid', False):
                passed = 1
        
        return {
            'total_phases': 1,
            'completed_phases': completed,
            'passed_phases': passed,
            'failed_phases': completed - passed,
            'all_passed': passed == 1,
            'validation_complete': completed == 1
        }
    
    def _count_total_issues(self, results: Dict) -> int:
        """Cuenta el total de issues encontrados"""
        total = 0
        
        if 'fase_1_formato' in results and 'summary' in results['fase_1_formato']:
            total += results['fase_1_formato']['summary'].get('failed_checks', 0)
        
        return total
    
    def get_validation_stats(self) -> Dict:
        """Retorna estadísticas del servicio"""
        return self.validation_stats.copy()


# Singleton instance
_sumas_saldos_validation_service: Optional[SumasSaldosValidationService] = None

def get_sumas_saldos_validation_service() -> SumasSaldosValidationService:
    """Get global sumas y saldos validation service instance"""
    global _sumas_saldos_validation_service
    if _sumas_saldos_validation_service is None:
        _sumas_saldos_validation_service = SumasSaldosValidationService()
    return _sumas_saldos_validation_service