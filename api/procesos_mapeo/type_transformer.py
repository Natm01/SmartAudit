# Crea este archivo: backend/procesos_mapeo/type_transformer.py

import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TypeTransformer:
    """Aplica transformaciones de tipo de dato basadas en los JSONs de definición"""
    
    def __init__(self):
        # Cargar los JSONs de definición
        config_dir = Path(__file__).parent.parent / 'config'
        
        with open(config_dir / 'journal_entries_table_mapping.json', 'r', encoding='utf-8') as f:
            je_config = json.load(f)
        
        with open(config_dir / 'trial_balance_table_mapping.json', 'r', encoding='utf-8') as f:
            tb_config = json.load(f)
        
        # Crear diccionario de tipos
        self.field_types = {}
        
        # Procesar Journal Entries
        for field in je_config['journal_entries']['header_fields']:
            self.field_types[field['name']] = field['type']
        
        for field in je_config['journal_entries']['detail_fields']:
            self.field_types[field['name']] = field['type']
        
        # Procesar Trial Balance
        for field in tb_config['trial_balance']['fields']:
            self.field_types[field['name']] = field['type']
        
        logger.info(f"TypeTransformer initialized with {len(self.field_types)} field definitions")
    
    def transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica transformaciones de tipo a todas las columnas del DataFrame
        según las definiciones del JSON
        """
        result_df = df.copy()
        stats = {
            'columns_processed': 0,
            'decimals_converted': 0,
            'dates_converted': 0,
            'integers_converted': 0,
            'strings_converted': 0,
            'errors': []
        }
        
        for column in result_df.columns:
            if column in self.field_types:
                field_type = self.field_types[column]
                
                try:
                    result_df[column] = self._apply_type_transformation(
                        result_df[column], 
                        field_type,
                        column
                    )
                    stats['columns_processed'] += 1
                    
                    # Contar por tipo
                    if 'decimal' in field_type:
                        stats['decimals_converted'] += 1
                    elif 'date' in field_type:
                        stats['dates_converted'] += 1
                    elif 'int' in field_type:
                        stats['integers_converted'] += 1
                    elif 'nvarchar' in field_type or 'char' in field_type:
                        stats['strings_converted'] += 1
                    
                except Exception as e:
                    error_msg = f"Error transforming column '{column}' to type '{field_type}': {str(e)}"
                    logger.warning(error_msg)
                    stats['errors'].append(error_msg)
        
        logger.info(f"Type transformation completed: {stats['columns_processed']} columns processed")
        logger.info(f"  - Decimals: {stats['decimals_converted']}")
        logger.info(f"  - Dates: {stats['dates_converted']}")
        logger.info(f"  - Integers: {stats['integers_converted']}")
        logger.info(f"  - Strings: {stats['strings_converted']}")
        
        if stats['errors']:
            logger.warning(f"  - Errors: {len(stats['errors'])}")
        
        return result_df
    
    def _apply_type_transformation(self, series: pd.Series, field_type: str, column_name: str) -> pd.Series:
        """Aplica la transformación de tipo específica a una serie"""
        
        # DECIMALES (amount, debit_amount, credit_amount, balances, etc.)
        if 'decimal' in field_type.lower():
            return self._convert_to_decimal(series, field_type)
        
        # FECHAS
        elif 'date' in field_type.lower():
            return self._convert_to_date(series)
        
        # HORA
        elif 'time' in field_type.lower():
            return self._convert_to_time(series)
        
        # ENTEROS (line_number, fiscal_year, period_number, etc.)
        elif 'int' in field_type.lower():
            return self._convert_to_integer(series)
        
        # BIT (boolean)
        elif 'bit' in field_type.lower():
            return self._convert_to_bit(series)
        
        # STRINGS (nvarchar, char, varchar)
        elif any(x in field_type.lower() for x in ['nvarchar', 'varchar', 'char']):
            max_length = self._extract_length(field_type)
            return self._convert_to_string(series, max_length)
        
        else:
            # Tipo no reconocido, devolver sin cambios
            logger.debug(f"Unknown type '{field_type}' for column '{column_name}', skipping transformation")
            return series
    
    def _convert_to_decimal(self, series: pd.Series, field_type: str) -> pd.Series:
        """Convierte a decimal con precisión especificada (ej: decimal(28,2))"""
        # Limpiar y convertir a float
        result = series.fillna(0)
        result = result.apply(self._clean_numeric_value)
        result = pd.to_numeric(result, errors='coerce').fillna(0)
        
        # Extraer precisión decimal del tipo (ej: decimal(28,2) -> 2)
        if ',' in field_type:
            try:
                decimal_places = int(field_type.split(',')[1].replace(')', ''))
                result = result.round(decimal_places)
            except:
                result = result.round(2)  # Default 2 decimales
        else:
            result = result.round(2)
        
        return result
    
    def _convert_to_date(self, series: pd.Series) -> pd.Series:
        """Convierte a fecha en formato YYYY-MM-DD"""
        result = pd.to_datetime(series, errors='coerce', dayfirst=True)
        
        # Convertir a string en formato ISO
        result = result.apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '')
        
        return result
    
    def _convert_to_time(self, series: pd.Series) -> pd.Series:
        """Convierte a hora en formato HH:MM:SS"""
        result = pd.to_datetime(series, errors='coerce', format='%H:%M:%S')
        
        # Convertir a string en formato HH:MM:SS
        result = result.apply(lambda x: x.strftime('%H:%M:%S') if pd.notna(x) else '')
        
        return result
    
    def _convert_to_integer(self, series: pd.Series) -> pd.Series:
        """Convierte a entero"""
        result = series.fillna(0)
        result = result.apply(self._clean_numeric_value)
        result = pd.to_numeric(result, errors='coerce').fillna(0)
        result = result.astype(int)
        
        return result
    
    def _convert_to_bit(self, series: pd.Series) -> pd.Series:
        """Convierte a bit (0 o 1)"""
        result = series.fillna(0)
        
        # Convertir valores truthy a 1, falsy a 0
        result = result.apply(lambda x: 1 if x and str(x).lower() not in ['0', 'false', 'no', ''] else 0)
        
        return result
    
    def _convert_to_string(self, series: pd.Series, max_length: int = None) -> pd.Series:
        """Convierte a string con longitud máxima"""
        result = series.fillna('').astype(str)
        
        # Limpiar valores None/NaN
        result = result.replace('nan', '').replace('None', '')
        
        # Aplicar longitud máxima si está especificada
        if max_length:
            result = result.str.slice(0, max_length)
        
        return result
    
    def _clean_numeric_value(self, value) -> float:
        """Limpia un valor numérico (maneja formatos europeos y americanos)"""
        if pd.isna(value) or value == '':
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convertir a string y limpiar
        str_value = str(value).strip()
        
        # Manejar signos negativos y paréntesis
        is_negative = False
        if str_value.startswith('-') or str_value.startswith('('):
            is_negative = True
            str_value = str_value.replace('-', '').replace('(', '').replace(')', '')
        
        # Limpiar caracteres no numéricos excepto . y ,
        cleaned = ''.join(c for c in str_value if c.isdigit() or c in '.,')
        
        if not cleaned:
            return 0.0
        
        # Detectar formato
        if '.' in cleaned and ',' in cleaned:
            # Formato: 1.234.567,89 o 1,234,567.89
            if cleaned.rindex('.') > cleaned.rindex(','):
                # Formato americano: 1,234,567.89
                cleaned = cleaned.replace(',', '')
            else:
                # Formato europeo: 1.234.567,89
                cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Solo coma: asumir decimal europeo
            cleaned = cleaned.replace(',', '.')
        
        try:
            result = float(cleaned)
            return -result if is_negative else result
        except:
            return 0.0
    
    def _extract_length(self, field_type: str) -> int:
        """Extrae la longitud máxima de un tipo string (ej: nvarchar(100) -> 100)"""
        try:
            if '(' in field_type and ')' in field_type:
                length_str = field_type.split('(')[1].split(')')[0].split(',')[0]
                return int(length_str)
        except:
            pass
        return None


# Singleton instance
_type_transformer = None

def get_type_transformer() -> TypeTransformer:
    """Obtiene la instancia global del TypeTransformer"""
    global _type_transformer
    if _type_transformer is None:
        _type_transformer = TypeTransformer()
    return _type_transformer