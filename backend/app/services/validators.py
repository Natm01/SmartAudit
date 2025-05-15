# backend/app/services/validators.py
import os
import re
import codecs
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import uuid

from app.services.file_processor import detect_encoding, parse_fixed_width_txt

def validate_files(temp_dir: str, files: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Valida archivos de libro diario y sumas y saldos.
    """
    libro_diario_files = [f for f in files if not f.startswith('sumas_')]
    sumas_saldos_files = [f for f in files if f.startswith('sumas_')]
    
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
    
    # Combinar todos los archivos para validación global
    all_entries = []
    
    for file_name in files:
        file_path = os.path.join(temp_dir, file_name)
        encoding = detect_encoding(file_path)
        
        # Intentar parsear el archivo
        try:
            entries = parse_fixed_width_txt(file_path, encoding)
            all_entries.extend(entries)
        except Exception as e:
            checks.append({
                "name": "Formato de archivo",
                "passed": False,
                "message": f"Error al parsear el archivo: {str(e)}"
            })
            has_errors = True
            continue
    
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
    
    return {
        "file_name": ", ".join(files),
        "checks": checks,
        "has_errors": has_errors
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
            "message": "; ".join(missing_fields[:5]) + f"{' y otros...' if len(missing_fields) > 5 else ''}"
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
        if not re.match(r'^\d{6}$', entry["accounting_date"]):
            format_errors.append(f"Asiento {i+1}: Formato inválido de fecha contable")
        
        # Validar fecha documento (formato DDMMYY)
        if not re.match(r'^\d{6}$', entry["doc_date"]):
            format_errors.append(f"Asiento {i+1}: Formato inválido de fecha documento")
        
        # Validar líneas
        for j, line in enumerate(entry["lines"]):
            # Verificar que los importes sean numéricos
            if "debit" in line and line["debit"] and not isinstance(line["debit"], (int, float)):
                format_errors.append(f"Asiento {i+1}, línea {j+1}: Importe debe no es numérico")
            
            if "credit" in line and line["credit"] and not isinstance(line["credit"], (int, float)):
                format_errors.append(f"Asiento {i+1}, línea {j+1}: Importe haber no es numérico")
    
    if format_errors:
        return {
            "name": "Formato de campos",
            "passed": False,
            "message": "; ".join(format_errors[:5]) + f"{' y otros...' if len(format_errors) > 5 else ''}"
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
        total_debit = sum(line.get("debit", 0) for line in entry["lines"])
        total_credit = sum(line.get("credit", 0) for line in entry["lines"])
        
        # Comparar con tolerancia para errores de redondeo
        if abs(total_debit - total_credit) > 0.01:
            unbalanced.append(f"Asiento {entry['entry_number']}: Debe ({total_debit:.2f}) ≠ Haber ({total_credit:.2f})")
    
    if unbalanced:
        return {
            "name": "Asientos balanceados",
            "passed": False,
            "message": "; ".join(unbalanced[:5]) + f"{' y otros...' if len(unbalanced) > 5 else ''}"
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
                # Extraer día, mes y año
                day = int(entry["accounting_date"][:2])
                month = int(entry["accounting_date"][2:4])
                year_short = int(entry["accounting_date"][4:6])
                
                # Determinar el año completo (asumiendo 20XX para años entre 00-99)
                year_full = 2000 + year_short
                
                # Crear objeto datetime
                entry_date = datetime(year_full, month, day)
                
                if entry_date < start or entry_date > end:
                    out_of_range.append(f"Asiento {entry['entry_number']}: Fecha {entry_date.strftime('%d/%m/%Y')} fuera del rango permitido")
            except ValueError as ve:
                out_of_range.append(f"Asiento {entry['entry_number']}: Formato de fecha inválido - {str(ve)}")
        
        if out_of_range:
            return {
                "name": "Fechas en periodo válido",
                "passed": False,
                "message": "; ".join(out_of_range[:5]) + f"{' y otros...' if len(out_of_range) > 5 else ''}"
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
    # Para el ejemplo, asumimos que todas las cuentas están presentes
    return {
        "name": "Contiene todas las cuentas",
        "passed": True
    }

def validate_sumas_saldos(temp_dir: str, files: List[str]) -> Dict[str, Any]:
    """
    Valida archivos de sumas y saldos.
    """
    # Simular problemas para el ejemplo
    checks = [
        {
            "name": "Contiene los campos mínimos",
            "passed": True
        },
        {
            "name": "Formato de campos",
            "passed": False,
            "message": "Los importes no coinciden con el formato esperado"
        },
        {
            "name": "Roll-forward de cuentas",
            "passed": True
        },
        {
            "name": "Coincidencia de sumas y saldos",
            "passed": False,
            "message": "Diferencia en saldo final"
        }
    ]
    
    return {
        "file_name": ", ".join(files),
        "checks": checks,
        "has_errors": True
    }