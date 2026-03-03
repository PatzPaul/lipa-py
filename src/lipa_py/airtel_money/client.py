import httpx
import time
from typing import Optional, Dict
from dataclasses import dataclass

from .schemas import AirtelSTKPushRequest, AirtelSTKPushResponse

@dataclass
class Environment:
    base_url: str

SANDBOX = Environment("https://openapiuat.airtel.africa")
LIVE = Environment("https://openapi.airtel.africa")

class AirtelClient:
    """
    Client for interacting with Airtel Money APIs (Tanzania, etc).
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        environment: str = "sandbox"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        
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
        Authenticates with Airtel and stores the access token temporarily.
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        response = await self.client.post("/auth/oauth2/token", json=data)
        
        if response.status_code != 200:
             raise Exception("Failed to authenticate with Airtel")
             
        # Mock logic
        self._access_token = response.json().get("access_token", "mock_token")
        self._token_expires_at = time.time() + float(response.json().get("expires_in", 3600)) - 60

    async def _get_auth_headers(self) -> Dict[str, str]:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._authenticate()
            
        return {
            "Authorization": f"Bearer {self._access_token}",
            "X-Country": "TZ",
            "X-Currency": "TZS",
            "Content-Type": "application/json"
        }

    async def stk_push(self, request: AirtelSTKPushRequest) -> AirtelSTKPushResponse:
        """
        Initiate an STK Push to the user's phone.
        """
        headers = await self._get_auth_headers()
        
        payload = {
            "subscriber": {
                "country": request.customer_country,
                "currency": "TZS",
                "msisdn": int(request.phone_number)
            },
            "transaction": {
                "amount": request.amount,
                "country": request.customer_country,
                "currency": "TZS",
                "id": request.reference
            }
        }
        
        # Example Endpoint Call for Airtel Merchant Payment
        response = await self.client.post("/merchant/v1/payments/", json=payload, headers=headers)
        
        if response.status_code not in (200, 201, 202):
            raise Exception(f"Airtel STK Push failed: {response.text}")
            
        return AirtelSTKPushResponse(**response.json())
