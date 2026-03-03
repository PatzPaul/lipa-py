import httpx
import time
from typing import Optional, Dict
from dataclasses import dataclass

from .crypto import generate_password, generate_timestamp, generate_auth_header
from .schemas import SafaricomSTKPushRequest, SafaricomSTKPushResponse, SafaricomAuthResponse

@dataclass
class Environment:
    base_url: str

SANDBOX = Environment("https://sandbox.safaricom.co.ke")
LIVE = Environment("https://api.safaricom.co.ke")

class SafaricomClient:
    """
    Client for interacting with Safaricom Daraja APIs.
    """
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        passkey: str,
        shortcode: str,
        environment: str = "sandbox"
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.passkey = passkey
        self.shortcode = shortcode
        
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
        Authenticates with Daraja and stores the access token temporarily.
        """
        auth_header = generate_auth_header(self.consumer_key, self.consumer_secret)
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Accept": "application/json"
        }
        
        response = await self.client.get(
            "/oauth/v1/generate?grant_type=client_credentials", 
            headers=headers
        )
        response.raise_for_status()
        
        data = SafaricomAuthResponse(**response.json())
        self._access_token = data.access_token
        # Subtracting 60 seconds from expiry for safety margin
        self._token_expires_at = time.time() + float(data.expires_in) - 60

    async def _get_auth_headers(self) -> Dict[str, str]:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._authenticate()
            
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

    async def stk_push(self, request: SafaricomSTKPushRequest) -> SafaricomSTKPushResponse:
        """
        Initiate an STK Push (M-Pesa Express) request to the user's phone.
        """
        headers = await self._get_auth_headers()
        
        timestamp = generate_timestamp()
        password = generate_password(self.shortcode, self.passkey, timestamp)
        
        payload = {
            "BusinessShortCode": int(self.shortcode),
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline", # Used for shortcodes (Paybill)
            "Amount": request.amount,
            "PartyA": request.phone_number,
            "PartyB": int(self.shortcode),
            "PhoneNumber": request.phone_number,
            "CallBackURL": request.callback_url,
            "AccountReference": request.reference,
            "TransactionDesc": request.description
        }
        
        response = await self.client.post("/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Safaricom STK Push failed: {response.text}")
            
        return SafaricomSTKPushResponse(**response.json())
