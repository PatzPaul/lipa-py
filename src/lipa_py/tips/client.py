import httpx
import logging
from typing import Optional, Dict

from lipa_py._base import BasePaymentClient, Environment
from .schemas import TIPSCheckoutRequest, TIPSCheckoutResponse

logger = logging.getLogger(__name__)


class TIPSError(Exception):
    """Base exception for TIPS (Tanzania Instant Payment System) API errors"""
    pass

SANDBOX = Environment("https://tips-sandbox.bot.go.tz")
LIVE = Environment("https://tips.bot.go.tz")

class TIPSClient(BasePaymentClient):
    """
    Client for interacting with TIPS (Tanzania Instant Payment System) APIs.
    """
    def __init__(
        self,
        api_key: str,
        institution_id: str,
        certificate_path: Optional[str] = None,
        environment: str = "sandbox",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.institution_id = institution_id
        self.certificate_path = certificate_path

        self.env = SANDBOX if environment.lower() == "sandbox" else LIVE

        if self.certificate_path:
            self.client = httpx.AsyncClient(base_url=self.env.base_url, cert=self.certificate_path, timeout=httpx.Timeout(timeout))
        else:
            self.client = httpx.AsyncClient(base_url=self.env.base_url, timeout=httpx.Timeout(timeout))

    async def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Institution-Id": self.institution_id,
            "Content-Type": "application/json"
        }

    async def create_checkout(self, request: TIPSCheckoutRequest) -> TIPSCheckoutResponse:
        """
        Initiate a payment request.
        """
        try:
            headers = await self._get_auth_headers()

            payload = {
                "accountNumber": request.account_number,
                "amount": request.amount,
                "transactionReference": request.reference,
                "institutionId": request.institution_id or self.institution_id,
                "payerName": request.payer_name or "Unknown"
            }

            response = await self.client.post("/api/v1/payments/", json=payload, headers=headers)
            response.raise_for_status()
            return TIPSCheckoutResponse(**response.json())
        except httpx.HTTPStatusError as e:
            logger.warning("TIPS checkout failed: status=%s ref=%s body=%s",
                           e.response.status_code, request.reference, e.response.text)
            raise TIPSError(f"TIPS Checkout failed: {e.response.text}") from e
        except TIPSError:
            raise
        except Exception as e:
            logger.warning("TIPS checkout raised unexpected error: ref=%s err=%s", request.reference, e)
            raise TIPSError(f"An unexpected error occurred during TIPS Checkout: {str(e)}") from e
