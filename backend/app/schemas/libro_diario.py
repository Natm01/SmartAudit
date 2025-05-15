# backend/app/schemas/libro_diario.py
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class FileInfo(BaseModel):
    name: str
    size: int

class FileUploadResponse(BaseModel):
    project: str
    year: str
    date_range: str
    libro_diario_files: List[FileInfo]
    sumas_saldos_files: List[FileInfo]
    temp_dir: str

class ValidationCheck(BaseModel):
    name: str
    passed: bool
    message: Optional[str] = None

class FileValidation(BaseModel):
    file_name: str
    checks: List[ValidationCheck]
    has_errors: bool

class ValidationResult(BaseModel):
    validation_id: str
    libro_diario_validation: FileValidation
    sumas_saldos_validation: Optional[FileValidation] = None
    has_errors: bool

class AccountingEntry(BaseModel):
    entry_number: str
    document_number: str
    accounting_date: str
    doc_date: str
    header_text: str
    lines: List[Dict[str, Any]]

class ActivitySummary(BaseModel):
    user: str
    entries: int
    debit_amount: float

class ProcessResult(BaseModel):
    accounting_date_range: str
    registration_date_range: str
    entries: List[AccountingEntry]
    summary: List[ActivitySummary]