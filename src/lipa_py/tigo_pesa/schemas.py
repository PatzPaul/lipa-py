from pydantic import BaseModel, ConfigDict
from typing import Optional

class TigoSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    reference: str
    customer_email: Optional[str] = None
    customer_firstname: Optional[str] = None
    customer_lastname: Optional[str] = None

class TigoSTKPushResponse(BaseModel):
    ResponseCode: str
    ResponseDescription: str
    ReferenceID: str
    
    model_config = ConfigDict(extra='ignore')

class TigoWebhookData(BaseModel):
    """
    Validates incoming JSON from Tigo when a payment succeeds or fails.
    """
    ReferenceID: Optional[str] = None
    Status: Optional[str] = None
    Description: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')
