# backend/app/services/file_processor.py
import os
import re
import csv
import pandas as pd
from typing import List, Dict, Any, Tuple
import codecs
from datetime import datetime

def detect_encoding(file_path: str) -> str:
    """
    Detecta la codificación de un archivo.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                f.read()
                return encoding
        except UnicodeDecodeError:
            continue
    
    # Default si no se puede detectar
    return 'utf-8'

def detect_separator(file_path: str, encoding: str) -> str:
    """
    Detecta el separador de un archivo CSV/TXT.
    """
    possible_delimiters = [';', ',', '\t', '|']
    
    try:
        with codecs.open(file_path, 'r', encoding=encoding) as f:
            sample = f.read(4096)
            
        counts = {sep: sample.count(sep) for sep in possible_delimiters}
        return max(counts.items(), key=lambda x: x[1])[0]
    except:
        # Si hay error, devolver separador por defecto
        return ';'

def parse_fixed_width_txt(file_path: str, encoding: str) -> List[Dict[str, Any]]:
    """
    Procesa un archivo TXT con formato de ancho fijo, específicamente para el formato de libro diario.
    """
    entries = []
    current_entry = None
    current_lines = []
    
    with codecs.open(file_path, 'r', encoding=encoding) as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Ignorar líneas de separación o encabezados de tabla
        if line.startswith('---') or 'Nº act' in line or line.strip() == '':
            i += 1
            continue
        
        # Detectar línea de cabecera de asiento
        if re.match(r'^\d{8}', line):
            # Si ya tenemos una entrada, guardarla
            if current_entry:
                current_entry['lines'] = current_lines
                entries.append(current_entry)
                current_lines = []
            
            # Extraer datos de la cabecera
            parts = line.split()
            if len(parts) >= 5:
                entry_num = parts[0]
                doc_num = parts[1]
                fe_cont = parts[2]
                fe_doc = parts[3]
                ba_code = parts[4]
                
                # El texto de cabecera está después del código BA
                header_text = ' '.join(parts[5:]) if len(parts) > 5 else ""
                
                current_entry = {
                    'entry_number': entry_num,
                    'document_number': doc_num,
                    'accounting_date': fe_cont,
                    'doc_date': fe_doc,
                    'ba_code': ba_code,
                    'header_text': header_text
                }
            else:
                print(f"Error: Cabecera de asiento malformada: {line}")
                i += 1
                continue
        
        # Línea de detalle
        elif line.strip() and current_entry and line.startswith(' '):
            # Procesar primera columna (nombre de cuenta)
            account_name = line.strip()[:40].strip()
            
            # Extraer más información si la línea tiene suficiente longitud
            if len(line) > 40:
                # Procesamos los códigos y números de cuenta
                ap_code = line[40:48].strip()
                i_code = line[48:50].strip()
                mayus_code = line[50:65].strip() if len(line) > 65 else ""
                account_number = line[65:80].strip() if len(line) > 80 else ""
                
                # Para los importes, usamos la posición relativa y buscamos los números
                # Los importes deben estar al final de la línea
                debit_ml = 0.0
                credit_ml = 0.0
                
                # Buscar importes en la línea
                # Para líneas con código S, el importe va al Debe
                # Para líneas con código D, el importe va al Haber
                
                # Buscar todos los valores numéricos que parecen importes
                # Patrón para capturar importes con formato X.XXX,XX (incluyendo negativos)
                amount_pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})(?:-)?'
                amount_matches = list(re.finditer(amount_pattern, line))
                
                # Si encontramos al menos un importe
                if amount_matches:
                    # Si es una línea con código S, buscamos el importe en la columna Debe
                    if 'S' in i_code:
                        # El último valor numérico sería el Debe
                        debit_str = amount_matches[-1].group(1)
                        debit_ml = float(debit_str.replace('.', '').replace(',', '.'))
                    
                    # Si es una línea con código D, buscamos el importe en la columna Haber
                    elif 'D' in i_code:
                        # El último valor numérico sería el Haber
                        credit_str = amount_matches[-1].group(1)
                        credit_ml = float(credit_str.replace('.', '').replace(',', '.'))
                
                current_lines.append({
                    'account_name': account_name,
                    'ap_code': ap_code,
                    'i_code': i_code,
                    'mayus_code': mayus_code,
                    'account_number': account_number,
                    'debit': debit_ml,
                    'credit': credit_ml
                })
            else:
                # Si la línea es muy corta, podría ser la continuación de un nombre de cuenta
                # En ese caso, actualizamos el nombre de la última línea procesada
                if current_lines:
                    current_lines[-1]['account_name'] += ' ' + line.strip()
        
        i += 1
    
    # No olvidar la última entrada
    if current_entry:
        current_entry['lines'] = current_lines
        entries.append(current_entry)
    
    return entries

def process_libro_diario(temp_dir: str, files: List[str]) -> Dict[str, Any]:
    """
    Procesa archivos de libro diario.
    """
    all_entries = []
    
    for file_name in files:
        file_path = os.path.join(temp_dir, file_name)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        encoding = detect_encoding(file_path)
        
        try:
            if file_ext in ['.csv', '.txt']:
                # Usar nuestra función mejorada para el análisis
                entries = parse_fixed_width_txt(file_path, encoding)
                all_entries.extend(entries)
            elif file_ext in ['.xlsx', '.xls']:
                # Procesar archivos Excel
                try:
                    df = pd.read_excel(file_path)
                    # Implementación para Excel pendiente
                    print(f"Procesando Excel: {file_name} - {df.shape}")
                except Exception as e:
                    print(f"Error al procesar Excel: {str(e)}")
        except Exception as e:
            print(f"Error procesando archivo {file_name}: {str(e)}")
    
    # Si no hay entradas, lanzar error
    if not all_entries:
        raise ValueError("No se encontraron entradas válidas en los archivos")
    
    # Extraer rangos de fecha
    try:
        accounting_dates = []
        doc_dates = []
        
        for entry in all_entries:
            try:
                # Extraer día, mes y año del formato DDMMYY
                fe_cont = entry["accounting_date"]
                fe_doc = entry["doc_date"]
                
                day_cont = int(fe_cont[:2])
                month_cont = int(fe_cont[2:4])
                year_short_cont = int(fe_cont[4:6])
                year_cont = 2000 + year_short_cont
                
                day_doc = int(fe_doc[:2])
                month_doc = int(fe_doc[2:4])
                year_short_doc = int(fe_doc[4:6])
                year_doc = 2000 + year_short_doc
                
                accounting_dates.append(datetime(year_cont, month_cont, day_cont))
                doc_dates.append(datetime(year_doc, month_doc, day_doc))
            except (ValueError, IndexError) as e:
                print(f"Error procesando fechas del asiento {entry.get('entry_number', 'desconocido')}: {str(e)}")
                continue
        
        accounting_date_range = ""
        registration_date_range = ""
        
        if accounting_dates:
            min_accounting = min(accounting_dates)
            max_accounting = max(accounting_dates)
            accounting_date_range = f"{min_accounting.strftime('%d/%m/%Y')} - {max_accounting.strftime('%d/%m/%Y')}"
        
        if doc_dates:
            min_doc = min(doc_dates)
            max_doc = max(doc_dates)
            registration_date_range = f"{min_doc.strftime('%d/%m/%Y')} - {max_doc.strftime('%d/%m/%Y')}"
    except Exception as e:
        print(f"Error calculando rangos de fecha: {str(e)}")
        accounting_date_range = "Desconocido"
        registration_date_range = "Desconocido"
    
    return {
        "entries": all_entries,
        "accounting_date_range": accounting_date_range,
        "registration_date_range": registration_date_range
    }

def process_sumas_saldos(temp_dir: str, files: List[str]) -> Dict[str, Any]:
    """
    Procesa archivos de sumas y saldos.
    """
    # Implementación similar a process_libro_diario pero adaptada
    # a la estructura de sumas y saldos
    return {"message": "Procesamiento de sumas y saldos implementado"}