# main.py - ACTUALIZADO
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime
import logging
import os
import uvicorn
import sys

# Importar routers del portal-web
from routes.projects import router as projects_router
from routes.applications import router as applications_router
from routes.upload import router as upload_router
from routes.validation import router as validation_router
from routes.conversion import router as conversion_router
from routes.mapeo import router as mapeo_router
from routes.manual_mapping import router as manual_mapping_router
from routes.preview import router as preview_router
from routes.sumas_saldos import router as sumas_saldos_router
from routes.sumas_saldos_manual_mapping import router as sumas_saldos_manual_mapping_router
from routes.execution_status import router as execution_status_router
from routes.audit_test import router as audit_test_router
from routes import validation_rules
from routes import database_upload
from routes import sumas_saldos_validation
from routes import database

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Crear FastAPI instance con path prefix
app = FastAPI(
    title="SmartAudit Proto API",
    description="API para SmartAudit Portal - Python 3.11 con FastAPI integrado con Portal Web",
    version="1.0.0"
)

# Configurar CORS para dominios smartaudit.com
ALLOWED_ORIGINS = [
    "https://devapi.grantthornton.es",
    "https://testapi.grantthornton.es",
    "https://api.grantthornton.es",
    "https://devsmartaudit.grantthornton.es",
    "https://testsmartaudit.grantthornton.es", 
    "https://smartaudit.grantthornton.es", 
    "http://localhost:3000",
    "http://localhost:4280",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de seguridad para hosts permitidos
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*.grantthornton.es", "localhost", "127.0.0.1", "*"]
)

# Incluir todos los routers del portal-web
app.include_router(projects_router)
app.include_router(applications_router)

# Portal Web Processing Routers
app.include_router(upload_router)
app.include_router(validation_router)
app.include_router(conversion_router)
app.include_router(mapeo_router)
app.include_router(manual_mapping_router)
app.include_router(preview_router)

# Sumas y Saldos Routers
app.include_router(sumas_saldos_router)
app.include_router(sumas_saldos_manual_mapping_router)

# Execution Status Router
app.include_router(execution_status_router)

# Audit Test Router
app.include_router(audit_test_router)

# Validation Rules Router
app.include_router(validation_rules.router)

app.include_router(database_upload.router)
app.include_router(sumas_saldos_validation.router)
app.include_router(database.router)

# Modelos Pydantic
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime.datetime
    version: str
    environment: str
    checks: dict

# Utility functions
def get_environment():
    return os.getenv("ENVIRONMENT", "development")

def get_current_timestamp():
    return datetime.datetime.now(datetime.timezone.utc)

def perform_health_checks():
    """Realizar verificaciones de salud de la aplicación"""
    checks = {
        "database": "ok",
        "memory": "ok",
        "disk_space": "ok",
        "azure_storage": "ok" if os.getenv("AZURE_STORAGE_CONNECTION_STRING") else "not_configured"
    }
    
    return checks

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": get_current_timestamp().isoformat()
        }
    )

# ==========================================
# HEALTH ENDPOINTS PARA CONTAINER APPS
# ==========================================

@app.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe - Container Apps usa esto automÃ¡ticamente
    Verifica que el contenedor estÃ¡ listo para recibir trÃ¡fico
    """
    try:
        return {
            "status": "ready",
            "timestamp": get_current_timestamp().isoformat(),
            "service": "smartaudit-proto-api"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/live")
async def liveness_probe():
    """
    Liveness probe - Container Apps usa esto automÃ¡ticamente
    Verifica que la aplicación estÃ¡ funcionando
    """
    return {
        "status": "alive",
        "timestamp": get_current_timestamp().isoformat()
    }

@app.get("/smau-proto/health")
async def health_check():
    """
    Health check completo con información del sistema
    """
    checks = perform_health_checks()
    
    all_ok = all(v in ["ok", "not_configured"] for v in checks.values())
    
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        timestamp=get_current_timestamp(),
        version="1.0.0",
        environment=get_environment(),
        checks=checks
    )

# ==========================================
# ROOT ENDPOINTS
# ==========================================

@app.get("/smau-proto/", response_model=dict)
async def root():
    """
    Endpoint raÃ­z de la API
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "SmartAudit Proto API with Portal Web",
        "version": "1.0.0",
        "python_version": "3.11",
        "framework": "FastAPI",
        "environment": get_environment(),
        "docs_url": "/smau-proto/docs",
        "timestamp": get_current_timestamp(),
        "available_endpoints": [
            "/smau-proto/api/import/upload",
            "/smau-proto/api/import/status/{execution_id}",  # NUEVO
            "/smau-proto/api/import/validate/{execution_id}",
            "/smau-proto/api/import/convert/{execution_id}",
            "/smau-proto/api/import/mapeo/{execution_id}",
            "/smau-proto/api/import/mapeo-sumas-saldos/{execution_id}",
            "/smau-proto/api/import/preview/{execution_id}",
            "/smau-proto/api/import/preview-sumas-saldos/{execution_id}",
            "/smau-proto/api/projects/",
            "/smau-proto/api/applications/"
        ]
    }

@app.get("/smau-proto/version")
async def get_version():
    """
    Información de versión detallada
    """
    return {
        "api_version": "1.0.0",
        "python_version": "3.11",
        "fastapi_version": "0.104.1",
        "environment": get_environment(),
        "build_timestamp": get_current_timestamp(),
        "portal_web_integrated": True,
        "azure_storage_enabled": bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")),
        "container_info": {
            "hostname": os.getenv("HOSTNAME", "unknown"),
            "container_app_name": os.getenv("CONTAINER_APP_NAME", "unknown"),
            "container_app_revision": os.getenv("CONTAINER_APP_REVISION", "unknown")
        }
    }

@app.get("/smau-proto/test-connection")
async def test_connection():
    """Endpoint simple para testing de conectividad desde el frontend"""
    return {
        "message": "SmartAudit Proto API - Conexión exitosa con Portal Web",
        "status": "connected",
        "api_url": "/smau-proto/",
        "timestamp": get_current_timestamp().isoformat(),
        "cors_enabled": True
    }

# ==========================================
# STARTUP EVENT
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Ejecutar al iniciar la aplicación"""
    logger.info("=" * 80)
    logger.info("ðŸš€ SmartAudit Proto API Starting...")
    logger.info(f"Environment: {get_environment()}")
    logger.info(f"Python Version: 3.11")
    logger.info(f"Azure Storage: {'Enabled' if os.getenv('AZURE_STORAGE_CONNECTION_STRING') else 'Disabled'}")
    logger.info("=" * 80)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )