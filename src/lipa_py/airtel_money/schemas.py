from pydantic import BaseModel, ConfigDict
from typing import Optional


class AirtelSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    reference: str
    customer_country: str = "TZ"


class AirtelTransactionData(BaseModel):
    id: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class AirtelResponseData(BaseModel):
    transaction: Optional[AirtelTransactionData] = None
    model_config = ConfigDict(extra="allow")


class AirtelResponseStatus(BaseModel):
    success: Optional[bool] = None
    model_config = ConfigDict(extra="allow")


class AirtelSTKPushResponse(BaseModel):
    status: AirtelResponseStatus
    data: Optional[AirtelResponseData] = None
    model_config = ConfigDict(extra="ignore")

class AirtelWebhookData(BaseModel):
    """
    Validates incoming JSON from Airtel when a payment succeeds or fails.
    """
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')
