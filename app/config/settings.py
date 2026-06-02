"""
Configuration settings for the ARCA API application.
"""
from pathlib import Path
import os

# Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# JWT Settings
SECRET_KEY = "your-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ARCA Settings
CERT_PATH = Path("app/services/certificados/certificado.crt")
KEY_PATH = Path("app/services/certificados/MiClavePrivada.key")
WSAA_WSDL = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
WSFE_WSDL = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"

# Environment - Change to "prod" in production
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Use test services in development mode
if ENVIRONMENT == "dev":
    WSAA_WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL"
    WSFE_WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL" 