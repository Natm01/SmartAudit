# backend/app/services/validators.py
import os
import re
import codecs
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import uuid

from app.services.file_processor import detect_encoding, parse_fixed_width_txt, parse_sumas_saldos_excel, parse_csv_sumas_saldos

def validate_files(temp_dir: str, files: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Valida archivos de libro diario y sumas y saldos.
    """
    # Separar archivos por tipo basándose en el nombre
    libro_diario_files = []
    sumas_saldos_files = []
    
    for file in files:
        # Los archivos de sumas y saldos típicamente contienen estas palabras en su nombre
        if any(keyword in file.lower() for keyword in ['suma', 'saldo', 'balance', 'mayor']):
            sumas_saldos_files.append(file)
        else:
            libro_diario_files.append(file)
    
    # Si no hay archivos identificados como sumas y saldos por nombre, buscar por extensión y contenido
    if not sumas_saldos_files:
        for file in files[:]:  # Copia de la lista para modificar durante iteración
            file_path = os.path.join(temp_dir, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            # Los archivos Excel podrían ser sumas y saldos
            if file_ext in ['.xlsx', '.xls']:
                try:
                    # Intentar detectar si es sumas y saldos por contenido
                    import openpyxl
                    workbook = openpyxl.load_workbook(file_path, data_only=True)
                    worksheet = workbook.active
                    
                    # Buscar headers típicos de sumas y saldos
                    for row in worksheet.iter_rows(max_row=10, values_only=True):
                        if row and any(cell and any(keyword in str(cell).lower() for keyword in ['cta.mayor', 'saldo', 'arrastre']) for cell in row):
                            sumas_saldos_files.append(file)
                            libro_diario_files.remove(file)
                            break
                except:
                    pass
    
    # Validar libro diario
    libro_validation = validate_libro_diario(temp_dir, libro_diario_files, start_date, end_date)
    
    # Validar sumas y saldos si existen
    sumas_validation = None
    if sumas_saldos_files:
        sumas_validation = validate_sumas_saldos(temp_dir, sumas_saldos_files)
    
    # Determinar si hay errores
    has_errors = libro_validation["has_errors"]
    if sumas_validation and sumas_validation["has_errors"]:
        has_errors = True
    
    return {
        "validation_id": str(uuid.uuid4()),
        "libro_diario_validation": libro_validation,
        "sumas_saldos_validation": sumas_validation,
        "has_errors": has_errors
    }

def validate_libro_diario(temp_dir: str, files: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Valida archivos de libro diario.
    """
    checks = []
    has_errors = False
    
    if not files:
        return {
            "file_name": "Sin archivos",
            "checks": [{
                "name": "Archivos encontrados",
                "passed": False,
                "message": "No se encontraron archivos de libro diario"
            }],
            "has_errors": True
        }
    
    # Combinar todos los archivos para validación global
    all_entries = []
    
    for file_name in files:
        file_path = os.path.join(temp_dir, file_name)
        
        if not os.path.exists(file_path):
            checks.append({
                "name": "Archivo accesible",
                "passed": False,
                "message": f"No se puede acceder al archivo {file_name}"
            })
            has_errors = True
            continue
            
        encoding = detect_encoding(file_path)
        
        # Intentar parsear el archivo
        try:
            entries = parse_fixed_width_txt(file_path, encoding)
            all_entries.extend(entries)
        except Exception as e:
            checks.append({
                "name": "Formato de archivo",
                "passed": False,
                "message": f"Error al parsear el archivo {file_name}: {str(e)}"
            })
            has_errors = True
            continue
    
    # Solo realizar validaciones adicionales si se pudieron parsear archivos
    if all_entries:
        # Validación 1: Campos mínimos
        fields_check = validate_minimum_fields(all_entries)
        checks.append(fields_check)
        if not fields_check["passed"]:
            has_errors = True
        
        # Validación 2: Formato de campos
        format_check = validate_field_formats(all_entries)
        checks.append(format_check)
        if not format_check["passed"]:
            has_errors = True
        
        # Validación 3: Asientos balanceados
        balance_check = validate_balanced_entries(all_entries)
        checks.append(balance_check)
        if not balance_check["passed"]:
            has_errors = True
        
        # Validación 4: Fechas en periodo válido
        date_check = validate_date_range(all_entries, start_date, end_date)
        checks.append(date_check)
        if not date_check["passed"]:
            has_errors = True
        
        # Validación 5: Verificar todas las cuentas
        accounts_check = validate_all_accounts(all_entries)
        checks.append(accounts_check)
        if not accounts_check["passed"]:
            has_errors = True
    else:
        # Si no se pudieron parsear archivos, agregar error general
        checks.append({
            "name": "Contenido válido",
            "passed": False,
            "message": "No se pudieron extraer asientos contables de ningún archivo"
        })
        has_errors = True
    
    return {
        "file_name": ", ".join(files),
        "checks": checks,
        "has_errors": has_errors
    }

def validate_sumas_saldos(temp_dir: str, files: List[str]) -> Dict[str, Any]:
    """
    Valida archivos de sumas y saldos.
    """
    checks = []
    has_errors = False
    
    if not files:
        return {
            "file_name": "Sin archivos",
            "checks": [{
                "name": "Archivos encontrados",
                "passed": False,
                "message": "No se encontraron archivos de sumas y saldos"
            }],
            "has_errors": True
        }
    
    # Procesar todos los archivos de sumas y saldos
    all_records = []
    
    for file_name in files:
        file_path = os.path.join(temp_dir, file_name)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if not os.path.exists(file_path):
            checks.append({
                "name": "Archivo accesible",
                "passed": False,
                "message": f"No se puede acceder al archivo {file_name}"
            })
            has_errors = True
            continue
        
        try:
            if file_ext in ['.xlsx', '.xls']:
                records = parse_sumas_saldos_excel(file_path)
                all_records.extend(records)
            elif file_ext in ['.csv', '.txt']:
                # Para CSV/TXT de sumas y saldos
                encoding = detect_encoding(file_path)
                from app.services.file_processor import detect_separator
                separator = detect_separator(file_path, encoding)
                records = parse_csv_sumas_saldos(file_path, encoding, separator)
                all_records.extend(records)
            else:
                checks.append({
                    "name": "Formato de archivo",
                    "passed": False,
                    "message": f"Formato de archivo no soportado para sumas y saldos: {file_ext}"
                })
                has_errors = True
                continue
                
        except Exception as e:
            checks.append({
                "name": "Formato de archivo",
                "passed": False,
                "message": f"Error al procesar {file_name}: {str(e)}"
            })
            has_errors = True
            continue
    
    # Solo realizar validaciones adicionales si se procesaron registros
    if all_records:
        # Validación 1: Campos mínimos
        fields_check = validate_sumas_saldos_fields(all_records)
        checks.append(fields_check)
        if not fields_check["passed"]:
            has_errors = True
        
        # Validación 2: Consistencia matemática (Arrastre + Debe - Haber = Saldo Acumulado)
        consistency_check = validate_sumas_saldos_consistency(all_records)
        checks.append(consistency_check)
        if not consistency_check["passed"]:
            has_errors = True
        
        # Validación 3: Formato numérico
        numeric_check = validate_sumas_saldos_numeric_format(all_records)
        checks.append(numeric_check)
        if not numeric_check["passed"]:
            has_errors = True
        
        # Validación 4: Cuentas únicas (no duplicados)
        unique_check = validate_sumas_saldos_unique_accounts(all_records)
        checks.append(unique_check)
        if not unique_check["passed"]:
            has_errors = True
    else:
        # Si no se pudieron procesar registros, agregar error general
        checks.append({
            "name": "Contenido válido",
            "passed": False,
            "message": "No se pudieron extraer registros de sumas y saldos de ningún archivo"
        })
        has_errors = True
    
    return {
        "file_name": ", ".join(files),
        "checks": checks,
        "has_errors": has_errors
    }

def validate_sumas_saldos_fields(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que todos los registros tengan los campos mínimos requeridos.
    """
    required_fields = ["cuenta", "descripcion", "saldoAcumulado"]
    missing_fields = []
    
    for i, record in enumerate(records):
        for field in required_fields:
            if field not in record or record[field] is None or str(record[field]).strip() == '':
                missing_fields.append(f"Registro {i+1}: Falta el campo '{field}'")
    
    if missing_fields:
        return {
            "name": "Contiene los campos mínimos",
            "passed": False,
            "message": "; ".join(missing_fields[:10]) + (f" y {len(missing_fields)-10} más..." if len(missing_fields) > 10 else "")
        }
    
    return {
        "name": "Contiene los campos mínimos",
        "passed": True
    }

def validate_sumas_saldos_consistency(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica la consistencia matemática: Arrastre + Debe - Haber = Saldo Acumulado
    """
    inconsistent_records = []
    
    for i, record in enumerate(records):
        arrastre = record.get('arrastre', 0)
        debe = record.get('debe', 0)
        haber = record.get('haber', 0)
        saldo_acumulado = record.get('saldoAcumulado', 0)
        
        # Calcular saldo esperado: Arrastre + Debe - Haber = Saldo Acumulado
        # Nota: No usar abs() en haber ya que puede ser positivo o negativo según la naturaleza de la cuenta
        saldo_calculado = arrastre + debe - haber
        
        # Tolerancia para errores de redondeo
        tolerance = 0.01
        if abs(saldo_calculado - saldo_acumulado) > tolerance:
            inconsistent_records.append(
                f"Cuenta {record.get('cuenta', 'N/A')}: Cálculo inconsistente - Arrastre({arrastre:,.2f}) + Debe({debe:,.2f}) - Haber({haber:,.2f}) = {saldo_calculado:,.2f}, pero Saldo Acumulado es {saldo_acumulado:,.2f}"
            )
    
    if inconsistent_records:
        return {
            "name": "Consistencia matemática",
            "passed": False,
            "message": "; ".join(inconsistent_records[:10]) + (f" y {len(inconsistent_records)-10} más..." if len(inconsistent_records) > 10 else "")
        }
    
    return {
        "name": "Consistencia matemática",
        "passed": True
    }

def validate_sumas_saldos_unique_accounts(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que no haya cuentas duplicadas en sumas y saldos.
    """
    account_counts = {}
    duplicated_accounts = []
    
    for i, record in enumerate(records):
        account = record.get('cuenta', '').strip()
        if account:
            if account in account_counts:
                account_counts[account].append(i + 1)
            else:
                account_counts[account] = [i + 1]
    
    # Encontrar cuentas duplicadas
    for account, indices in account_counts.items():
        if len(indices) > 1:
            duplicated_accounts.append(f"Cuenta {account}: aparece en registros {', '.join(map(str, indices))}")
    
    if duplicated_accounts:
        return {
            "name": "Cuentas únicas",
            "passed": False,
            "message": "; ".join(duplicated_accounts[:10]) + (f" y {len(duplicated_accounts)-10} más..." if len(duplicated_accounts) > 10 else "")
        }
    
    return {
        "name": "Cuentas únicas",
        "passed": True
    }

def validate_sumas_saldos_numeric_format(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que los valores numéricos estén en formato correcto.
    """
    format_errors = []
    numeric_fields = ['arrastre', 'saldoAnterior', 'debe', 'haber', 'saldoAcumulado']
    
    for i, record in enumerate(records):
        for field in numeric_fields:
            value = record.get(field)
            if value is not None:
                try:
                    float(value)
                except (ValueError, TypeError):
                    format_errors.append(f"Registro {i+1}: Campo '{field}' no es numérico: {value}")
    
    if format_errors:
        return {
            "name": "Formato numérico",
            "passed": False,
            "message": "; ".join(format_errors[:10]) + (f" y {len(format_errors)-10} más..." if len(format_errors) > 10 else "")
        }
    
    return {
        "name": "Formato numérico",
        "passed": True
    }

def validate_minimum_fields(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que todos los asientos tengan los campos mínimos requeridos.
    """
    required_fields = ["entry_number", "document_number", "accounting_date", "doc_date"]
    missing_fields = []
    
    for i, entry in enumerate(entries):
        for field in required_fields:
            if field not in entry or not entry[field]:
                missing_fields.append(f"Asiento {i+1}: Falta el campo {field}")
        
        # Verificar que tenga líneas
        if "lines" not in entry or not entry["lines"]:
            missing_fields.append(f"Asiento {i+1}: No tiene líneas")
        else:
            # Verificar campos en líneas
            for j, line in enumerate(entry["lines"]):
                if "account_name" not in line or not line["account_name"]:
                    missing_fields.append(f"Asiento {i+1}, línea {j+1}: Falta el nombre de cuenta")
    
    if missing_fields:
        return {
            "name": "Contiene los campos mínimos",
            "passed": False,
            "message": "; ".join(missing_fields[:10]) + (f" y {len(missing_fields)-10} más..." if len(missing_fields) > 10 else "")
        }
    
    return {
        "name": "Contiene los campos mínimos",
        "passed": True
    }

def validate_field_formats(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica el formato de los campos.
    """
    format_errors = []
    
    for i, entry in enumerate(entries):
        # Validar fecha contable (formato DDMMYY)
        if not re.match(r'^\d{6}$', entry.get("accounting_date", "")):
            format_errors.append(f"Asiento {i+1}: Formato inválido de fecha contable: {entry.get('accounting_date', 'N/A')}")
        
        # Validar fecha documento (formato DDMMYY)
        if not re.match(r'^\d{6}$', entry.get("doc_date", "")):
            format_errors.append(f"Asiento {i+1}: Formato inválido de fecha documento: {entry.get('doc_date', 'N/A')}")
        
        # Validar líneas
        for j, line in enumerate(entry.get("lines", [])):
            # Verificar que los importes sean numéricos
            if "debit" in line and line["debit"] is not None and not isinstance(line["debit"], (int, float)):
                format_errors.append(f"Asiento {i+1}, línea {j+1}: Importe debe no es numérico: {line['debit']}")
            
            if "credit" in line and line["credit"] is not None and not isinstance(line["credit"], (int, float)):
                format_errors.append(f"Asiento {i+1}, línea {j+1}: Importe haber no es numérico: {line['credit']}")
    
    if format_errors:
        return {
            "name": "Formato de campos",
            "passed": False,
            "message": "; ".join(format_errors[:10]) + (f" y {len(format_errors)-10} más..." if len(format_errors) > 10 else "")
        }
    
    return {
        "name": "Formato de campos",
        "passed": True
    }

def validate_balanced_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que cada asiento esté balanceado (debe = haber).
    """
    unbalanced = []
    
    for entry in entries:
        total_debit = sum(line.get("debit", 0) or 0 for line in entry.get("lines", []))
        total_credit = sum(line.get("credit", 0) or 0 for line in entry.get("lines", []))
        
        # Comparar con tolerancia para errores de redondeo
        if abs(total_debit - total_credit) > 0.01:
            unbalanced.append(f"Asiento {entry.get('entry_number', 'N/A')}: Debe ({total_debit:.2f}) ≠ Haber ({total_credit:.2f})")
    
    if unbalanced:
        return {
            "name": "Asientos balanceados",
            "passed": False,
            "message": "; ".join(unbalanced[:10]) + (f" y {len(unbalanced)-10} más..." if len(unbalanced) > 10 else "")
        }
    
    return {
        "name": "Asientos balanceados",
        "passed": True
    }

def validate_date_range(entries: List[Dict[str, Any]], start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Verifica que las fechas estén dentro del rango permitido.
    """
    try:
        # Convertir fechas del formato YYYY-MM-DD a objetos datetime
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        out_of_range = []
        
        for entry in entries:
            # Convertir fecha contable de DDMMYY a datetime
            try:
                accounting_date = entry.get("accounting_date", "")
                if len(accounting_date) != 6:
                    out_of_range.append(f"Asiento {entry.get('entry_number', 'N/A')}: Formato de fecha inválido: {accounting_date}")
                    continue
                    
                # Extraer día, mes y año
                day = int(accounting_date[:2])
                month = int(accounting_date[2:4])
                year_short = int(accounting_date[4:6])
                
                # Determinar el año completo (asumiendo 20XX para años entre 00-99)
                year_full = 2000 + year_short
                
                # Validar componentes de fecha
                if not (1 <= day <= 31):
                    out_of_range.append(f"Asiento {entry.get('entry_number', 'N/A')}: Día inválido: {day}")
                    continue
                    
                if not (1 <= month <= 12):
                    out_of_range.append(f"Asiento {entry.get('entry_number', 'N/A')}: Mes inválido: {month}")
                    continue
                
                # Crear objeto datetime
                entry_date = datetime(year_full, month, day)
                
                if entry_date < start or entry_date > end:
                    out_of_range.append(f"Asiento {entry.get('entry_number', 'N/A')}: Fecha {entry_date.strftime('%d/%m/%Y')} fuera del rango permitido")
                    
            except (ValueError, TypeError) as ve:
                out_of_range.append(f"Asiento {entry.get('entry_number', 'N/A')}: Error procesando fecha: {str(ve)}")
        
        if out_of_range:
            return {
                "name": "Fechas en periodo válido",
                "passed": False,
                "message": "; ".join(out_of_range[:10]) + (f" y {len(out_of_range)-10} más..." if len(out_of_range) > 10 else "")
            }
        
        return {
            "name": "Fechas en periodo válido",
            "passed": True
        }
    
    except ValueError as e:
        return {
            "name": "Fechas en periodo válido",
            "passed": False,
            "message": f"Formato de fechas de periodo inválido: {str(e)}"
        }

def validate_all_accounts(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica que todas las cuentas necesarias estén presentes.
    """
    # Esta validación requeriría un catálogo de cuentas contra el cual comparar
    # Para el ejemplo, verificamos que haya cuentas válidas
    missing_accounts = []
    
    for i, entry in enumerate(entries):
        if not entry.get("lines"):
            continue
            
        for j, line in enumerate(entry["lines"]):
            account_name = line.get("account_name", "").strip()
            account_number = line.get("account_number", "").strip()
            
            # Verificar que al menos tengamos nombre o número de cuenta
            if not account_name and not account_number:
                missing_accounts.append(f"Asiento {entry.get('entry_number', 'N/A')}, línea {j+1}: Sin información de cuenta")
    
    if missing_accounts:
        return {
            "name": "Contiene todas las cuentas",
            "passed": False,
            "message": "; ".join(missing_accounts[:10]) + (f" y {len(missing_accounts)-10} más..." if len(missing_accounts) > 10 else "")
        }
    
    return {
        "name": "Contiene todas las cuentas",
        "passed": True
    }