"""
AFIP Web Services endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import ssl
import requests

from app.models.database import User
from app.services.afip_client import (
    get_server_status, 
    get_last_voucher_number, 
    get_invoice_types,
    get_concept_types,
    get_document_types,
    get_tax_types,
    get_currency_types,
    get_optional_types,
    create_invoice,
    get_invoice_info,
    AfipError,
    get_access_ticket
)
from app.models.schemas import AfipTicketRequest, AfipTicketResponse
from app.dependencies import get_current_user, templates
from app.config.settings import CERT_PATH, KEY_PATH, ENVIRONMENT, WSAA_WSDL, WSFE_WSDL

router = APIRouter(
    prefix="/api/afip",
    tags=["afip"]
)

# Ruta para mostrar el formulario de creación de facturas
@router.get("/invoice/create-form", response_class=HTMLResponse, tags=["ui"])
async def invoice_create_form(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Display the invoice creation form.
    """
    return templates.TemplateResponse("create_invoice.html", {
        "request": request,
        "user": current_user
    })

@router.get("/status", summary="Check AFIP server status")
async def check_status(
    service: str = "wsfe",
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Check the status of AFIP's servers.
    
    Args:
        service: AFIP service to check (default: wsfe)
        
    Returns:
        Dictionary with status information for each server component
    """
    try:
        return await get_server_status(service)
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/invoice/last-number/{punto_venta}/{tipo_comprobante}",
    summary="Get last invoice number"
)
async def last_invoice_number(
    punto_venta: int,
    tipo_comprobante: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, int]:
    """
    Get the last authorized invoice number for a specific sales point and invoice type.
    
    Args:
        punto_venta: Sales point number
        tipo_comprobante: Invoice type code
        
    Returns:
        Dictionary with the last invoice number
    """
    try:
        last_number = await get_last_voucher_number(
            punto_venta=punto_venta,
            tipo_comprobante=tipo_comprobante
        )
        return {"last_number": last_number}
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/invoice-types",
    summary="Get available invoice types"
)
async def invoice_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available invoice types from AFIP.
    
    Returns:
        Dictionary with invoice types information
    """
    try:
        return await get_invoice_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/concept-types",
    summary="Get available concept types"
)
async def concept_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available concept types from AFIP.
    
    Returns:
        Dictionary with concept types information
    """
    try:
        return await get_concept_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/document-types",
    summary="Get available document types"
)
async def document_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available document types from AFIP.
    
    Returns:
        Dictionary with document types information
    """
    try:
        return await get_document_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/tax-types",
    summary="Get available tax types"
)
async def tax_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available tax types from AFIP.
    
    Returns:
        Dictionary with tax types information
    """
    try:
        return await get_tax_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/currency-types",
    summary="Get available currency types"
)
async def currency_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available currency types from AFIP.
    
    Returns:
        Dictionary with currency types information
    """
    try:
        return await get_currency_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.get(
    "/params/optional-types",
    summary="Get available optional data types"
)
async def optional_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available optional data types from AFIP.
    
    Returns:
        Dictionary with optional data types information
    """
    try:
        return await get_optional_types()
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.post(
    "/invoice/create",
    summary="Create an electronic invoice"
)
async def create_electronic_invoice(
    invoice_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create an electronic invoice through AFIP.
    
    Args:
        invoice_data: Dictionary containing invoice data
        
    Returns:
        Dictionary with AFIP response including CAE
    """
    try:
        # Verificar certificados
        cert_exists = CERT_PATH.exists()
        key_exists = KEY_PATH.exists()
        
        if not cert_exists or not key_exists:
            error_msg = []
            if not cert_exists:
                error_msg.append(f"Certificate file not found at {CERT_PATH}")
            if not key_exists:
                error_msg.append(f"Private key file not found at {KEY_PATH}")
                
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Certificate error: {', '.join(error_msg)}"
            )
        
        # Validate required fields
        required_fields = ["punto_venta", "tipo_comprobante", "concepto", "doc_tipo", "doc_nro"]
        missing_fields = [field for field in required_fields if field not in invoice_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Agregar el CUIT del emisor al invoice_data si no está proporcionado
        if "cuit_emisor" not in invoice_data:
            invoice_data["cuit_emisor"] = current_user.cuit
            print(f"Using CUIT from current user: {current_user.cuit}")
        
        # Obtener el próximo número de comprobante si no se proporciona
        if invoice_data.get("cbte_desde", 0) == 0:
            try:
                last_number = await get_last_voucher_number(
                    punto_venta=invoice_data["punto_venta"],
                    tipo_comprobante=invoice_data["tipo_comprobante"]
                )
                invoice_data["cbte_desde"] = last_number + 1
                invoice_data["cbte_hasta"] = last_number + 1
                print(f"Using invoice number: {invoice_data['cbte_desde']}")
            except Exception as e:
                print(f"Error getting last invoice number: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error getting last invoice number: {str(e)}"
                )
        
        # Ensure cbte_hasta is set if only cbte_desde was provided
        if "cbte_desde" in invoice_data and "cbte_hasta" not in invoice_data:
            invoice_data["cbte_hasta"] = invoice_data["cbte_desde"]
        
        # Asegurar que la fecha esté en el formato correcto (AAAAMMDD)
        if "cbte_fecha" in invoice_data:
            # Si la fecha está en formato ISO (YYYY-MM-DD), convertirla a AAAAMMDD
            if "-" in invoice_data["cbte_fecha"]:
                invoice_data["cbte_fecha"] = invoice_data["cbte_fecha"].replace("-", "")
            # Si la fecha no tiene el formato adecuado, intentar convertirla
            elif len(invoice_data["cbte_fecha"]) != 8:
                try:
                    date_obj = datetime.strptime(invoice_data["cbte_fecha"], "%Y-%m-%d")
                    invoice_data["cbte_fecha"] = date_obj.strftime("%Y%m%d")
                except Exception as e:
                    print(f"Error converting date: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid date format: {invoice_data['cbte_fecha']}. Use YYYY-MM-DD format."
                    )
        else:
            # Si no se proporciona fecha, usar la fecha actual
            invoice_data["cbte_fecha"] = datetime.now().strftime("%Y%m%d")
            
        # Format service dates if present (for service invoices)
        for date_field in ["fch_serv_desde", "fch_serv_hasta", "fch_vto_pago"]:
            if date_field in invoice_data and invoice_data[date_field]:
                if "-" in invoice_data[date_field]:
                    invoice_data[date_field] = invoice_data[date_field].replace("-", "")
                elif len(invoice_data[date_field]) != 8 and invoice_data[date_field]:
                    try:
                        date_obj = datetime.strptime(invoice_data[date_field], "%Y-%m-%d")
                        invoice_data[date_field] = date_obj.strftime("%Y%m%d")
                    except Exception as e:
                        print(f"Error converting {date_field}: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid date format for {date_field}: {invoice_data[date_field]}. Use YYYY-MM-DD format."
                        )
        
        # Verificar si se proporcionaron alícuotas de IVA
        if "iva" in invoice_data and invoice_data["iva"]:
            # Verificar los campos requeridos en cada alícuota de IVA
            for idx, alicuota in enumerate(invoice_data["iva"]):
                if "id" not in alicuota or "base_imp" not in alicuota or "importe" not in alicuota:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required fields in IVA entry {idx}: Each entry must have 'id', 'base_imp', and 'importe'"
                    )
            
            # Calcular el importe total de IVA si no está establecido
            total_iva = sum(float(item.get("importe", 0)) for item in invoice_data["iva"])
            invoice_data["imp_iva"] = total_iva
        
        # Ensure numerical fields are properly formatted as numbers
        for field in ["imp_total", "imp_neto", "imp_iva", "imp_trib", "imp_tot_conc", "imp_op_ex"]:
            if field in invoice_data and invoice_data[field]:
                try:
                    invoice_data[field] = float(invoice_data[field])
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid value for {field}: {invoice_data[field]}. Must be a number."
                    )
        
        # Calcular el importe total si no está establecido
        if "imp_total" not in invoice_data:
            imp_neto = float(invoice_data.get("imp_neto", 0))
            imp_iva = float(invoice_data.get("imp_iva", 0))
            imp_tot_conc = float(invoice_data.get("imp_tot_conc", 0))
            imp_op_ex = float(invoice_data.get("imp_op_ex", 0))
            imp_trib = float(invoice_data.get("imp_trib", 0))
            
            invoice_data["imp_total"] = imp_neto + imp_iva + imp_tot_conc + imp_op_ex + imp_trib
            print(f"Calculated total amount: {invoice_data['imp_total']}")
        
        # Invocar el servicio de AFIP para crear la factura
        result = await create_invoice(invoice_data)
        
        # Extract CAE and related data
        cae = getattr(result.FeDetResp.FECAEDetResponse[0], "CAE", "")
        cae_expiration = getattr(result.FeDetResp.FECAEDetResponse[0], "CAEFchVto", "")
        result_status = getattr(result.FeDetResp.FECAEDetResponse[0], "Resultado", "")
        
        # Format dates for response
        invoice_date = getattr(result.FeDetResp.FECAEDetResponse[0], "CbteFch", "")
        if invoice_date and len(invoice_date) == 8:
            formatted_date = f"{invoice_date[0:4]}-{invoice_date[4:6]}-{invoice_date[6:8]}"
        else:
            formatted_date = invoice_date
            
        cae_exp_date = cae_expiration
        if cae_exp_date and len(cae_exp_date) == 8:
            formatted_exp_date = f"{cae_exp_date[0:4]}-{cae_exp_date[4:6]}-{cae_exp_date[6:8]}"
        else:
            formatted_exp_date = cae_exp_date
        
        # Formatear la respuesta para el cliente
        formatted_response = {
            "result": result_status,
            "success": result_status == "A",
            "invoice_data": {
                "invoice_type": invoice_data["tipo_comprobante"],
                "invoice_point_of_sale": invoice_data["punto_venta"],
                "invoice_number": getattr(result.FeDetResp.FECAEDetResponse[0], "CbteDesde", 0),
                "invoice_date": formatted_date
            },
            "cae_data": {
                "cae": cae,
                "cae_expiration": formatted_exp_date
            },
            "amounts": {
                "total": invoice_data["imp_total"],
                "net": invoice_data.get("imp_neto", 0),
                "tax": invoice_data.get("imp_iva", 0)
            }
        }
        
        # If debug mode, include original response
        if ENVIRONMENT == "dev":
            formatted_response["original_response"] = str(result)
        
        return formatted_response
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error creating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get(
    "/invoice/info/{punto_venta}/{tipo_comprobante}/{nro_comprobante}",
    summary="Get information about a specific invoice"
)
async def invoice_info(
    punto_venta: int,
    tipo_comprobante: int,
    nro_comprobante: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about a specific invoice.
    
    Args:
        punto_venta: Sales point number
        tipo_comprobante: Invoice type code
        nro_comprobante: Invoice number
        
    Returns:
        Dictionary with invoice information
    """
    try:
        result = await get_invoice_info(
            punto_venta=punto_venta,
            tipo_comprobante=tipo_comprobante,
            nro_comprobante=nro_comprobante
        )
        return result
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )

@router.post(
    "/invoice/generate-example",
    summary="Generate a simple example invoice"
)
async def generate_example_invoice(
    data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate a simple example invoice with basic data.
    
    Args:
        data: Dictionary containing minimal invoice data
        
    Returns:
        Dictionary with AFIP response
    """
    try:
        # Validate the minimal required data
        required_fields = ["punto_venta", "tipo_comprobante", "doc_tipo", "doc_nro", "importe"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Create the complete invoice data structure
        from datetime import datetime
        
        # Current date in YYYYMMDD format
        current_date = datetime.now().strftime("%Y%m%d")
        
        # Try to get the last invoice number
        try:
            last_number = await get_last_voucher_number(
                punto_venta=data["punto_venta"],
                tipo_comprobante=data["tipo_comprobante"]
            )
            next_number = last_number + 1
        except Exception as e:
            print(f"Error getting last invoice number: {str(e)}")
            # Use 1 as fallback number
            next_number = 1
        
        # Calculate tax based on invoice type (if Factura A, must include tax separately)
        imp_total = float(data["importe"])
        
        # For Factura A, importe is net amount and we add tax
        if str(data["tipo_comprobante"]) == "1":  # Factura A
            imp_neto = imp_total
            # Default to 21% tax
            imp_iva = round(imp_total * 0.21, 2)
            imp_total = imp_neto + imp_iva
            
            # Add IVA detail (21%)
            iva = [
                {
                    "id": 5,  # 21%
                    "base_imp": imp_neto,
                    "importe": imp_iva
                }
            ]
        else:  # For Factura B/C, importe includes tax
            # For Factura B, we calculate net amount by removing tax
            imp_iva = round(imp_total - (imp_total / 1.21), 2)
            imp_neto = imp_total - imp_iva
            
            # Add IVA detail for Factura B
            if str(data["tipo_comprobante"]) == "6":  # Factura B
                iva = [
                    {
                        "id": 5,  # 21%
                        "base_imp": imp_neto,
                        "importe": imp_iva
                    }
                ]
            else:
                iva = []
        
        # Build the complete invoice data
        invoice_data = {
            "punto_venta": data["punto_venta"],
            "tipo_comprobante": data["tipo_comprobante"],
            "cbte_desde": next_number,
            "cbte_hasta": next_number,
            "concepto": data.get("concepto", 1),  # Default to products
            "doc_tipo": data["doc_tipo"],
            "doc_nro": data["doc_nro"],
            "cbte_fecha": current_date,
            "imp_total": imp_total,
            "imp_neto": imp_neto,
            "imp_iva": imp_iva,
            "imp_trib": 0,
            "imp_op_ex": 0,
            "imp_tot_conc": 0,
            "moneda_id": "PES",
            "moneda_cotiz": 1
        }
        
        # Add IVA details if present
        if iva:
            invoice_data["iva"] = iva
        
        # Add optional description if provided
        if "descripcion" in data:
            invoice_data["descripcion"] = data["descripcion"]
        
        # Add service dates if it's a service invoice
        if data.get("concepto") in [2, 3]:  # Services or Products and Services
            # Service period: current month
            service_start = datetime.now().replace(day=1).strftime("%Y%m%d")
            service_end = current_date
            payment_due = (datetime.now().replace(day=1) + timedelta(days=30)).strftime("%Y%m%d")
            
            invoice_data["fch_serv_desde"] = service_start
            invoice_data["fch_serv_hasta"] = service_end
            invoice_data["fch_vto_pago"] = payment_due
        
        # Call AFIP to create the invoice
        result = await create_invoice(invoice_data)
        
        # Extract CAE and related data
        cae = getattr(result.FeDetResp.FECAEDetResponse[0], "CAE", "")
        cae_expiration = getattr(result.FeDetResp.FECAEDetResponse[0], "CAEFchVto", "")
        result_status = getattr(result.FeDetResp.FECAEDetResponse[0], "Resultado", "")
        
        # Format dates for response
        invoice_date = getattr(result.FeDetResp.FECAEDetResponse[0], "CbteFch", "")
        if invoice_date and len(invoice_date) == 8:
            formatted_date = f"{invoice_date[0:4]}-{invoice_date[4:6]}-{invoice_date[6:8]}"
        else:
            formatted_date = invoice_date
            
        cae_exp_date = cae_expiration
        if cae_exp_date and len(cae_exp_date) == 8:
            formatted_exp_date = f"{cae_exp_date[0:4]}-{cae_exp_date[4:6]}-{cae_exp_date[6:8]}"
        else:
            formatted_exp_date = cae_exp_date
        
        # Format the response for the client
        formatted_response = {
            "result": result_status,
            "success": result_status == "A",
            "invoice_data": {
                "invoice_type": invoice_data["tipo_comprobante"],
                "invoice_type_desc": "Factura A" if str(invoice_data["tipo_comprobante"]) == "1" else 
                                    "Factura B" if str(invoice_data["tipo_comprobante"]) == "6" else 
                                    "Factura C" if str(invoice_data["tipo_comprobante"]) == "11" else 
                                    f"Tipo {invoice_data['tipo_comprobante']}",
                "invoice_point_of_sale": invoice_data["punto_venta"],
                "invoice_number": getattr(result.FeDetResp.FECAEDetResponse[0], "CbteDesde", 0),
                "invoice_date": formatted_date,
                "description": data.get("descripcion", ""),
                "document_type": "CUIT" if str(invoice_data["doc_tipo"]) == "80" else 
                               "DNI" if str(invoice_data["doc_tipo"]) == "96" else 
                               f"Tipo {invoice_data['doc_tipo']}",
                "document_number": invoice_data["doc_nro"],
            },
            "cae_data": {
                "cae": cae,
                "cae_expiration": formatted_exp_date
            },
            "amounts": {
                "total": round(imp_total, 2),
                "net": round(imp_neto, 2),
                "tax": round(imp_iva, 2)
            }
        }
        
        return formatted_response
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error generating example invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get(
    "/test-connection",
    summary="Test connectivity to AFIP services"
)
async def test_connection(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test connectivity to AFIP Web Services and check SSL configuration.
    
    Returns:
        Dictionary with connectivity results
    """
    results = {}
    
    # Check certificate and key files
    cert_exists = CERT_PATH.exists()
    key_exists = KEY_PATH.exists()
    
    results["certificates"] = {
        "cert_file": str(CERT_PATH),
        "cert_exists": cert_exists,
        "key_file": str(KEY_PATH),
        "key_exists": key_exists
    }
    
    # Test SSL connection to AFIP
    try:
        # Test direct HTTPS connection
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('https://', adapter)
        session.verify = False
        
        # Create custom SSL context
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Test direct connection to WSAA
        wsaa_url = WSAA_WSDL.replace("?WSDL", "")
        wsaa_response = session.get(wsaa_url, timeout=10)
        results["wsaa_connection"] = {
            "url": wsaa_url,
            "status_code": wsaa_response.status_code,
            "success": wsaa_response.status_code < 400
        }
        
        # Test direct connection to WSFE
        wsfe_url = WSFE_WSDL.replace("?WSDL", "")
        wsfe_response = session.get(wsfe_url, timeout=10)
        results["wsfe_connection"] = {
            "url": wsfe_url,
            "status_code": wsfe_response.status_code,
            "success": wsfe_response.status_code < 400
        }
    except Exception as e:
        results["direct_connection_error"] = str(e)
    
    # Test AFIP WSDL parsing and server status
    try:
        afip_status = await get_server_status()
        results["afip_status"] = afip_status
    except AfipError as e:
        results["afip_status_error"] = {
            "message": str(e),
            "code": getattr(e, "code", None)
        }
    except Exception as e:
        results["afip_status_error"] = str(e)
    
    # Get access ticket
    try:
        ticket = await get_access_ticket("wsfe")
        if ticket:
            results["auth_ticket"] = {
                "success": True,
                "token_length": len(ticket.get("token", "")),
                "sign_length": len(ticket.get("sign", "")),
                "cuit": ticket.get("cuit"),
                "expiration": ticket.get("expiration")
            }
        else:
            results["auth_ticket"] = {
                "success": False,
                "message": "Failed to obtain authentication ticket"
            }
    except Exception as e:
        results["auth_ticket_error"] = str(e)
    
    results["environment"] = ENVIRONMENT
    
    return results

# Add more AFIP endpoints as needed 