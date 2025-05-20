# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Path
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

from app.services.file_processor import process_libro_diario, process_sumas_saldos, parse_sumas_saldos_excel
from app.services.validators import validate_files
from app.services.analyzers import generate_summary
from app.schemas.libro_diario import FileUploadResponse, ValidationResult, ProcessResult

app = FastAPI(title="SmartAudit API", description="API para procesamiento de libros diarios contables")

# CORS configuration
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
    try:
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Obtener archivos en el directorio
        all_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        if not all_files:
            raise HTTPException(status_code=400, detail="No se encontraron archivos")
        
        # Validar los archivos
        validation_results = validate_files(temp_dir, all_files, start_date, end_date)
        
        return validation_results
    
    except Exception as e:
        print(f"Error en validate: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en la validación: {str(e)}")

@app.get("/api/preview/{temp_dir}")
async def get_preview_data(
    temp_dir: str = Path(...),
    file_type: str = "libro"
):
    """
    Obtiene datos de previsualización de los archivos procesados.
    """
    try:
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Obtener archivos
        all_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        
        if file_type == "libro":
            # Separar archivos de libro diario
            libro_files = []
            for file in all_files:
                if not any(keyword in file.lower() for keyword in ['suma', 'saldo', 'balance', 'mayor']):
                    libro_files.append(file)
            
            if libro_files:
                try:
                    result = process_libro_diario(temp_dir, libro_files)
                    return {
                        "entries": result["entries"][:20],  # Primeros 20 para previsualización
                        "total": len(result["entries"]),
                        "accounting_date_range": result.get("accounting_date_range", ""),
                        "registration_date_range": result.get("registration_date_range", "")
                    }
                except Exception as e:
                    print(f"Error procesando libro diario para previsualización: {str(e)}")
                    return {"entries": [], "total": 0, "error": str(e)}
            else:
                return {"entries": [], "total": 0}
                
        elif file_type == "sumas":
            # Separar archivos de sumas y saldos
            sumas_files = []
            for file in all_files:
                if any(keyword in file.lower() for keyword in ['suma', 'saldo', 'balance', 'mayor']) or file.lower().endswith(('.xlsx', '.xls')):
                    sumas_files.append(file)
            
            if sumas_files:
                try:
                    result = process_sumas_saldos(temp_dir, sumas_files)
                    return {
                        "records": result["records"][:30],  # Primeros 30 para previsualización
                        "total": len(result["records"]),
                        "total_debe": result.get("total_debe", 0),
                        "total_haber": result.get("total_haber", 0),
                        "total_saldo": result.get("total_saldo", 0)
                    }
                except Exception as e:
                    print(f"Error procesando sumas y saldos para previsualización: {str(e)}")
                    return {"records": [], "total": 0, "error": str(e)}
            else:
                return {"records": [], "total": 0}
        
        else:
            raise HTTPException(status_code=400, detail="Tipo de archivo no válido")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en get_preview_data: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de previsualización: {str(e)}")

@app.post("/api/process", response_model=ProcessResult)
async def process(
    temp_dir: str = Form(...),
    validation_id: str = Form(...)
):
    try:
        if not os.path.exists(temp_dir):
            raise HTTPException(status_code=400, detail="El directorio temporal no existe")
        
        # Separar archivos por tipo
        all_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        
        libro_files = []
        sumas_files = []
        
        for file in all_files:
            if any(keyword in file.lower() for keyword in ['suma', 'saldo', 'balance', 'mayor']) or file.lower().endswith(('.xlsx', '.xls')):
                # Verificar si realmente es un archivo de sumas y saldos por contenido
                try:
                    if file.lower().endswith(('.xlsx', '.xls')):
                        import openpyxl
                        file_path = os.path.join(temp_dir, file)
                        workbook = openpyxl.load_workbook(file_path, data_only=True)
                        worksheet = workbook.active
                        
                        # Buscar headers típicos de sumas y saldos
                        is_sumas_saldos = False
                        for row in worksheet.iter_rows(max_row=10, values_only=True):
                            if row and any(cell and any(keyword in str(cell).lower() for keyword in ['cta.mayor', 'saldo', 'arrastre']) for cell in row):
                                is_sumas_saldos = True
                                break
                        
                        if is_sumas_saldos:
                            sumas_files.append(file)
                        else:
                            libro_files.append(file)
                    else:
                        sumas_files.append(file)
                except:
                    libro_files.append(file)
            else:
                libro_files.append(file)
        
        if not libro_files:
            raise HTTPException(status_code=400, detail="No se encontraron archivos de libro diario para procesar")
            
        if not validation_id:
            raise HTTPException(status_code=400, detail="ID de validación vacío")
        
        # Procesar archivos de libro diario
        try:
            libro_result = process_libro_diario(temp_dir, libro_files)
            
            # Procesar archivos de sumas y saldos si existen
            sumas_result = None
            if sumas_files:
                try:
                    sumas_result = process_sumas_saldos(temp_dir, sumas_files)
                except Exception as e:
                    print(f"Error procesando sumas y saldos: {str(e)}")
            
            # Generar resumen
            summary = generate_summary(libro_result)
            
            return {
                "accounting_date_range": summary["accounting_date_range"],
                "registration_date_range": summary["registration_date_range"],
                "entries": libro_result["entries"][:10],  # Limitamos a 10 entradas
                "summary": summary["activity_summary"],
                "sumas_saldos_summary": {
                    "total_records": len(sumas_result["records"]) if sumas_result else 0,
                    "total_balance": sumas_result["total_saldo"] if sumas_result else 0
                } if sumas_result else None
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

@app.delete("/api/cleanup/{temp_dir}")
async def cleanup_temp_files(temp_dir: str = Path(...)):
    """
    Limpia archivos temporales.
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return {"message": "Archivos temporales eliminados correctamente"}
    except Exception as e:
        print(f"Error en cleanup: {str(e)}")
        return {"message": f"Error al eliminar archivos temporales: {str(e)}"}

@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(frontend_path, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"message": "Favicon not found"})

@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    full_path = os.path.join(frontend_path, "static", file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    return JSONResponse(status_code=404, content={"message": f"Static file {file_path} not found"})

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
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)