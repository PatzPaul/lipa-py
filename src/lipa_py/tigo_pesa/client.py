import asyncio
import httpx
import logging
import time
from typing import Optional, Dict

from lipa_py._base import BasePaymentClient, Environment
from .schemas import TigoSTKPushRequest, TigoSTKPushResponse

logger = logging.getLogger(__name__)


class TigoError(Exception):
    """Base exception for Tigo Pesa API errors"""
    pass

SANDBOX = Environment("https://securesandbox.tigo.com/v1/tigo/payment-auth")
LIVE = Environment("https://secure.tigo.com/v1/tigo/payment-auth")

class TigoClient(BasePaymentClient):
    """
    Client for interacting with Tigo Pesa Secure APIs.
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        biller_code: str,
        environment: str = "sandbox",
        timeout: float = 30.0
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.biller_code = biller_code

        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE
        self.client = httpx.AsyncClient(base_url=self.env.base_url, timeout=httpx.Timeout(timeout))

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    async def _authenticate(self) -> None:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = await self.client.post("/oauth/generate/accesstoken", data=data)
            response.raise_for_status()
            body = response.json()
            token = body.get("access_token")
            if not token:
                raise TigoError("Tigo auth response missing access_token")
            self._access_token = token
            self._token_expires_at = time.time() + float(body.get("expires_in", 3600)) - 60
        except httpx.HTTPStatusError as e:
            logger.warning("Tigo auth failed: status=%s body=%s", e.response.status_code, e.response.text)
            raise TigoError(f"Failed to authenticate with Tigo: {e.response.text}") from e
        except TigoError:
            raise
        except Exception as e:
            logger.warning("Tigo auth raised unexpected error: %s", e)
            raise TigoError(f"An unexpected error occurred during Tigo auth: {str(e)}") from e

    async def _get_auth_headers(self) -> Dict[str, str]:
        async with self._token_lock:
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
        try:
            headers = await self._get_auth_headers()

            payload = {
                "CustomerMSISDN": request.phone_number,
                "Amount": request.amount,
                "ReferenceID": request.reference,
                "BillerCode": self.biller_code,
                "CustomerEmail": request.customer_email or "",
            }

            response = await self.client.post("/authorize/payment", json=payload, headers=headers)
            response.raise_for_status()
            return TigoSTKPushResponse(**response.json())
        except httpx.HTTPStatusError as e:
            logger.warning("Tigo STK push failed: status=%s ref=%s body=%s",
                           e.response.status_code, request.reference, e.response.text)
            raise TigoError(f"Tigo STK Push failed: {e.response.text}") from e
        except TigoError:
            raise
        except Exception as e:
            logger.warning("Tigo STK push raised unexpected error: ref=%s err=%s", request.reference, e)
            raise TigoError(f"An unexpected error occurred during Tigo STK Push: {str(e)}") from e
