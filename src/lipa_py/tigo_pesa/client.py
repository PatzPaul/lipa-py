import httpx
import time
from typing import Optional, Dict
from dataclasses import dataclass

from .schemas import TigoSTKPushRequest, TigoSTKPushResponse

@dataclass
class Environment:
    base_url: str

SANDBOX = Environment("https://securesandbox.tigo.com/v1/tigo/payment-auth")
LIVE = Environment("https://secure.tigo.com/v1/tigo/payment-auth")

class TigoClient:
    """
    Client for interacting with Tigo Pesa Secure APIs.
    (Note: exact paths depend on version. This template focuses on basic auth patterns).
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        biller_code: str,
        environment: str = "sandbox"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.biller_code = biller_code
        
        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE
        self.client = httpx.AsyncClient(base_url=self.env.base_url)
        
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
    async def close(self):
        await self.client.aclose()
        
    async def _authenticate(self) -> None:
        """
        Authenticates with Tigo and stores the access token temporarily.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = await self.client.post("/oauth/generate/accesstoken", data=data)
        
        if response.status_code != 200:
             raise Exception("Failed to authenticate with Tigo")
             
        # Mock logic
        self._access_token = response.json().get("access_token", "mock_token")
        self._token_expires_at = time.time() + float(response.json().get("expires_in", 3600)) - 60

    async def _get_auth_headers(self) -> Dict[str, str]:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._authenticate()
            
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

    async def stk_push(self, request: TigoSTKPushRequest) -> TigoSTKPushResponse:
        """
        Initiate an STK Push to the user's phone.
        """
        # Note: Depending on Tigo's implementation, you may need a separate path for Sandbox pushing.
        headers = await self._get_auth_headers()
        
        payload = {
            "CustomerMSISDN": request.phone_number,
            "Amount": request.amount,
            "ReferenceID": request.reference,
            "BillerCode": self.biller_code,
            "CustomerEmail": request.customer_email or "",
        }
        
        # Example Endpoint Call for Tigo
        response = await self.client.post("/authorize/payment", json=payload, headers=headers)
        
        if response.status_code not in (200, 201, 202):
            raise Exception(f"Tigo STK Push failed: {response.text}")
            
        return TigoSTKPushResponse(**response.json())
