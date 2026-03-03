from pydantic import BaseModel
from typing import Optional

class SelcomCheckoutRequest(BaseModel):
    vendor: str
    order_id: str
    buyer_email: str
    buyer_name: str
    buyer_phone: str
    amount: float
    currency: str = "TZS"
    payment_methods: str = "ALL"

class SelcomCheckoutResponse(BaseModel):
    result: str
    message: str
    order_id: str
    payment_token: Optional[str] = None
    checkout_url: Optional[str] = None
    
class SelcomWebhookData(BaseModel):
    """
    Standard schema to validate incoming Selcom payment notifications via Webhook.
    """
    transid: str
    reference: str
    amount: float
    currency: str
    gateway_buyer_uuid: str
    gateway_buyer_msisdn: str
    resultcode: str
    result: str

    def is_successful(self) -> bool:
        return self.resultcode == "000" and self.result.lower() == "success"
