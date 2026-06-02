"""
Main FastAPI application file.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import ssl
import requests
from contextlib import asynccontextmanager

# Configuración SSL para solucionar problemas de conexión a ARCA
os.environ['PYTHONHTTPSVERIFY'] = '0'
# Configurar requests para ignorar verificación SSL
requests.packages.urllib3.disable_warnings()
# Configurar el nivel de seguridad SSL mínimo
try:
    # Establecer configuración SSL menos restrictiva
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception as e:
    print(f"SSL config error: {e}")

from app.models.database import engine, Base
from app.dependencies import templates
from app.routes import auth, users, afip

# Create database tables
Base.metadata.create_all(bind=engine)

# Create directory for ARCA tickets if it doesn't exist
os.makedirs("app/services/tickets", exist_ok=True)
os.makedirs("app/services/certificados", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    """
    # Startup code
    print("Starting up API...")
    yield
    # Shutdown code
    print("Shutting down API...")

app = FastAPI(
    title="ARCA Web Services API",
    description="API for interacting with ARCA Web Services",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(afip.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page route.
    """
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}