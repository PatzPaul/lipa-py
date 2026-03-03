from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict

class UnifiedPaymentConfig(BaseModel):
    """Configuration for the Unified Integration Client"""
    mpesa: Optional[Dict[str, str]] = None
    selcom: Optional[Dict[str, str]] = None
    safaricom: Optional[Dict[str, str]] = None
    tigo_pesa: Optional[Dict[str, str]] = None
    airtel_money: Optional[Dict[str, str]] = None
    tips: Optional[Dict[str, str]] = None

class UnifiedPaymentRequest(BaseModel):
    """Standardized Payment Request mapped dynamically to supported Gateways"""
    phone_number: str
    amount: float
    reference: str
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
