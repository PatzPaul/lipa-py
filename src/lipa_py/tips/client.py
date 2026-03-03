import httpx
import time
from typing import Optional, Dict
from dataclasses import dataclass

from .schemas import TIPSCheckoutRequest, TIPSCheckoutResponse

@dataclass
class Environment:
    base_url: str

SANDBOX = Environment("https://tips-sandbox.bot.go.tz")
LIVE = Environment("https://tips.bot.go.tz")

class TIPSClient:
    """
    Client for interacting with TIPS (Tanzania Instant Payment System) APIs.
    """
    def __init__(
        self,
        api_key: str,
        institution_id: str,
        certificate_path: Optional[str] = None, # Often required for mTLS by TIPS
        environment: str = "sandbox"
    ):
        self.api_key = api_key
        self.institution_id = institution_id
        self.certificate_path = certificate_path
        
        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE
        
        # Simplified Client instantiation. TIPS often uses mTLS.
        if self.certificate_path:
            self.client = httpx.AsyncClient(base_url=self.env.base_url, cert=self.certificate_path)
        else:
            self.client = httpx.AsyncClient(base_url=self.env.base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
    async def close(self):
        await self.client.aclose()
        
    async def _get_auth_headers(self) -> Dict[str, str]:
        # Typically TIPS authenticates via API key or signature headers + mTLS rather than OAuth tokens
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Institution-Id": self.institution_id,
            "Content-Type": "application/json"
        }

    async def create_checkout(self, request: TIPSCheckoutRequest) -> TIPSCheckoutResponse:
        """
        Initiate a payment request.
        """
        headers = await self._get_auth_headers()
        
        payload = {
            "accountNumber": request.account_number,
            "amount": request.amount,
            "transactionReference": request.reference,
            "institutionId": request.institution_id or self.institution_id,
            "payerName": request.payer_name or "Unknown"
        }
        
        response = await self.client.post("/api/v1/payments/", json=payload, headers=headers)
        
        if response.status_code not in (200, 201, 202):
            raise Exception(f"TIPS Checkout failed: {response.text}")
            
        return TIPSCheckoutResponse(**response.json())
