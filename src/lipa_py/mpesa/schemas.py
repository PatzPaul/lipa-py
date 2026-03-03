from pydantic import BaseModel, ConfigDict
from typing import Optional

class STKPushRequest(BaseModel):
    phone_number: str
    amount: float
    reference: str
    third_party_conversation_id: str

class MpesaAuthResponse(BaseModel):
    output_ResponseCode: str
    output_ResponseDesc: str
    output_SessionID: str

class MpesaResponse(BaseModel):
    output_ResponseCode: str
    output_ResponseDesc: str
    output_TransactionID: str
    output_ConversationID: str
    output_ThirdPartyConversationID: str
    
    model_config = ConfigDict(extra='ignore')

class MpesaWebhookData(BaseModel):
    """
    Validates incoming JSON from Vodacom when a payment succeeds or fails.
    The exact shape of M-Pesa webhook data can vary slightly, so we use
    flexible typing for the main payload body but enforce standard fields if needed.
    """
    input_TransactionID: Optional[str] = None
    input_ResultCode: Optional[str] = None
    input_ResultDesc: Optional[str] = None
    input_ThirdPartyConversationID: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')
