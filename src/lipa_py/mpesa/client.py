import httpx

from lipa_py.mpesa.crypto import encrypt_api_key
from lipa_py.mpesa.schemas import STKPushRequest, MpesaAuthResponse, MpesaResponse

class MpesaError(Exception):
    """Base exception for M-Pesa API errors"""
    pass

class MPesaClient:
    def __init__(self, api_key: str, public_key: str, environment: str = "sandbox"):
        self.api_key = api_key
        self.public_key = public_key
        self.environment = environment
        
        if environment == "sandbox":
            self.base_url = "https://openapi.m-pesa.com/sandbox"
        else:
            self.base_url = "https://openapi.m-pesa.com/openapi"
            
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def _get_session_token(self) -> str:
        """
        Encrypts the API key and retrieves a session token from Vodacom's API.
        """
        encrypted_key = encrypt_api_key(self.api_key, self.public_key)
        
        headers = {
            "Authorization": f"Bearer {encrypted_key}",
            "Accept": "application/json"
        }
        
        try:
            response = await self.client.get("/ipg/v2/vodacomTZN/getSession/", headers=headers)
            response.raise_for_status()
            
            auth_response = MpesaAuthResponse.model_validate(response.json())
            return auth_response.output_SessionID
        except httpx.HTTPStatusError as e:
            raise MpesaError(f"Failed to get session token: {e.response.text}") from e
        except Exception as e:
            raise MpesaError(f"An unexpected error occurred during auth: {str(e)}") from e

    async def stk_push(self, data: STKPushRequest) -> MpesaResponse:
        """
        Initiates an STK Push to a customer's phone using the current session token.
        """
        session_token = await self._get_session_token()
        
        headers = {
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Mapping our clean Pydantic model to the keys expected by Vodacom
        payload = {
            "input_Amount": str(data.amount),
            "input_CustomerMSISDN": data.phone_number,
            "input_Country": "TZN",
            "input_Currency": "TZS",
            "input_ServiceProviderCode": "000000",
            "input_TransactionReference": data.reference,
            "input_ThirdPartyConversationID": data.third_party_conversation_id,
            "input_PurchasedItemsDesc": "Payment via STK push"
        }
        
        try:
            response = await self.client.post(
                "/ipg/v2/vodacomTZN/c2bPayment/singleStage/", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            
            return MpesaResponse.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            raise MpesaError(f"Failed to initiate STK push: {e.response.text}") from e
        except Exception as e:
            raise MpesaError(f"An unexpected error occurred during STK push: {str(e)}") from e

    async def close(self):
        """Clean up the async HTTP client"""
        await self.client.aclose()
        
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
