"""
Main FastAPI application file.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from app.models.database import engine, Base
from app.dependencies import templates
from app.routes import auth, users, afip

# Create database tables
Base.metadata.create_all(bind=engine)

# Create directory for AFIP tickets if it doesn't exist
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
    title="AFIP Web Services API",
    description="API for interacting with AFIP Web Services",
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