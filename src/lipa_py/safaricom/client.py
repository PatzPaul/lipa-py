import asyncio
import httpx
import logging
import time
from typing import Optional, Dict

from lipa_py._base import BasePaymentClient, Environment
from .crypto import generate_password, generate_timestamp, generate_auth_header
from .schemas import SafaricomSTKPushRequest, SafaricomSTKPushResponse, SafaricomAuthResponse

logger = logging.getLogger(__name__)


class SafaricomError(Exception):
    """Base exception for Safaricom Daraja API errors"""
    pass

SANDBOX = Environment("https://sandbox.safaricom.co.ke")
LIVE = Environment("https://api.safaricom.co.ke")

class SafaricomClient(BasePaymentClient):
    """
    Client for interacting with Safaricom Daraja APIs.
    """
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        passkey: str,
        shortcode: str,
        environment: str = "sandbox",
        timeout: float = 30.0
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.passkey = passkey
        self.shortcode = shortcode

        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE
        self.client = httpx.AsyncClient(base_url=self.env.base_url, timeout=httpx.Timeout(timeout))

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    async def _authenticate(self) -> None:
        auth_header = generate_auth_header(self.consumer_key, self.consumer_secret)
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Accept": "application/json"
        }

        try:
            response = await self.client.get(
                "/oauth/v1/generate?grant_type=client_credentials",
                headers=headers
            )
            response.raise_for_status()
            data = SafaricomAuthResponse(**response.json())
            self._access_token = data.access_token
            # Subtracting 60 seconds from expiry for safety margin
            self._token_expires_at = time.time() + float(data.expires_in) - 60
        except httpx.HTTPStatusError as e:
            logger.warning("Safaricom auth failed: status=%s body=%s", e.response.status_code, e.response.text)
            raise SafaricomError(f"Safaricom authentication failed: {e.response.text}") from e
        except Exception as e:
            logger.warning("Safaricom auth raised unexpected error: %s", e)
            raise SafaricomError(f"An unexpected error occurred during Safaricom auth: {str(e)}") from e

    async def _get_auth_headers(self) -> Dict[str, str]:
        async with self._token_lock:
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
        try:
            headers = await self._get_auth_headers()

            timestamp = generate_timestamp()
            password = generate_password(self.shortcode, self.passkey, timestamp)

            payload = {
                "BusinessShortCode": int(self.shortcode),
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": request.amount,
                "PartyA": request.phone_number,
                "PartyB": int(self.shortcode),
                "PhoneNumber": request.phone_number,
                "CallBackURL": request.callback_url,
                "AccountReference": request.reference,
                "TransactionDesc": request.description
            }

            response = await self.client.post("/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
            response.raise_for_status()
            return SafaricomSTKPushResponse(**response.json())
        except httpx.HTTPStatusError as e:
            logger.warning("Safaricom STK push failed: status=%s ref=%s body=%s",
                           e.response.status_code, request.reference, e.response.text)
            raise SafaricomError(f"Safaricom STK Push failed: {e.response.text}") from e
        except SafaricomError:
            raise
        except Exception as e:
            logger.warning("Safaricom STK push raised unexpected error: ref=%s err=%s", request.reference, e)
            raise SafaricomError(f"An unexpected error occurred during Safaricom STK Push: {str(e)}") from e
