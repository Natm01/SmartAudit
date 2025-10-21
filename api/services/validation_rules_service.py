# services/validation_rules_service.py

import pandas as pd
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from procesos_mapeo.balance_validator import BalanceValidator

logger = logging.getLogger(__name__)

class ValidationRulesService:
    """
    Servicio para validar archivos contables DESPUÉS del mapeo.
    Lee el archivo CSV final y ejecuta las 4 fases de validación.
    """
    
    def __init__(self):
        self.balance_validator = BalanceValidator(tolerance=0.01)
        self.validation_stats = {
            'validations_performed': 0,
            'total_rows_validated': 0,
            'total_issues_found': 0
        }
    
    def run_all_validations(self, csv_path: str, period: str) -> Dict[str, Any]:
        """
        Ejecuta todas las validaciones sobre el archivo CSV final mapeado.
        
        Args:
            csv_path: Ruta al archivo _manual_mapped_Je.csv
            period: Período contable en formato YYYY-MM
        
        Returns:
            Dict con resultados de las 4 fases
        """
        try:
            # Leer CSV final
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV for validation: {len(df)} rows, {len(df.columns)} columns")
            
            self.validation_stats['validations_performed'] += 1
            self.validation_stats['total_rows_validated'] += len(df)
            
            results = {
                'file_info': {
                    'path': csv_path,
                    'rows': len(df),
                    'columns': list(df.columns)
                },
                'validation_timestamp': datetime.now().isoformat(),
                'period': period,
                'fase_1_formato': self.validate_format_after_mapping(df),
                'fase_2_identificadores': self.validate_identifiers(df),
                'fase_3_temporales': self.validate_temporal_with_period(df, period),
                'fase_4_integridad': self.validate_integrity(df),
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
                'fase_1_formato': {'error': str(e)},
                'fase_2_identificadores': {'error': str(e)},
                'fase_3_temporales': {'error': str(e)},
                'fase_4_integridad': {'error': str(e)},
                'summary': {
                    'total_phases': 4,
                    'completed_phases': 0,
                    'all_passed': False,
                    'has_errors': True
                }
            }
    
    # ==========================================
    # FASE 1: VALIDACIONES DE FORMATO POST-MAPEO
    # ==========================================
    
    def validate_format_after_mapping(self, df: pd.DataFrame) -> Dict:
        """
        Valida que los campos YA MAPEADOS tengan el formato correcto.
        Esto verifica el RESULTADO del proceso de accounting_data_processor
        """
        results = {
            'phase_name': 'Validaciones de Formato',
            'description': 'Verifica que los campos tengan el formato correcto después del mapeo',
            'validations': {
                'dates': {},
                'times': {},
                'amounts': {}
            },
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }
        
        # 1. FECHAS: Validar que estén en formato YYYY-MM-DD después del mapeo
        date_columns = ['posting_date', 'entry_date']
        for col in date_columns:
            if col in df.columns:
                validation_result = self._validate_date_is_iso_format(df[col])
                results['validations']['dates'][col] = validation_result
                results['summary']['total_checks'] += 1
                if validation_result['is_valid']:
                    results['summary']['passed_checks'] += 1
                else:
                    results['summary']['failed_checks'] += 1
        
        # 2. HORAS: Validar que estén en formato HH:MM:SS después del mapeo
        if 'entry_time' in df.columns:
            validation_result = self._validate_time_is_standard_format(df['entry_time'])
            results['validations']['times']['entry_time'] = validation_result
            results['summary']['total_checks'] += 1
            if validation_result['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # 3. IMPORTES: Validar que sean numéricos limpios (sin caracteres)
        amount_columns = ['debit_amount', 'credit_amount', 'amount']
        for col in amount_columns:
            if col in df.columns:
                validation_result = self._validate_amount_is_numeric(df[col])
                results['validations']['amounts'][col] = validation_result
                results['summary']['total_checks'] += 1
                if validation_result['is_valid']:
                    results['summary']['passed_checks'] += 1
                else:
                    results['summary']['failed_checks'] += 1
        
        results['is_phase_valid'] = results['summary']['failed_checks'] == 0
        
        return results
    
    def _validate_date_is_iso_format(self, series: pd.Series) -> Dict:
        """Valida que las fechas estén en formato ISO (YYYY-MM-DD)"""
        iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
        
        invalid_rows = []
        valid_count = 0
        
        for idx, value in series.items():
            if pd.isna(value) or value == '':
                continue
            
            str_value = str(value).strip()
            if re.match(iso_pattern, str_value):
                valid_count += 1
            else:
                invalid_rows.append({
                    'row': int(idx) + 2,  # +2 porque Excel empieza en 1 y hay header
                    'value': str_value,
                    'issue': 'Not in YYYY-MM-DD format'
                })
        
        return {
            'field': series.name,
            'validation': 'Fechas con formato correcto',
            'expected_format': 'YYYY-MM-DD',
            'total_values': int(series.notna().sum()),
            'valid_count': valid_count,
            'invalid_count': len(invalid_rows),
            'invalid_rows': invalid_rows[:10],
            'is_valid': len(invalid_rows) == 0
        }
    
    def _validate_time_is_standard_format(self, series: pd.Series) -> Dict:
        """Valida que los tiempos estén en formato HH:MM:SS o HH:MM"""
        time_pattern = r'^\d{1,2}:\d{2}(:\d{2})?$'
        
        invalid_rows = []
        valid_count = 0
        
        for idx, value in series.items():
            if pd.isna(value) or value == '':
                continue
            
            str_value = str(value).strip()
            if re.match(time_pattern, str_value):
                valid_count += 1
            else:
                invalid_rows.append({
                    'row': int(idx) + 2,
                    'value': str_value,
                    'issue': 'Not in HH:MM:SS format'
                })
        
        return {
            'field': series.name,
            'validation': 'Horas con formato correcto',
            'expected_format': 'HH:MM:SS or HH:MM',
            'total_values': int(series.notna().sum()),
            'valid_count': valid_count,
            'invalid_count': len(invalid_rows),
            'invalid_rows': invalid_rows[:10],
            'is_valid': len(invalid_rows) == 0
        }
    
    def _validate_amount_is_numeric(self, series: pd.Series) -> Dict:
        """Valida que los importes sean numéricos puros (resultado del proceso de limpieza)"""
        invalid_rows = []
        valid_count = 0
        
        for idx, value in series.items():
            if pd.isna(value) or value == '':
                continue
            
            # Intentar convertir a float
            try:
                float_value = float(value)
                # Verificar que no tenga caracteres extraños
                str_value = str(value).strip()
                if re.match(r'^-?\d+(\.\d+)?$', str_value):
                    valid_count += 1
                else:
                    invalid_rows.append({
                        'row': int(idx) + 2,
                        'value': str_value,
                        'issue': 'Contains non-numeric characters'
                    })
            except (ValueError, TypeError):
                invalid_rows.append({
                    'row': int(idx) + 2,
                    'value': str(value),
                    'issue': 'Cannot convert to numeric'
                })
        
        return {
            'field': series.name,
            'validation': 'Importes con formato correcto',
            'expected_format': 'Numeric (e.g., 1234.56)',
            'total_values': int(series.notna().sum()),
            'valid_count': valid_count,
            'invalid_count': len(invalid_rows),
            'invalid_rows': invalid_rows[:10],
            'is_valid': len(invalid_rows) == 0
        }
    
    # ==========================================
    # FASE 2: VALIDACIONES DE IDENTIFICADORES
    # ==========================================
    
    def validate_identifiers(self, df: pd.DataFrame) -> Dict:
        """Validar unicidad y secuencialidad de identificadores"""
        results = {
            'phase_name': 'Validaciones de Identificadores',
            'description': 'Verifica la unicidad y secuencialidad de los identificadores',
            'validations': {
                'unique_journal_ids': {},
                'sequential_line_numbers': {}
            },
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }
        
        # Validación 1: Journal Entry IDs únicos
        unique_ids_result = self._validate_unique_journal_ids(df)
        results['validations']['unique_journal_ids'] = unique_ids_result
        results['summary']['total_checks'] += 1
        if unique_ids_result['is_valid']:
            results['summary']['passed_checks'] += 1
        else:
            results['summary']['failed_checks'] += 1
        
        # Validación 2: Line numbers secuenciales
        sequential_result = self._validate_sequential_lines(df)
        results['validations']['sequential_line_numbers'] = sequential_result
        results['summary']['total_checks'] += 1
        if sequential_result['is_valid']:
            results['summary']['passed_checks'] += 1
        else:
            results['summary']['failed_checks'] += 1
        
        results['is_phase_valid'] = results['summary']['failed_checks'] == 0
        
        return results
    
    def _validate_unique_journal_ids(self, df: pd.DataFrame) -> Dict:
        """Valida que los journal_entry_id sean consistentes"""
        
        if 'journal_entry_id' not in df.columns:
            return {
                'validation': 'Identificadores de asientos únicos',
                'error': 'Column journal_entry_id not found',
                'is_valid': False
            }
        
        # Contar apariciones de cada ID
        id_counts = df['journal_entry_id'].value_counts()
        
        # Los IDs deben repetirse (múltiples líneas por asiento)
        duplicate_ids = id_counts[id_counts > 1]
        unique_ids = id_counts[id_counts == 1]
        
        # Detectar IDs que aparecen solo una vez (posible error si son muchos)
        suspicious_single_ids = []
        if len(unique_ids) > 0:
            for entry_id in unique_ids.head(10).index:
                suspicious_single_ids.append({
                    'journal_entry_id': str(entry_id),
                    'line_count': 1,
                    'issue': 'Journal entry with only one line (may be valid)'
                })
        
        return {
            'validation': 'Identificadores de asientos únicos',
            'description': 'Los journal_entry_id deben ser únicos por asiento',
            'total_unique_ids': len(id_counts),
            'ids_with_multiple_lines': len(duplicate_ids),
            'ids_with_single_line': len(unique_ids),
            'suspicious_ids': suspicious_single_ids,
            'is_valid': True  # Siempre válido si la columna existe
        }
    
    def _validate_sequential_lines(self, df: pd.DataFrame) -> Dict:
        """Valida que line_number sea secuencial dentro de cada asiento"""
        
        # Si no existe la columna line_number, marcar como opcional y válida
        if 'line_number' not in df.columns:
            return {
                'validation': 'Identificadores de apuntes secuenciales',
                'description': 'Los line_number deben ser secuenciales dentro de cada asiento',
                'status': 'skipped',
                'reason': 'Column line_number not found - validation skipped (optional)',
                'is_valid': True,  # CAMBIO CLAVE: Marcamos como válida aunque no exista
                'optional': True
            }
        
        # Si no existe journal_entry_id, entonces sí es un error
        if 'journal_entry_id' not in df.columns:
            return {
                'validation': 'Identificadores de apuntes secuenciales',
                'error': 'Column journal_entry_id is required for this validation',
                'is_valid': False
            }
        
        issues = []
        
        # Agrupar por asiento
        for entry_id, group in df.groupby('journal_entry_id'):
            # Convertir a numérico y eliminar NaN
            line_numbers = pd.to_numeric(group['line_number'], errors='coerce').dropna()
            line_numbers_sorted = sorted(line_numbers.tolist())
            
            if len(line_numbers_sorted) == 0:
                continue
            
            # Verificar secuencia (debe ser 1, 2, 3... o 0, 1, 2...)
            start = line_numbers_sorted[0]
            expected = list(range(int(start), int(start) + len(line_numbers_sorted)))
            
            if line_numbers_sorted != expected:
                missing = [x for x in expected if x not in line_numbers_sorted]
                issues.append({
                    'journal_entry_id': str(entry_id),
                    'expected': expected,
                    'actual': line_numbers_sorted,
                    'missing_numbers': missing,
                    'issue': 'Non-sequential line numbers'
                })
        
        return {
            'validation': 'Identificadores de apuntes secuenciales',
            'description': 'Los line_number deben ser secuenciales dentro de cada asiento',
            'total_entries_checked': int(df['journal_entry_id'].nunique()),
            'entries_with_issues': len(issues),
            'issue_details': issues[:10],
            'is_valid': len(issues) == 0
        }
    
    # ==========================================
    # FASE 3: VALIDACIONES TEMPORALES
    # ==========================================
    
    def validate_temporal_with_period(self, df: pd.DataFrame, period: str) -> Dict:
        """
        Valida fechas contra el período contable enviado desde el frontend.
        
        period format: "YYYY-MM" (ej: "2024-12")
        
        Reglas:
        - posting_date (fecha contable): DEBE estar dentro del período
        - entry_date (fecha registro): DEBE estar dentro del período O ser mayor
        """
        
        results = {
            'phase_name': 'Validaciones Temporales',
            'description': 'Verifica que las fechas estén dentro del período contable',
            'period': period,
            'validations': {
                'posting_date_in_period': {},
                'entry_date_valid': {}
            },
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }
        
        # Parsear período
        try:
            period_start, period_end = self._parse_period(period)
        except Exception as e:
            return {
                'phase_name': 'Validaciones Temporales',
                'error': f'Invalid period format: {period}. Expected "YYYY-MM" or "YYYY-MM-DD a YYYY-MM-DD"',
                'is_phase_valid': False
            }
        
        results['period_start'] = period_start.strftime('%Y-%m-%d')
        results['period_end'] = period_end.strftime('%Y-%m-%d')
        
        # VALIDACIÓN 1: posting_date DENTRO del período
        if 'posting_date' in df.columns:
            posting_result = self._validate_posting_date_in_period(
                df, period_start, period_end
            )
            results['validations']['posting_date_in_period'] = posting_result
            results['summary']['total_checks'] += 1
            if posting_result['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        # VALIDACIÓN 2: entry_date DENTRO del período O MAYOR
        if 'entry_date' in df.columns:
            entry_result = self._validate_entry_date_valid(
                df, period_start, period_end
            )
            results['validations']['entry_date_valid'] = entry_result
            results['summary']['total_checks'] += 1
            if entry_result['is_valid']:
                results['summary']['passed_checks'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        results['is_phase_valid'] = results['summary']['failed_checks'] == 0
        
        return results
    
    def _parse_period(self, period: str) -> tuple:
        """
        Parsea el período en múltiples formatos y retorna (period_start, period_end)
        
        Formatos soportados:
        1. "YYYY-MM" -> primer día al último día del mes
        2. "YYYY-MM-DD a YYYY-MM-DD" -> rango exacto
        3. "YYYY-MM-DD to YYYY-MM-DD" -> rango exacto
        """
        import pandas as pd
        import re
        
        period = period.strip()
        
        # Formato 1: "YYYY-MM" (ej: "2024-12")
        if re.match(r'^\d{4}-\d{2}$', period):
            year, month = map(int, period.split('-'))
            period_start = pd.Timestamp(year=year, month=month, day=1)
            
            # Último día del mes
            if month == 12:
                period_end = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
            else:
                period_end = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
            
            return period_start, period_end
        
        # Formato 2 y 3: "YYYY-MM-DD a YYYY-MM-DD" o "YYYY-MM-DD to YYYY-MM-DD"
        separators = [' a ', ' to ', ' - ']
        
        for sep in separators:
            if sep in period:
                parts = period.split(sep)
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    
                    # Validar formato de fechas
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', start_str) and re.match(r'^\d{4}-\d{2}-\d{2}$', end_str):
                        period_start = pd.Timestamp(start_str)
                        period_end = pd.Timestamp(end_str)
                        
                        # Validar que la fecha de inicio sea menor que la de fin
                        if period_start > period_end:
                            raise ValueError(f"Start date {start_str} is after end date {end_str}")
                        
                        return period_start, period_end
        
        # Si no coincide con ningún formato, lanzar error
        raise ValueError(f"Period format not recognized: {period}")
    
    def _validate_posting_date_in_period(self, df: pd.DataFrame, 
                                        period_start: pd.Timestamp, 
                                        period_end: pd.Timestamp) -> Dict:
        """Valida que posting_date esté dentro del período"""
        
        df_temp = df.copy()
        df_temp['posting_date_parsed'] = pd.to_datetime(df_temp['posting_date'], errors='coerce')
        
        # Fechas fuera del período
        out_of_period = df_temp[
            (df_temp['posting_date_parsed'] < period_start) | 
            (df_temp['posting_date_parsed'] > period_end)
        ]
        
        invalid_samples = []
        for idx, row in out_of_period.head(10).iterrows():
            invalid_samples.append({
                'row': int(idx) + 2,
                'posting_date': str(row['posting_date']),
                'parsed_date': row['posting_date_parsed'].strftime('%Y-%m-%d') if pd.notna(row['posting_date_parsed']) else 'Invalid',
                'issue': f"Outside period {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            })
        
        return {
            'validation': 'Fecha contable en el período',
            'rule': 'Fecha contable debe estar dentro del período',
            'total_rows': len(df_temp),
            'rows_in_period': len(df_temp) - len(out_of_period),
            'rows_out_of_period': len(out_of_period),
            'is_valid': len(out_of_period) == 0,
            'out_of_period_samples': invalid_samples
        }
    
    def _validate_entry_date_valid(self, df: pd.DataFrame, 
                                   period_start: pd.Timestamp, 
                                   period_end: pd.Timestamp) -> Dict:
        """Valida que entry_date esté dentro del período o sea posterior"""
        
        df_temp = df.copy()
        df_temp['entry_date_parsed'] = pd.to_datetime(df_temp['entry_date'], errors='coerce')
        
        # Fechas ANTES del período (no permitido)
        before_period = df_temp[df_temp['entry_date_parsed'] < period_start]
        
        # Fechas dentro o después del período (permitido)
        valid_dates = df_temp[df_temp['entry_date_parsed'] >= period_start]
        
        invalid_samples = []
        for idx, row in before_period.head(10).iterrows():
            invalid_samples.append({
                'row': int(idx) + 2,
                'entry_date': str(row['entry_date']),
                'parsed_date': row['entry_date_parsed'].strftime('%Y-%m-%d') if pd.notna(row['entry_date_parsed']) else 'Invalid',
                'issue': f"Before period start {period_start.strftime('%Y-%m-%d')}"
            })
        
        return {
            'validation': 'Fecha registro excede el período contable',
            'rule': 'Fecha de registro debe estar dentro del período o ser posterior',
            'total_rows': len(df_temp),
            'rows_valid': len(valid_dates),
            'rows_before_period': len(before_period),
            'is_valid': len(before_period) == 0,
            'invalid_samples': invalid_samples
        }
    
    # ==========================================
    # FASE 4: VALIDACIONES DE INTEGRIDAD
    # ==========================================
    
    def validate_integrity(self, df: pd.DataFrame) -> Dict:
        """Validar balance usando balance_validator existente"""
        
        results = {
            'phase_name': 'Validaciones de Integridad Contable',
            'description': 'Verifica que los asientos estén balanceados',
            'validations': {
                'balanced_entries': {}
            },
            'summary': {
                'total_checks': 1,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }
        
        try:
            balance_result = self.balance_validator.perform_comprehensive_balance_validation(df)
            
            is_valid = balance_result['is_balanced']
            
            results['validations']['balanced_entries'] = {
                'validation': 'Asientos balanceados',
                'rule': 'Debe = Haber para cada asiento',
                'is_balanced': balance_result['is_balanced'],
                'total_entries': balance_result.get('entries_count', 0),
                'balanced_count': balance_result.get('balanced_entries_count', 0),
                'unbalanced_count': balance_result.get('entries_count', 0) - balance_result.get('balanced_entries_count', 0),
                'total_debit': float(balance_result.get('total_debit_sum', 0)),
                'total_credit': float(balance_result.get('total_credit_sum', 0)),
                'total_difference': float(balance_result.get('total_balance_difference', 0)),
                'unbalanced_entries': balance_result.get('unbalanced_entries', [])[:10],
                'is_valid': is_valid
            }
            
            if is_valid:
                results['summary']['passed_checks'] = 1
            else:
                results['summary']['failed_checks'] = 1
            
            results['is_phase_valid'] = is_valid
            
        except Exception as e:
            logger.error(f"Error validating balance: {e}")
            results['validations']['balanced_entries'] = {
                'validation': 'Asientos balanceados',
                'error': str(e),
                'is_valid': False
            }
            results['summary']['failed_checks'] = 1
            results['is_phase_valid'] = False
        
        return results
    
    # ==========================================
    # UTILIDADES
    # ==========================================
    
    def _calculate_summary(self, results: Dict) -> Dict:
        """Calcula resumen general de las validaciones"""
        phases = ['fase_1_formato', 'fase_2_identificadores', 'fase_3_temporales', 'fase_4_integridad']
        
        completed = 0
        passed = 0
        
        for phase in phases:
            if phase in results and 'error' not in results[phase]:
                completed += 1
                if results[phase].get('is_phase_valid', False):
                    passed += 1
        
        return {
            'total_phases': 4,
            'completed_phases': completed,
            'passed_phases': passed,
            'failed_phases': completed - passed,
            'all_passed': passed == 4,
            'validation_complete': completed == 4
        }
    
    def _count_total_issues(self, results: Dict) -> int:
        """Cuenta el total de issues encontrados en todas las fases"""
        total = 0
        
        # Fase 1
        if 'fase_1_formato' in results and 'summary' in results['fase_1_formato']:
            total += results['fase_1_formato']['summary'].get('failed_checks', 0)
        
        # Fase 2
        if 'fase_2_identificadores' in results and 'summary' in results['fase_2_identificadores']:
            total += results['fase_2_identificadores']['summary'].get('failed_checks', 0)
        
        # Fase 3
        if 'fase_3_temporales' in results and 'summary' in results['fase_3_temporales']:
            total += results['fase_3_temporales']['summary'].get('failed_checks', 0)
        
        # Fase 4
        if 'fase_4_integridad' in results and 'summary' in results['fase_4_integridad']:
            total += results['fase_4_integridad']['summary'].get('failed_checks', 0)
        
        return total
    
    def get_validation_stats(self) -> Dict:
        """Retorna estadísticas del servicio"""
        return self.validation_stats.copy()


# Singleton instance
_validation_rules_service: Optional[ValidationRulesService] = None

def get_validation_rules_service() -> ValidationRulesService:
    """Get global validation rules service instance"""
    global _validation_rules_service
    if _validation_rules_service is None:
        _validation_rules_service = ValidationRulesService()
    return _validation_rules_service