# backend/app/services/analyzers.py
from typing import List, Dict, Any
from collections import defaultdict

def generate_summary(processing_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un resumen de la actividad a partir de los resultados del procesamiento.
    """
    entries = processing_result.get("entries", [])
    
    # Resumen por usuario
    user_summary = defaultdict(lambda: {"entries": 0, "debit_amount": 0.0})
    
    for entry in entries:
        # Para este ejemplo, asignamos usuarios ficticios basados en el número de asiento
        # En un sistema real, extraeríamos el usuario real de los datos
        entry_num = int(entry["entry_number"])
        
        if entry_num % 3 == 0:
            user = "Pedro"
        elif entry_num % 3 == 1:
            user = "Juan"
        else:
            user = "María"
        
        # Incrementar contador de asientos
        user_summary[user]["entries"] += 1
        
        # Sumar importes debe
        total_debit = sum(line.get("debit", 0) for line in entry["lines"])
        user_summary[user]["debit_amount"] += total_debit
    
    # Convertir el diccionario en una lista para la respuesta
    activity_summary = [
        {
            "user": user,
            "entries": data["entries"],
            "debit_amount": round(data["debit_amount"], 2)
        }
        for user, data in user_summary.items()
    ]
    
    # Ordenar por cantidad de asientos (descendente)
    activity_summary.sort(key=lambda x: x["debit_amount"], reverse=True)
    
    return {
        "accounting_date_range": processing_result.get("accounting_date_range", ""),
        "registration_date_range": processing_result.get("registration_date_range", ""),
        "activity_summary": activity_summary
    }

def analyze_account_distribution(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analiza la distribución de cuentas en los asientos.
    """
    account_usage = defaultdict(int)
    
    for entry in entries:
        for line in entry.get("lines", []):
            account = line.get("account_name", "")
            if account:
                account_usage[account] += 1
    
    # Ordenar por frecuencia
    sorted_accounts = sorted(
        [{"account": acc, "usage": count} for acc, count in account_usage.items()],
        key=lambda x: x["usage"],
        reverse=True
    )
    
    return {
        "most_used_accounts": sorted_accounts[:10],
        "total_accounts": len(account_usage)
    }

def analyze_entry_balance(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analiza el balance de los asientos.
    """
    total_debit = 0
    total_credit = 0
    unbalanced_entries = []
    
    for entry in entries:
        entry_debit = sum(line.get("debit", 0) for line in entry.get("lines", []))
        entry_credit = sum(line.get("credit", 0) for line in entry.get("lines", []))
        
        total_debit += entry_debit
        total_credit += entry_credit
        
        if abs(entry_debit - entry_credit) > 0.01:
            unbalanced_entries.append({
                "entry_number": entry["entry_number"],
                "debit": entry_debit,
                "credit": entry_credit,
                "difference": entry_debit - entry_credit
            })
    
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "global_balance": total_debit - total_credit,
        "unbalanced_entries": unbalanced_entries,
        "balanced": len(unbalanced_entries) == 0
    }