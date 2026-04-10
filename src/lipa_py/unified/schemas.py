from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class MpesaConfig(BaseModel):
    api_key: str
    public_key: str
    service_provider_code: str = "000000"
    environment: str = "sandbox"
    timeout: float = 30.0


class SelcomConfig(BaseModel):
    vendor_id: str
    api_key: str
    api_secret: str
    environment: str = "sandbox"
    base_url: Optional[str] = None
    timeout: float = 30.0


class SafaricomConfig(BaseModel):
    consumer_key: str
    consumer_secret: str
    passkey: str
    shortcode: str
    environment: str = "sandbox"
    timeout: float = 30.0


class TigoConfig(BaseModel):
    client_id: str
    client_secret: str
    biller_code: str
    environment: str = "sandbox"
    timeout: float = 30.0


class AirtelConfig(BaseModel):
    client_id: str
    client_secret: str
    environment: str = "sandbox"
    timeout: float = 30.0


class TIPSConfig(BaseModel):
    api_key: str
    institution_id: str
    certificate_path: Optional[str] = None
    environment: str = "sandbox"
    timeout: float = 30.0


class UnifiedPaymentConfig(BaseModel):
    """Configuration for the Unified Integration Client"""
    mpesa: Optional[MpesaConfig] = None
    selcom: Optional[SelcomConfig] = None
    safaricom: Optional[SafaricomConfig] = None
    tigo_pesa: Optional[TigoConfig] = None
    airtel_money: Optional[AirtelConfig] = None
    tips: Optional[TIPSConfig] = None


class UnifiedPaymentRequest(BaseModel):
    """Standardized Payment Request mapped dynamically to supported Gateways"""
    phone_number: str
    amount: float
    reference: str
    conversation_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = "Payment services"


class UnifiedPaymentResponse(BaseModel):
    """Standardized Payment Response mapping Gateway outputs"""
    provider: str
    status: str
    transaction_id: str
    original_response: Any

    model_config = ConfigDict(extra='allow')
