# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import os
import tempfile
import shutil
from datetime import datetime

from app.services.file_processor import process_libro_diario, process_sumas_saldos
from app.services.validators import validate_files
from app.services.analyzers import generate_summary
from app.schemas.libro_diario import FileUploadResponse, ValidationResult, ProcessResult

app = FastAPI(title="SmartAudit API", description="API para procesamiento de libros diarios contables")

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SmartAudit API"}

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_files(
    project: str = Form(...),
    year: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    libro_diario_files: List[UploadFile] = File(...),
    sumas_saldos_files: Optional[List[UploadFile]] = File(None)
):
    # Crear directorio temporal para los archivos
    temp_dir = tempfile.mkdtemp()
    libro_paths = []
    sumas_paths = []
    
    try:
        # Guardar archivos de libro diario
        for file in libro_diario_files:
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            libro_paths.append(temp_file_path)
        
        # Guardar archivos de sumas y saldos si existen
        if sumas_saldos_files:
            for file in sumas_saldos_files:
                temp_file_path = os.path.join(temp_dir, file.filename)
                with open(temp_file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                sumas_paths.append(temp_file_path)
        
        # Devolver información de los archivos cargados
        return {
            "project": project,
            "year": year,
            "date_range": f"{start_date} - {end_date}",
            "libro_diario_files": [{"name": file.filename, "size": file.size} for file in libro_diario_files],
            "sumas_saldos_files": [{"name": file.filename, "size": file.size} for file in sumas_saldos_files] if sumas_saldos_files else [],
            "temp_dir": temp_dir
        }
    
    except Exception as e:
        # Limpiar directorio en caso de error
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {str(e)}")

@app.post("/api/validate", response_model=ValidationResult)
async def validate(
    temp_dir: str = Form(...),
    project: str = Form(...),
    year: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    try:
        # Validar que el directorio temporal existe
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Obtener archivos en el directorio
        libro_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        if not libro_files:
            raise HTTPException(status_code=400, detail="No se encontraron archivos")
        
        # Validar los archivos
        validation_results = validate_files(temp_dir, libro_files, start_date, end_date)
        
        return validation_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la validación: {str(e)}")

@app.post("/api/process", response_model=ProcessResult)
async def process(
    temp_dir: str = Form(...),
    validation_id: str = Form(...)
):
    try:
        # Verificar que el directorio temporal existe
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Procesar los archivos de libro diario
        libro_files = [f for f in os.listdir(temp_dir) if f.lower().endswith(('.txt', '.csv', '.xlsx', '.xls'))]
        
        # Simplificar la validación del ID - aceptar cualquier ID por ahora
        # Para producción, deberías verificar que el ID existe en una base de datos o cache
        # En lugar de una validación estricta, vamos a aceptar cualquier ID no vacío
        if not validation_id:
            raise HTTPException(status_code=400, detail="ID de validación vacío")
        
        # Procesar los archivos
        try:
            result = process_libro_diario(temp_dir, libro_files)
            
            # Generar resumen
            summary = generate_summary(result)
            
            return {
                "accounting_date_range": summary["accounting_date_range"],
                "registration_date_range": summary["registration_date_range"],
                "entries": result["entries"][:10],  # Limitamos a 10 entradas para evitar respuestas demasiado grandes
                "summary": summary["activity_summary"]
            }
        except Exception as e:
            print(f"Error de procesamiento: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error en el procesamiento de archivos: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error general: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")
    

@app.on_event("shutdown")
async def cleanup():
    # Limpiar directorios temporales en el cierre
    # Este sería un lugar para implementar limpieza de archivos temporales
    pass

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)