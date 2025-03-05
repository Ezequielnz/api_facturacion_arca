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
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs7
from zeep import Client

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

# Ejecutar generación del TA
generar_ticket_acceso()

"""
def verificar_ticket():
    # Verifica si el Ticket de Acceso sigue siendo válido
    try:
        tree = etree.parse("loginTicketResponse.xml")
        expiration_time = tree.find(".//expirationTime").text
        exp_time = datetime.datetime.fromisoformat(expiration_time)

        if exp_time < datetime.datetime.now():
            print("El Ticket de Acceso ha expirado. Creando uno nuevo...")
            return generar_ticket_acceso()
        else:
            print("El Ticket de Acceso sigue siendo válido.")
            return True
    except Exception as e:
        print(f"Error verificando el Ticket de Acceso: {e}")
        return None
"""

