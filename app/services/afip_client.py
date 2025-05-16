"""
Client service for interacting with AFIP Web Services.
"""
from datetime import datetime
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from zeep import Client
from zeep.exceptions import Fault
from typing import Dict, Optional, Tuple, Any, List

from app.config.settings import WSAA_WSDL, WSFE_WSDL
from app.services.ticket_access import get_access_ticket

class AfipError(Exception):
    """Custom exception for AFIP service errors."""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

async def get_client(service: str) -> Tuple[Client, Dict[str, str]]:
    """
    Get a configured SOAP client for the specified AFIP service.
    
    Args:
        service: Service ID (e.g., 'wsfe')
        
    Returns:
        Tuple containing the SOAP client and authentication data
        
    Raises:
        AfipError: If authentication fails or service is unsupported
    """
    # Get authentication ticket
    ticket_data = await get_access_ticket(service)
    
    if not ticket_data:
        raise AfipError("Failed to obtain AFIP authentication ticket")
    
    # Select the appropriate WSDL based on service
    wsdl_url = None
    if service == "wsfe":
        wsdl_url = WSFE_WSDL
    else:
        raise AfipError(f"Unsupported service: {service}")
    
    # Create client
    try:
        client = Client(wsdl_url)
        auth = {
            "Token": ticket_data["token"],
            "Sign": ticket_data["sign"],
            "Cuit": ticket_data["cuit"]
        }
        return client, auth
    except Exception as e:
        raise AfipError(f"Failed to create SOAP client: {str(e)}")

async def get_server_status(service: str = "wsfe") -> Dict[str, str]:
    """
    Check the status of the AFIP service.
    
    Args:
        service: Service ID to check
        
    Returns:
        Dictionary with status information
    """
    try:
        client, _ = await get_client(service)
        result = client.service.FEDummy()
        return {
            "appserver": getattr(result, "AppServer", "Unknown"),
            "dbserver": getattr(result, "DbServer", "Unknown"),
            "authserver": getattr(result, "AuthServer", "Unknown")
        }
    except Exception as e:
        raise AfipError(f"Failed to check server status: {str(e)}")

async def get_last_voucher_number(
    punto_venta: int, 
    tipo_comprobante: int, 
    service: str = "wsfe"
) -> int:
    """
    Get the last voucher number for the specified sales point and voucher type.
    
    Args:
        punto_venta: Sales point number
        tipo_comprobante: Voucher type code
        service: Service ID
        
    Returns:
        Last voucher number
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FECompUltimoAutorizado(
            Auth=auth,
            PtoVta=punto_venta,
            CbteTipo=tipo_comprobante
        )
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result.CbteNro
    except Fault as fault:
        raise AfipError(f"SOAP fault: {str(fault)}")
    except Exception as e:
        raise AfipError(f"Failed to get last voucher number: {str(e)}")

async def get_invoice_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available invoice types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with invoice types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposCbte(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get invoice types: {str(e)}")

async def get_concept_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available concept types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with concept types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposConcepto(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get concept types: {str(e)}")

async def get_document_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available document types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with document types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposDoc(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get document types: {str(e)}")

async def get_tax_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available tax types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with tax types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposIva(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get tax types: {str(e)}")

async def get_currency_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available currency types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with currency types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposMonedas(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get currency types: {str(e)}")

async def get_optional_types(service: str = "wsfe") -> Dict[str, Any]:
    """
    Get available optional data types from AFIP.
    
    Args:
        service: Service ID
        
    Returns:
        Dictionary with optional data types information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FEParamGetTiposOpcional(Auth=auth)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Exception as e:
        raise AfipError(f"Failed to get optional data types: {str(e)}")

async def create_invoice(
    invoice_data: Dict[str, Any],
    service: str = "wsfe"
) -> Dict[str, Any]:
    """
    Create an electronic invoice through AFIP.
    
    Args:
        invoice_data: Dictionary containing invoice data
        service: Service ID
        
    Returns:
        Dictionary with AFIP response
    """
    try:
        client, auth = await get_client(service)
        
        # Structure the request according to AFIP's specifications
        # This is a simplified example - adapt to your needs
        req = {
            'Auth': auth,
            'FeCAEReq': {
                'FeCabReq': {
                    'CantReg': 1,
                    'PtoVta': invoice_data['punto_venta'],
                    'CbteTipo': invoice_data['tipo_comprobante']
                },
                'FeDetReq': {
                    'FECAEDetRequest': [{
                        'Concepto': invoice_data['concepto'],
                        'DocTipo': invoice_data['doc_tipo'],
                        'DocNro': invoice_data['doc_nro'],
                        'CbteDesde': invoice_data['cbte_desde'],
                        'CbteHasta': invoice_data['cbte_hasta'],
                        'CbteFch': invoice_data['cbte_fecha'].replace('-', ''),
                        'ImpTotal': invoice_data['imp_total'],
                        'ImpTotConc': invoice_data.get('imp_tot_conc', 0),
                        'ImpNeto': invoice_data.get('imp_neto', 0),
                        'ImpOpEx': invoice_data.get('imp_op_ex', 0),
                        'ImpIVA': invoice_data.get('imp_iva', 0),
                        'ImpTrib': invoice_data.get('imp_trib', 0),
                        'MonId': invoice_data.get('moneda_id', 'PES'),
                        'MonCotiz': invoice_data.get('moneda_cotiz', 1),
                    }]
                }
            }
        }
        
        # Add IVA details if available
        if 'iva' in invoice_data and invoice_data['iva']:
            req['FeCAEReq']['FeDetReq']['FECAEDetRequest'][0]['Iva'] = {
                'AlicIva': [
                    {'Id': item['id'], 'BaseImp': item['base_imp'], 'Importe': item['importe']}
                    for item in invoice_data['iva']
                ]
            }
            
        # Add optional data if available
        if 'opcionales' in invoice_data and invoice_data['opcionales']:
            req['FeCAEReq']['FeDetReq']['FECAEDetRequest'][0]['Opcionales'] = {
                'Opcional': [
                    {'Id': item['id'], 'Valor': item['valor']}
                    for item in invoice_data['opcionales']
                ]
            }
            
        # Call AFIP web service
        result = client.service.FECAESolicitar(**req)
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Fault as fault:
        raise AfipError(f"SOAP fault: {str(fault)}")
    except Exception as e:
        raise AfipError(f"Failed to create invoice: {str(e)}")

async def get_invoice_info(
    punto_venta: int,
    tipo_comprobante: int,
    nro_comprobante: int,
    service: str = "wsfe"
) -> Dict[str, Any]:
    """
    Get information about a specific invoice.
    
    Args:
        punto_venta: Sales point number
        tipo_comprobante: Invoice type code
        nro_comprobante: Invoice number
        service: Service ID
        
    Returns:
        Dictionary with invoice information
    """
    try:
        client, auth = await get_client(service)
        result = client.service.FECompConsultar(
            Auth=auth,
            FeCompConsReq={
                'PtoVta': punto_venta,
                'CbteTipo': tipo_comprobante,
                'CbteNro': nro_comprobante
            }
        )
        
        if hasattr(result, "Errors") and result.Errors:
            error_msg = ", ".join(f"{error.Code}: {error.Msg}" for error in result.Errors)
            raise AfipError(f"AFIP error: {error_msg}")
            
        return result
    except Fault as fault:
        raise AfipError(f"SOAP fault: {str(fault)}")
    except Exception as e:
        raise AfipError(f"Failed to get invoice information: {str(e)}")

# Add more AFIP Web Services functions as needed 