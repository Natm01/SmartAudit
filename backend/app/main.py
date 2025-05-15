# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import uvicorn
import os
import tempfile
import shutil
import traceback
from datetime import datetime

# Debug output
print(f"Current working directory: {os.getcwd()}")
frontend_path = "../frontend/build"
print(f"Frontend build path exists: {os.path.exists(frontend_path)}")
try:
    print(f"Parent directory contents: {os.listdir('..')}")
    if os.path.exists("../frontend"):
        print(f"Frontend directory contents: {os.listdir('../frontend')}")
        if os.path.exists(frontend_path):
            print(f"Build directory contents: {os.listdir(frontend_path)}")
except Exception as e:
    print(f"Error exploring directories: {str(e)}")

from app.services.file_processor import process_libro_diario, process_sumas_saldos
from app.services.validators import validate_files
from app.services.analyzers import generate_summary
from app.schemas.libro_diario import FileUploadResponse, ValidationResult, ProcessResult

app = FastAPI(title="SmartAudit API", description="API para procesamiento de libros diarios contables")

# Single CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api")
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
    try:
        # Your existing code
        temp_dir = tempfile.mkdtemp()
        libro_paths = []
        sumas_paths = []
        
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
            "libro_diario_files": [{"name": file.filename, "size": 0} for file in libro_diario_files],
            "sumas_saldos_files": [{"name": file.filename, "size": 0} for file in sumas_saldos_files] if sumas_saldos_files else [],
            "temp_dir": temp_dir
        }
    
    except Exception as e:
        print(f"Error en upload_files: {str(e)}")
        traceback.print_exc()
        # Limpiar directorio en caso de error
        if 'temp_dir' in locals():
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
    # Your existing code
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
        print(f"Error en validate: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en la validación: {str(e)}")

@app.post("/api/process", response_model=ProcessResult)
async def process(
    temp_dir: str = Form(...),
    validation_id: str = Form(...)
):
    # Your existing code
    try:
        # Verificar que el directorio temporal existe
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Procesar los archivos de libro diario
        libro_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f)) and f.lower().endswith(('.txt', '.csv', '.xlsx', '.xls'))]
        
        if not libro_files:
            raise HTTPException(status_code=400, detail="No se encontraron archivos para procesar")
            
        # Aceptar cualquier ID de validación por ahora
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
                "entries": result["entries"][:10],  # Limitamos a 10 entradas para reducir tamaño
                "summary": summary["activity_summary"]
            }
        except Exception as e:
            print(f"Error de procesamiento: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error en el procesamiento de archivos: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error general en process: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")


@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(frontend_path, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"message": "Favicon not found"})

# Serve static files from the /static directory
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    full_path = os.path.join(frontend_path, "static", file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    return JSONResponse(status_code=404, content={"message": f"Static file {file_path} not found"})

# Fallback for React routes - MUST be the last route
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    # First try to serve the file directly if it exists
    direct_path = os.path.join(frontend_path, full_path)
    if os.path.exists(direct_path) and os.path.isfile(direct_path):
        return FileResponse(direct_path)
    
    # Otherwise fallback to index.html for client-side routing
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # If even index.html doesn't exist, return a helpful error
    return JSONResponse(
        status_code=404, 
        content={
            "message": "Frontend build not found. Make sure you've built your React app and the build directory exists.",
            "requested_path": full_path,
            "expected_dir": frontend_path
        }
    )

@app.on_event("shutdown")
async def cleanup():
    # Limpiar directorios temporales en el cierre
    # Este sería un lugar para implementar limpieza de archivos temporales
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)