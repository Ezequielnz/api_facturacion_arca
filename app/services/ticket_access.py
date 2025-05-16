"""
Service for handling AFIP authentication tickets (TA).
"""
import base64
import datetime
import glob
import os
from pathlib import Path
from typing import Dict, Optional, Any
from lxml import etree
from zeep import Client
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs7

from app.config.settings import CERT_PATH, KEY_PATH, WSAA_WSDL

# Cache for tickets to avoid unnecessary WSAA calls
ticket_cache: Dict[str, Dict[str, Any]] = {}

async def sign_tra(tra: str, cert_path: Path, key_path: Path) -> Optional[str]:
    """
    Sign a TRA with PKCS7 and return it in Base64 format.
    
    Args:
        tra: The XML TRA to sign
        cert_path: Path to the certificate file
        key_path: Path to the private key file
        
    Returns:
        Base64 encoded signed data or None if there was an error
    """
    try:
        with open(key_path, "rb") as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())
        
        with open(cert_path, "rb") as cert_file:
            certificate = load_pem_x509_certificate(cert_file.read(), default_backend())

        # Sign the XML with PKCS#7 and DER encoding
        signer = pkcs7.PKCS7SignatureBuilder().set_data(tra.encode()).add_signer(
            certificate, private_key, hashes.SHA256()
        )
        signed_der = signer.sign(
            options=[pkcs7.PKCS7Options.Binary], encoding=Encoding.DER
        )

        return base64.b64encode(signed_der).decode()
    except Exception as e:
        print(f"Error signing XML: {e}")
        return None

async def create_login_ticket(service: str) -> str:
    """
    Create a login ticket request XML for AFIP.
    
    Args:
        service: Service ID (e.g., 'wsfe')
        
    Returns:
        XML login ticket request
    """
    now = datetime.datetime.now()
    unique_id = now.strftime("%y%m%d%H%M")
    
    # Build the XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <loginTicketRequest>
        <header>
            <uniqueId>{unique_id}</uniqueId>
            <generationTime>{(now - datetime.timedelta(minutes=10)).isoformat()}</generationTime>
            <expirationTime>{(now + datetime.timedelta(hours=12)).isoformat()}</expirationTime>
        </header>
        <service>{service}</service>
    </loginTicketRequest>"""
    
    return xml

async def send_ticket_request(signed_data: str) -> Optional[str]:
    """
    Send a signed login ticket request to WSAA.
    
    Args:
        signed_data: Base64 encoded signed request
        
    Returns:
        XML response from WSAA or None if there was an error
    """
    try:
        client = Client(WSAA_WSDL)
        response = client.service.loginCms(signed_data)
        
        # Create directory if it doesn't exist
        os.makedirs("app/services/tickets", exist_ok=True)
        
        # Save response to file
        now = datetime.datetime.now()
        unique_id = now.strftime("%y%m%d%H%M")
        response_filename = f"app/services/tickets/{unique_id}-loginTicketResponse.xml"
        
        with open(response_filename, "w", encoding="utf-8") as f:
            f.write(response)
        
        return response
    except Exception as e:
        print(f"Error in WSAA call: {e}")
        return None

async def parse_ticket_response(response: str) -> Dict[str, str]:
    """
    Parse the login ticket response XML.
    
    Args:
        response: XML response from WSAA
        
    Returns:
        Dictionary with token, sign, and expiration
    """
    try:
        root = etree.fromstring(response.encode('utf-8'))
        
        # Extract data
        token = root.find(".//token").text
        sign = root.find(".//sign").text
        expiration = root.find(".//expirationTime").text
        generation = root.find(".//generationTime").text
        
        return {
            "token": token,
            "sign": sign,
            "expiration": expiration,
            "generation": generation
        }
    except Exception as e:
        print(f"Error parsing ticket response: {e}")
        return {}

async def check_ticket_validity(service: str) -> Optional[Dict[str, str]]:
    """
    Check if a valid ticket exists for the specified service.
    
    Args:
        service: Service ID (e.g., 'wsfe')
        
    Returns:
        Dictionary with token and sign or None if no valid ticket exists
    """
    # Check in-memory cache first
    if service in ticket_cache:
        ticket = ticket_cache[service]
        expiration = datetime.datetime.fromisoformat(ticket["expiration"])
        now = datetime.datetime.now(expiration.tzinfo if expiration.tzinfo else None)
        
        if expiration > now:
            return ticket
    
    # Check for saved ticket files
    try:
        ticket_dir = Path("app/services/tickets")
        if not ticket_dir.exists():
            return None
            
        response_files = list(ticket_dir.glob("*-loginTicketResponse.xml"))
        if not response_files:
            return None
            
        # Find the most recent file
        latest_file = max(response_files, key=os.path.getctime)
        
        # Parse the XML
        with open(latest_file, "r", encoding="utf-8") as f:
            response = f.read()
            
        # Parse the ticket
        ticket_data = await parse_ticket_response(response)
        
        # Check expiration
        if not ticket_data or "expiration" not in ticket_data:
            return None
            
        expiration = datetime.datetime.fromisoformat(ticket_data["expiration"])
        now = datetime.datetime.now(expiration.tzinfo if expiration.tzinfo else None)
        
        if expiration > now:
            # Add to cache
            ticket_cache[service] = ticket_data
            return ticket_data
            
        return None
    except Exception as e:
        print(f"Error checking ticket validity: {e}")
        return None

async def get_access_ticket(service: str, cuit: str = None) -> Optional[Dict[str, str]]:
    """
    Get a valid access ticket for the specified AFIP service.
    If no valid ticket exists, create a new one.
    
    Args:
        service: Service ID (e.g., 'wsfe')
        cuit: CUIT number (optional, can be set in the environment)
        
    Returns:
        Dictionary with token, sign and cuit or None if there was an error
    """
    # Check if a valid ticket exists
    ticket = await check_ticket_validity(service)
    if ticket:
        # Add CUIT to ticket data
        if cuit:
            ticket["cuit"] = cuit
        elif "AFIP_CUIT" in os.environ:
            ticket["cuit"] = os.environ["AFIP_CUIT"]
        return ticket
    
    # Create a new ticket
    try:
        # Create login ticket request
        tra = await create_login_ticket(service)
        
        # Sign the request
        signed_data = await sign_tra(tra, CERT_PATH, KEY_PATH)
        if not signed_data:
            return None
        
        # Send to WSAA
        response = await send_ticket_request(signed_data)
        if not response:
            return None
        
        # Parse response
        ticket_data = await parse_ticket_response(response)
        
        # Add to cache
        ticket_cache[service] = ticket_data
        
        # Add CUIT to ticket data
        if cuit:
            ticket_data["cuit"] = cuit
        elif "AFIP_CUIT" in os.environ:
            ticket_data["cuit"] = os.environ["AFIP_CUIT"]
            
        return ticket_data
    except Exception as e:
        print(f"Error getting access ticket: {e}")
        return None 