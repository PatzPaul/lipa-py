import httpx

from lipa_py.selcom.crypto import generate_selcom_signature, get_iso_timestamp
from lipa_py.selcom.schemas import SelcomCheckoutRequest, SelcomCheckoutResponse

class SelcomError(Exception):
    """Base exception for Selcom API errors"""
    pass

class SelcomClient:
    def __init__(self, vendor_id: str, api_key: str, api_secret: str, environment: str = "sandbox"):
        self.vendor_id = vendor_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.environment = environment
        
        if environment == "sandbox":
            self.base_url = "https://apigw.selcommobile.com/v1"
        else:
            self.base_url = "https://apigw.selcommobile.com/v1" # Need correct prod URL when going live
            
        self.client = httpx.AsyncClient(base_url=self.base_url)

    def _get_headers(self) -> dict:
        """
        Generates required headers including the dynamic HMAC signature.
        """
        timestamp = get_iso_timestamp()
        signature = generate_selcom_signature(self.api_key, self.api_secret, timestamp)
        
        return {
            "Authorization": f"SELCOM {self.api_key}:{signature}",
            "Digest-Method": "HS256",
            "Timestamp": timestamp,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def create_checkout(self, data: SelcomCheckoutRequest) -> SelcomCheckoutResponse:
        """
        Initiates a Selcom Checkout process.
        Returns the token required to complete payment.
        """
        headers = self._get_headers()
        
        payload = data.model_dump()
        payload["vendor"] = self.vendor_id
        
        try:
            response = await self.client.post(
                "/checkout/create-order",
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            
            # Note: Selcom response mapping might require flattening logic depending on exact specs.
            res_data = response.json()
            flattened = {
                "result": res_data.get("result", "FAIL"),
                "message": res_data.get("message", "Unknown validation error"),
            }
            if "data" in res_data and res_data["data"]:
                inner = res_data["data"][0] if isinstance(res_data["data"], list) else res_data["data"]
                flattened.update(inner)

            return SelcomCheckoutResponse.model_validate(flattened)
        except httpx.HTTPStatusError as e:
            raise SelcomError(f"Selcom API request failed: {e.response.text}") from e
        except Exception as e:
            raise SelcomError(f"An unexpected error occurred during Selcom checkout: {str(e)}") from e

    async def close(self):
        """Clean up the async HTTP client"""
        await self.client.aclose()
        
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
