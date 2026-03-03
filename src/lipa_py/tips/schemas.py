from pydantic import BaseModel, ConfigDict
from typing import Optional

class TIPSCheckoutRequest(BaseModel):
    account_number: str
    amount: float
    reference: str
    institution_id: Optional[str] = None
    payer_name: Optional[str] = None

class TIPSCheckoutResponse(BaseModel):
    transaction_reference: str
    status: str
    message: str
    
    model_config = ConfigDict(extra='ignore')

class TIPSWebhookData(BaseModel):
    """
    Validates incoming JSON from TIPS.
    """
    transaction_reference: Optional[str] = None
    status: Optional[str] = None
    status_code: Optional[str] = None
    amount: Optional[float] = None
    
    model_config = ConfigDict(extra='allow')
