from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List

class SafaricomSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    reference: str
    callback_url: str
    description: str = "Payment"

class SafaricomAuthResponse(BaseModel):
    access_token: str
    expires_in: str

class SafaricomSTKPushResponse(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str
    
    model_config = ConfigDict(extra='ignore')

class SafaricomCallbackItem(BaseModel):
    Name: str
    Value: Optional[Any] = None

class SafaricomCallbackMetadata(BaseModel):
    Item: List[SafaricomCallbackItem]

class SafaricomStkCallback(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[SafaricomCallbackMetadata] = None

class SafaricomWebhookBody(BaseModel):
    stkCallback: SafaricomStkCallback

class SafaricomWebhookData(BaseModel):
    """
    Validates incoming JSON from Safaricom Daraja API when a payment succeeds or fails.
    """
    Body: SafaricomWebhookBody
    
    model_config = ConfigDict(extra='allow')
