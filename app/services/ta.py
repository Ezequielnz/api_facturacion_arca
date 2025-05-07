#pylint: disable=import-error
import datetime
import base64
import sys
import shutil
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from zeep import Client
from lxml import etree
import glob
import os

CERT_PATH = "certificados/certificado.crt"
KEY_PATH = "certificados/MiClavePrivada.key"
WSAA_WSDL = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
SERVICE_ID = "wsfe"

def sign_tra(tra, cert_path, key_path):
    """Firma un TRA con PKCS7 y lo devuelve en formato Base64."""
    try:
        with open(key_path, "rb") as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())
        
        with open(cert_path, "rb") as cert_file:
            certificate = load_pem_x509_certificate(cert_file.read(), default_backend())

        # Firmar el XML con PKCS#7 y codificación DER
        signer = pkcs7.PKCS7SignatureBuilder().set_data(tra.encode()).add_signer(
            certificate, private_key, hashes.SHA256()
        )
        signed_der = signer.sign(
            options=[pkcs7.PKCS7Options.Binary], encoding=Encoding.DER
        )

        return base64.b64encode(signed_der).decode()
    except Exception as e:
        print(f"❌ Error firmando XML: {e}")
        return None

def generar_ticket_acceso():
    """Genera y firma un LoginTicketRequest para AFIP"""
    now = datetime.datetime.now()
    unique_id = now.strftime("%y%m%d%H%M")

    # Construcción del XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <loginTicketRequest>
        <header>
            <uniqueId>{unique_id}</uniqueId>
            <generationTime>{(now - datetime.timedelta(minutes=10)).isoformat()}</generationTime>
            <expirationTime>{(now + datetime.timedelta(hours=12)).isoformat()}</expirationTime>
        </header>
        <service>{SERVICE_ID}</service>
    </loginTicketRequest>"""

    # Firmar el XML
    signed_data = sign_tra(xml, CERT_PATH, KEY_PATH)
    if not signed_data:
        print("❌ Error al firmar el XML")
        return None
    
    # Enviar a WSAA
    return enviar_a_wsaa(signed_data, unique_id)

def enviar_a_wsaa(signed_data, unique_id):
    """Envía el LoginTicketRequest firmado a WSAA"""
    try:
        client = Client(WSAA_WSDL)
        response = client.service.loginCms(signed_data)
        
        # Guardar respuesta
        response_filename = f"{unique_id}-loginTicketResponse.xml"
        with open(response_filename, "w", encoding="ascii") as f:
            f.write(response)
        
        return response
    except Exception as e:
        print(f"❌ Error en WSAA: {e}")
        return None

def verificar_ticket():
    """Verifica si existe un Ticket de Acceso válido"""
    try:
        # Buscar el último archivo de respuesta generado
        response_files = glob.glob("*-loginTicketResponse.xml")
        if not response_files:
            print("No se encontró ningún Ticket de Acceso. Generando uno nuevo...")
            return generar_ticket_acceso()
            
        latest_file = max(response_files, key=os.path.getctime)
        
        # Parsear el XML
        tree = etree.parse(latest_file)
        expiration_time = tree.find(".//expirationTime").text
        exp_time = datetime.datetime.fromisoformat(expiration_time)
        
        # Asegurarnos de que el datetime.now() también sea timezone-aware
        now = datetime.datetime.now(exp_time.tzinfo)

        if exp_time < now:
            print("El Ticket de Acceso ha expirado. Creando uno nuevo...")
            return generar_ticket_acceso()
        else:
            print("El Ticket de Acceso sigue siendo válido.")
            with open(latest_file, "r", encoding="ascii") as f:
                return f.read()
    except Exception as e:
        print(f"Error verificando el Ticket de Acceso: {e}")
        return generar_ticket_acceso()

# Ejecutar verificación del TA antes de generar uno nuevo
verificar_ticket()
