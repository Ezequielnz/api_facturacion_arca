"""
AFIP Web Services endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, List, Optional

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
    AfipError
)
from app.models.schemas import AfipTicketRequest, AfipTicketResponse
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/api/afip",
    tags=["afip"]
)

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
        Dictionary with AFIP response
    """
    try:
        # Add the user's CUIT to the invoice data if not provided
        if "cuit_emisor" not in invoice_data:
            invoice_data["cuit_emisor"] = current_user.cuit
            
        result = await create_invoice(invoice_data)
        return result
    except AfipError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AFIP error: {str(e)}"
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

# Add more AFIP endpoints as needed 