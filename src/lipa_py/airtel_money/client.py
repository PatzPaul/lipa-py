import asyncio
import httpx
import logging
import time
from typing import Optional, Dict

from lipa_py._base import BasePaymentClient, Environment
from .schemas import AirtelSTKPushRequest, AirtelSTKPushResponse

logger = logging.getLogger(__name__)


class AirtelError(Exception):
    """Base exception for Airtel Money API errors"""
    pass

SANDBOX = Environment("https://openapiuat.airtel.africa")
LIVE = Environment("https://openapi.airtel.africa")

class AirtelClient(BasePaymentClient):
    """
    Client for interacting with Airtel Money APIs (Tanzania, etc).
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        environment: str = "sandbox",
        timeout: float = 30.0
    ):
        self.client_id = client_id
        self.client_secret = client_secret

        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE
        self.client = httpx.AsyncClient(base_url=self.env.base_url, timeout=httpx.Timeout(timeout))

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    async def _authenticate(self) -> None:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        try:
            response = await self.client.post("/auth/oauth2/token", json=data)
            response.raise_for_status()
            body = response.json()
            token = body.get("access_token")
            if not token:
                raise AirtelError("Airtel auth response missing access_token")
            self._access_token = token
            self._token_expires_at = time.time() + float(body.get("expires_in", 3600)) - 60
        except httpx.HTTPStatusError as e:
            logger.warning("Airtel auth failed: status=%s body=%s", e.response.status_code, e.response.text)
            raise AirtelError(f"Failed to authenticate with Airtel: {e.response.text}") from e
        except AirtelError:
            raise
        except Exception as e:
            logger.warning("Airtel auth raised unexpected error: %s", e)
            raise AirtelError(f"An unexpected error occurred during Airtel auth: {str(e)}") from e

    async def _get_auth_headers(self) -> Dict[str, str]:
        async with self._token_lock:
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
        try:
            headers = await self._get_auth_headers()

            normalized_phone = request.phone_number.lstrip("+").replace(" ", "")
            payload = {
                "subscriber": {
                    "country": request.customer_country,
                    "currency": "TZS",
                    "msisdn": int(normalized_phone)
                },
                "transaction": {
                    "amount": request.amount,
                    "country": request.customer_country,
                    "currency": "TZS",
                    "id": request.reference
                }
            }

            response = await self.client.post("/merchant/v1/payments/", json=payload, headers=headers)
            response.raise_for_status()
            return AirtelSTKPushResponse(**response.json())
        except httpx.HTTPStatusError as e:
            logger.warning("Airtel STK push failed: status=%s ref=%s body=%s",
                           e.response.status_code, request.reference, e.response.text)
            raise AirtelError(f"Airtel STK Push failed: {e.response.text}") from e
        except AirtelError:
            raise
        except Exception as e:
            logger.warning("Airtel STK push raised unexpected error: ref=%s err=%s", request.reference, e)
            raise AirtelError(f"An unexpected error occurred during Airtel STK Push: {str(e)}") from e
