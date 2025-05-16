"""
Pydantic schemas for the AFIP API application.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import date

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    cuit: str = Field(..., description="CUIT number")
    company_name: str

class UserCreate(UserBase):
    """Schema for user creation, including password."""
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    """Schema for user information returned to clients."""
    id: int
    is_active: bool

    class Config:
        """Pydantic model configuration."""
        from_attributes = True

class Token(BaseModel):
    """
    Schema for the access token returned after authentication.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Schema for data contained within a JWT token.
    """
    email: Optional[str] = None

class AfipTicketRequest(BaseModel):
    """
    Schema for requesting an AFIP access ticket.
    """
    service: str = Field(..., description="Service ID (e.g., wsfe)")

class AfipTicketResponse(BaseModel):
    """
    Schema for AFIP access ticket response.
    """
    token: str
    sign: str
    expiration: str

class AlicuotaIVA(BaseModel):
    """
    Schema for an IVA tax aliquot.
    """
    id: int = Field(..., description="IVA type ID")
    base_imp: float = Field(..., description="Base amount")
    importe: float = Field(..., description="Tax amount")

class Tributo(BaseModel):
    """
    Schema for a tax/tribute.
    """
    id: int = Field(..., description="Tax type ID")
    base_imp: float = Field(..., description="Base amount")
    alicuota: float = Field(..., description="Tax rate")
    importe: float = Field(..., description="Tax amount")

class Opcional(BaseModel):
    """
    Schema for optional invoice data.
    """
    id: str = Field(..., description="Optional ID")
    valor: str = Field(..., description="Optional value")

class InvoiceCreate(BaseModel):
    """
    Schema for creating an electronic invoice.
    """
    punto_venta: int = Field(..., description="Sales point number")
    tipo_comprobante: int = Field(..., description="Invoice type code")
    concepto: int = Field(..., description="Concept type code")
    doc_tipo: int = Field(..., description="Document type code")
    doc_nro: int = Field(..., description="Document number")
    cbte_desde: int = Field(..., description="Invoice number from")
    cbte_hasta: int = Field(..., description="Invoice number to")
    cbte_fecha: str = Field(..., description="Invoice date (YYYYMMDD)")
    imp_total: float = Field(..., description="Total amount")
    imp_tot_conc: Optional[float] = Field(0, description="Non-taxable amount")
    imp_neto: Optional[float] = Field(0, description="Net amount")
    imp_op_ex: Optional[float] = Field(0, description="Exempt amount")
    imp_iva: Optional[float] = Field(0, description="IVA amount")
    imp_trib: Optional[float] = Field(0, description="Tributes amount")
    moneda_id: Optional[str] = Field("PES", description="Currency ID")
    moneda_cotiz: Optional[float] = Field(1, description="Currency exchange rate")
    iva: Optional[List[AlicuotaIVA]] = Field(None, description="IVA details")
    tributos: Optional[List[Tributo]] = Field(None, description="Tributes details")
    opcionales: Optional[List[Opcional]] = Field(None, description="Optional data")
    
    @field_validator('cbte_fecha')
    @classmethod
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('cbte_fecha must be in YYYYMMDD format')
        return v

class InvoiceResponse(BaseModel):
    """
    Schema for the response of an invoice creation.
    """
    resultado: str = Field(..., description="Result (A: Approved, R: Rejected)")
    cae: Optional[str] = Field(None, description="CAE number")
    cae_vto: Optional[str] = Field(None, description="CAE expiration date")
    observaciones: Optional[List[Dict[str, Any]]] = Field(None, description="Observations")
    errores: Optional[List[Dict[str, Any]]] = Field(None, description="Errors")

class InvoiceInfo(BaseModel):
    """
    Schema for invoice information.
    """
    punto_venta: int
    tipo_comprobante: int
    nro_comprobante: int
    fecha: str
    imp_total: float
    resultado: str
    cae: Optional[str] = None
    cae_vto: Optional[str] = None 