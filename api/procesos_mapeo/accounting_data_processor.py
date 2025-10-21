# procesos_mapeo/accounting_data_processor.py

import pandas as pd
import re
from typing import Dict, List, Tuple, Any, Optional
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class AccountingDataProcessor:
    """
    Reusable processor for accounting data with numeric cleaning and calculations
    """
    
    def __init__(self):
        self.stats = {
            'zero_filled_fields': 0,
            'debit_credit_calculated': 0,
            'debit_amounts_from_indicator': 0,
            'credit_amounts_from_indicator': 0,
            'amount_signs_adjusted': 0,
            'fields_cleaned': 0,
            'parentheses_negatives_processed': 0,
            'amount_calculated': 0,
            'indicators_created': 0
        }

    def separate_datetime_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Separates fields containing combined date and time into separate fields.
        Ensures all dates are converted to YYYY-MM-DD format.
        """
        
        def _separate_single_datetime_field(df, field_name):
            """Auxiliary function to separate an individual datetime field"""
            if field_name not in df.columns:
                return False
            
            sample_values = df[field_name].dropna().head(10)
            if len(sample_values) == 0:
                return False
            
            datetime_detected = False
            pure_date_count = 0
            pure_time_count = 0
            detected_format = None
            detected_dayfirst = True
            
            for value in sample_values:
                str_value = str(value).strip()
                
                pure_date_patterns = [
                    r'^\d{1,2}\.\d{1,2}\.\d{4}$',
                    r'^\d{1,2}/\d{1,2}/\d{4}$',
                    r'^\d{1,2}-\d{1,2}-\d{4}$',
                    r'^\d{4}-\d{2}-\d{2}$',
                    r'^\d{4}/\d{2}/\d{2}$',
                    r'^\d{4}\.\d{2}\.\d{2}$',
                    r'^\d{8}$',
                ]
                
                pure_time_patterns = [
                    r'^\d{1,2}:\d{2}:\d{2}$',
                    r'^\d{1,2}:\d{2}$',
                    r'^\d{1,2}:\d{2}:\d{2}\.\d+$',
                ]
                
                if any(re.match(pattern, str_value) for pattern in pure_date_patterns):
                    pure_date_count += 1
                    if not detected_format:
                        if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', str_value):
                            detected_format = '%d.%m.%Y'
                            detected_dayfirst = True
                        elif re.match(r'^\d{4}-\d{2}-\d{2}$', str_value):
                            detected_format = '%Y-%m-%d'
                            detected_dayfirst = False
                        elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', str_value):
                            detected_dayfirst = True
                        else:
                            detected_dayfirst = '.' in str_value or not str_value.startswith(('20', '19'))
                    continue
                elif any(re.match(pattern, str_value) for pattern in pure_time_patterns):
                    pure_time_count += 1
                    continue
                
                combined_datetime_patterns = [
                    r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}',
                    r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}',
                    r'\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{2}',
                    r'\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}',
                    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
                ]
                
                for pattern in combined_datetime_patterns:
                    if re.search(pattern, str_value):
                        datetime_detected = True
                        if not detected_format:
                            if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}', str_value):
                                detected_format = '%d.%m.%Y %H:%M:%S'
                                detected_dayfirst = True
                            elif re.search(r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', str_value):
                                detected_format = '%Y-%m-%d %H:%M:%S'
                                detected_dayfirst = False
                            elif re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', str_value):
                                detected_format = '%Y-%m-%dT%H:%M:%S'
                                detected_dayfirst = False
                            else:
                                detected_dayfirst = '.' in str_value or ('/' in str_value and not str_value.startswith(('20', '19')))
                        break
                
                if datetime_detected:
                    break
            
            total_samples = len(sample_values)
            if total_samples == 0:
                return False
                
            pure_date_ratio = pure_date_count / total_samples
            pure_time_ratio = pure_time_count / total_samples
            
            def convert_to_standard_date(value, dayfirst=detected_dayfirst):
                """Converts any date to YYYY-MM-DD format"""
                if pd.isna(value) or value == '':
                    return value
                
                str_value = str(value).strip()
                try:
                    parsed_dt = pd.to_datetime(str_value, dayfirst=dayfirst, errors='coerce')
                    if not pd.isna(parsed_dt):
                        return parsed_dt.strftime('%Y-%m-%d')
                    else:
                        return str_value
                except:
                    return str_value
            
            if pure_date_ratio >= 0.7:
                df[field_name] = df[field_name].apply(lambda x: convert_to_standard_date(x, detected_dayfirst))
                return False
            elif pure_time_ratio >= 0.7:
                return False
            elif not datetime_detected:
                df[field_name] = df[field_name].apply(lambda x: convert_to_standard_date(x, detected_dayfirst))
                return False
            
            dates = []
            times = []
            
            for value in df[field_name]:
                if pd.isna(value) or value == '':
                    dates.append('')
                    times.append('')
                    continue
                
                str_value = str(value).strip()
                
                if any(re.match(pattern, str_value) for pattern in pure_date_patterns):
                    try:
                        parsed_dt = pd.to_datetime(str_value, dayfirst=detected_dayfirst, errors='coerce')
                        date_str = parsed_dt.strftime('%Y-%m-%d') if not pd.isna(parsed_dt) else str_value
                    except:
                        date_str = str_value

                    dates.append(date_str)
                    times.append('')
                    continue
                
                if any(re.match(pattern, str_value) for pattern in pure_time_patterns):
                    dates.append('')
                    times.append(str_value)
                    continue
                
                has_space_and_colon = ' ' in str_value and ':' in str_value
                has_t_separator = 'T' in str_value and ':' in str_value
                
                if has_space_and_colon or has_t_separator:
                    try:
                        if detected_format:
                            try:
                                parsed_dt = pd.to_datetime(str_value, format=detected_format)
                            except:
                                parsed_dt = pd.to_datetime(str_value, dayfirst=detected_dayfirst, errors='raise')
                        else:
                            parsed_dt = pd.to_datetime(str_value, dayfirst=detected_dayfirst, errors='raise')
                        
                        date_str = parsed_dt.strftime('%Y-%m-%d')
                        time_str = parsed_dt.strftime('%H:%M:%S')

                        dates.append(date_str)
                        times.append(time_str)
                        
                    except Exception as e:
                        try:
                            parsed_dt = pd.to_datetime(str_value, dayfirst=detected_dayfirst, errors='coerce')
                            date_str = parsed_dt.strftime('%Y-%m-%d') if not pd.isna(parsed_dt) else str_value
                        except:
                            date_str = str_value
                        dates.append(date_str)
                        times.append('')
                else:
                    try:
                        parsed_dt = pd.to_datetime(str_value, dayfirst=detected_dayfirst, errors='coerce')
                        date_str = parsed_dt.strftime('%Y-%m-%d') if not pd.isna(parsed_dt) else str_value
                    except:
                        date_str = str_value
                    dates.append(date_str)
                    times.append('')
            
            if any(time for time in times if time):
                if field_name == 'entry_date':
                    date_field = 'entry_date'
                    time_field = 'entry_time'
                elif field_name == 'entry_time':
                    date_field = 'entry_date'
                    time_field = 'entry_time'
                else:
                    date_field = field_name
                    time_field = field_name.replace('_date', '_time').replace('date', 'time')
                    if time_field == date_field:
                        time_field = f"{field_name}_time"
                
                df[date_field] = dates
                
                if time_field not in df.columns or df[time_field].isna().all():
                    df[time_field] = times
                else:
                    counter = 1
                    new_time_field = f"{time_field}_{counter}"
                    while new_time_field in df.columns:
                        counter += 1
                        new_time_field = f"{time_field}_{counter}"
                    df[new_time_field] = times
                    time_field = new_time_field
                
                return True
            else:
                df[field_name] = dates
                return False
            
            return False
        
        try:
            fields_to_process = ['entry_date', 'entry_time', 'posting_date']
            
            for field_name in fields_to_process:
                if field_name in df.columns:
                    _separate_single_datetime_field(df, field_name)
                
        except Exception as e:
            logger.error(f"Error processing DateTime fields: {e}")

        return df

    def process_numeric_fields_and_calculate_amounts(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Main function that processes numeric fields and calculates amounts according to availability.
        Returns: DataFrame and statistics dictionary
        """
        try:
            self.stats = {key: 0 for key in self.stats.keys()}
            
            df = self._clean_existing_numeric_fields(df)
            
            has_amount = 'amount' in df.columns
            has_debit = 'debit_amount' in df.columns
            has_credit = 'credit_amount' in df.columns
            has_indicator = (
                'debit_credit_indicator' in df.columns and 
                not df['debit_credit_indicator'].isna().all() and
                (df['debit_credit_indicator'] != '').any()
            )
            
            if not has_amount and has_debit and has_credit:
                df = self.debit_credit_to_amount(df)
            elif has_amount and not has_indicator and not has_debit and not has_credit:
                df = self.amount_only_create_indicator(df)
            elif has_amount and has_indicator:
                pass
            elif has_amount and has_debit and has_credit and not has_indicator:
                df = self.create_indicator_from_debit_credit_pattern(df)
            
            return df, self.stats.copy()
            
        except Exception as e:
            logger.error(f"Error in accounting data processing: {e}")
            return df, self.stats.copy()

    def debit_credit_to_amount(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SCENARIO 1: Has debit_amount and credit_amount but no amount
        - Calculates amount = debit_amount - credit_amount (NO absolute values)
        - Creates debit_credit_indicator: 'D' if debit != 0 and credit == 0, 'H' if debit == 0 and credit != 0
        """
        df['debit_amount'] = df['debit_amount'].apply(self._clean_numeric_value_with_zero_fill)
        df['credit_amount'] = df['credit_amount'].apply(self._clean_numeric_value_with_zero_fill)
        
        df['amount'] = df['debit_amount'] - df['credit_amount']
        
        df['debit_credit_indicator'] = ''
        
        mask_debit = (df['credit_amount'] == 0)
        df.loc[mask_debit, 'debit_credit_indicator'] = 'D'
        
        mask_credit = (df['debit_amount'] == 0) & (df['credit_amount'] != 0)
        df.loc[mask_credit, 'debit_credit_indicator'] = 'H'
        
        debit_count = mask_debit.sum()
        credit_count = mask_credit.sum()
        
        self.stats['amount_calculated'] = len(df)
        self.stats['indicators_created'] = debit_count + credit_count
        
        return df
    
    def create_indicator_from_debit_credit_pattern(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SCENARIO 4: Has amount, debit_amount, credit_amount but no indicator
        Creates indicator based on debit/credit pattern
        """
        df['debit_credit_indicator'] = ''
        
        mask_debit = (df['credit_amount'] == 0)
        df.loc[mask_debit, 'debit_credit_indicator'] = 'D'
        
        mask_credit = (df['debit_amount'] == 0) & (df['credit_amount'] != 0)
        df.loc[mask_credit, 'debit_credit_indicator'] = 'H'
        
        debit_count = mask_debit.sum()
        credit_count = mask_credit.sum()
        
        self.stats['indicators_created'] = debit_count + credit_count
        return df

    def amount_only_create_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SCENARIO 2: Has only amount without indicator or debit/credit
        Creates debit_credit_indicator column based on amount sign
        """
        df['amount'] = df['amount'].apply(self._clean_numeric_value_with_zero_fill)
        
        df['debit_credit_indicator'] = ''
        
        mask_positive = df['amount'] > 0
        df.loc[mask_positive, 'debit_credit_indicator'] = 'D'
        
        mask_negative = df['amount'] < 0
        df.loc[mask_negative, 'debit_credit_indicator'] = 'H'
        
        positive_count = mask_positive.sum()
        negative_count = mask_negative.sum()
        
        self.stats['indicators_created'] = positive_count + negative_count
        
        return df

    def _clean_existing_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans existing numeric fields WITHOUT applying absolute values"""
        numeric_fields = ['amount', 'debit_amount', 'credit_amount', 'debit', 'credit', 
                         'debe', 'haber', 'importe', 'valor']
        
        for field in numeric_fields:
            if field in df.columns:
                parentheses_count = df[field].astype(str).str.contains(r'\(', na=False).sum()
                
                df[field] = df[field].apply(self._clean_numeric_value_with_zero_fill)
                
                zero_count = (df[field] == 0.0).sum()
                self.stats['zero_filled_fields'] += zero_count
                self.stats['fields_cleaned'] += 1
                self.stats['parentheses_negatives_processed'] += parentheses_count
                
                self.stats['fields_cleaned'] += 1
        
        return df

    def _clean_numeric_value_with_zero_fill(self, value) -> float:
        """
        Cleans an individual numeric value WITHOUT applying absolute values
        - Converts to float if possible
        - Handles parentheses as negative values
        - Returns 0.0 for invalid or empty values
        - Handles European formats like 25.000.00
        """
        if pd.isna(value) or value == '' or str(value).strip() == '':
            return 0.0
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            str_value = str(value).strip()
            if str_value == '':
                return 0.0
            
            is_parentheses_negative = bool(re.search(r'\([^)]*\d+[^)]*\)', str_value))
            
            cleaned = re.sub(r'[^\d.,\-]', '', str_value)
            
            if cleaned:
                if ',' in cleaned and '.' in cleaned:
                    if cleaned.rfind(',') < cleaned.rfind('.'):
                        cleaned = cleaned.replace(',', '')
                    else:
                        last_comma = cleaned.rfind(',')
                        cleaned = cleaned[:last_comma].replace(',', '').replace('.', '') + '.' + cleaned[last_comma+1:]
                elif ',' in cleaned:
                    parts = cleaned.split(',')
                    if len(parts[-1]) <= 2:
                        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
                    else:
                        cleaned = cleaned.replace(',', '')
                elif '.' in cleaned:
                    dot_parts = cleaned.split('.')
                    if len(dot_parts) >= 2:
                        last_part = dot_parts[-1]
                        if len(dot_parts) > 2 and len(last_part) <= 2 and last_part.isdigit():
                            integer_part = ''.join(dot_parts[:-1])
                            cleaned = f"{integer_part}.{last_part}"
                        elif len(dot_parts) == 2 and len(last_part) > 2:
                            cleaned = cleaned.replace('.', '')
                
                first_num = re.search(r'-?\d+\.?\d*', cleaned)
                if first_num:
                    result = float(first_num.group())
                    if is_parentheses_negative:
                        result = -result
                    return result
                    
                return 0.0
        except:
            return 0.0


# Utility functions for direct use
def clean_numeric_field(series: pd.Series, field_name: str = "field") -> pd.Series:
    """Utility function to clean a numeric series"""
    processor = AccountingDataProcessor()
    return series.apply(processor._clean_numeric_value_with_zero_fill)

def calculate_amount_from_debit_credit(debit_series: pd.Series, credit_series: pd.Series) -> pd.Series:
    """Utility function to calculate amount from debit and credit WITHOUT absolute values"""
    return debit_series - credit_series

def create_debit_credit_indicator(amount_series: pd.Series) -> pd.Series:
    """Utility function to create indicator from amount"""
    indicator = pd.Series('', index=amount_series.index)
    indicator[amount_series > 0] = 'D'
    indicator[amount_series < 0] = 'H'
    return indicator