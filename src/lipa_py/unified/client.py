from typing import Optional, Dict
from lipa_py.mpesa.client import MPesaClient
from lipa_py.selcom.client import SelcomClient
from lipa_py.mpesa.schemas import STKPushRequest
from lipa_py.selcom.schemas import SelcomCheckoutRequest
from lipa_py.safaricom.client import SafaricomClient
from lipa_py.safaricom.schemas import SafaricomSTKPushRequest
from lipa_py.tigo_pesa.client import TigoClient
from lipa_py.tigo_pesa.schemas import TigoSTKPushRequest
from lipa_py.airtel_money.client import AirtelClient
from lipa_py.airtel_money.schemas import AirtelSTKPushRequest
from lipa_py.tips.client import TIPSClient
from lipa_py.tips.schemas import TIPSCheckoutRequest
from lipa_py.unified.schemas import UnifiedPaymentConfig, UnifiedPaymentRequest, UnifiedPaymentResponse

class UnifiedPaymentClient:
    """
    The main orchestrator for lipa-py.
    Automatically detects the provider based on configuration or phone prefix
    and routes the generalized PaymentRequest to the correct MNO/Aggregator.
    """
    
    def __init__(self, config: Dict):
        self._parsed_config = UnifiedPaymentConfig.model_validate(config)
        self._clients = {}
        
        # Initialize configured clients
        if self._parsed_config.mpesa:
            self._clients["mpesa"] = MPesaClient(**self._parsed_config.mpesa)
            
        if self._parsed_config.selcom:
            self._clients["selcom"] = SelcomClient(**self._parsed_config.selcom)

        if self._parsed_config.safaricom:
            self._clients["safaricom"] = SafaricomClient(**self._parsed_config.safaricom)
            
        if self._parsed_config.tigo_pesa:
            self._clients["tigo_pesa"] = TigoClient(**self._parsed_config.tigo_pesa)
            
        if self._parsed_config.airtel_money:
            self._clients["airtel_money"] = AirtelClient(**self._parsed_config.airtel_money)

        if self._parsed_config.tips:
            self._clients["tips"] = TIPSClient(**self._parsed_config.tips)

    def _detect_provider(self, phone: str) -> str:
        """
        Simple prefix routing. 
        In Tanzania, prefixes generally map to:
        075, 076, 074 -> Vodacom (M-Pesa)
        071, 065, 067 -> Tigo
        078, 068 -> Airtel
        
        For this MVP, we route Vodacom to M-Pesa, everything else to Selcom if configured.
        """
        # Normalize to 255 format if passed with 0
        if phone.startswith("0"):
            phone = "255" + phone[1:]
            
        prefix = phone[3:5] if phone.startswith("255") else phone[:2]
        
        # 75, 76, 74 are standard Vodacom Tanzania prefixes
        if prefix in ["75", "76", "74"] and "mpesa" in self._clients:
            return "mpesa"
            
        # 71, 65, 67 are standard Tigo Tanzania prefixes
        if prefix in ["71", "65", "67"] and "tigo_pesa" in self._clients:
            return "tigo_pesa"

        # 78, 68, 69 are standard Airtel Tanzania prefixes
        if prefix in ["78", "68", "69"] and "airtel_money" in self._clients:
            return "airtel_money"
            
        # Detect Kenyan Safaricom (254) numbers
        # Typically Safaricom uses 70, 71, 72, 79, 74, 11 etc. Simplification for 254:
        if phone.startswith("254") and "safaricom" in self._clients:
            return "safaricom"

        if "tips" in self._clients:
            return "tips"

        if "selcom" in self._clients:
            return "selcom"
            
        raise ValueError(f"No configured provider could handle the phone number: {phone}")

    async def request_payment(self, request: UnifiedPaymentRequest, force_provider: Optional[str] = None) -> UnifiedPaymentResponse:
        """
        Executes the payment against the detected or forced provider.
        """
        provider = force_provider or self._detect_provider(request.phone_number)
        client = self._clients.get(provider)
        
        if not client:
            raise ValueError(f"Provider '{provider}' is not configured.")

        # ==========================================
        # M-Pesa Adapter
        # ==========================================
        if provider == "mpesa":
            mpesa_req = STKPushRequest(
                phone_number=request.phone_number,
                amount=request.amount,
                reference=request.reference,
                third_party_conversation_id=request.reference
            )
            mpesa_res = await client.stk_push(mpesa_req)
            
            return UnifiedPaymentResponse(
                provider="mpesa",
                status="pending",
                transaction_id=mpesa_res.output_ConversationID,
                original_response=mpesa_res
            )

        # ==========================================
        # Selcom Adapter
        # ==========================================
        elif provider == "selcom":
            selcom_req = SelcomCheckoutRequest(
                vendor=self._parsed_config.selcom.get("vendor_id"),
                order_id=request.reference,
                buyer_email=request.email or "guest@example.com",
                buyer_name=request.name or "Guest User",
                buyer_phone=request.phone_number,
                amount=request.amount,
            )
            selcom_res = await client.create_checkout(selcom_req)
            
            return UnifiedPaymentResponse(
                provider="selcom",
                status="created",
                transaction_id=selcom_res.order_id,
                original_response=selcom_res
            )

        # ==========================================
        # Safaricom Adapter
        # ==========================================
        elif provider == "safaricom":
            safaricom_req = SafaricomSTKPushRequest(
                phone_number=request.phone_number,
                amount=request.amount,
                reference=request.reference,
                callback_url=self._parsed_config.safaricom.get("callback_url", "https://example.com/webhook")
            )
            safaricom_res = await client.stk_push(safaricom_req)
            
            return UnifiedPaymentResponse(
                provider="safaricom",
                status="pending",
                transaction_id=safaricom_res.CheckoutRequestID,
                original_response=safaricom_res
            )

        # ==========================================
        # Tigo Pesa Adapter
        # ==========================================
        elif provider == "tigo_pesa":
            tigo_req = TigoSTKPushRequest(
                phone_number=request.phone_number,
                amount=request.amount,
                reference=request.reference,
                customer_email=request.email
            )
            tigo_res = await client.stk_push(tigo_req)
            
            return UnifiedPaymentResponse(
                provider="tigo_pesa",
                status="pending",
                transaction_id=tigo_res.ReferenceID,
                original_response=tigo_res
            )

        # ==========================================
        # Airtel Money Adapter
        # ==========================================
        elif provider == "airtel_money":
            airtel_req = AirtelSTKPushRequest(
                phone_number=request.phone_number,
                amount=request.amount,
                reference=request.reference
            )
            airtel_res = await client.stk_push(airtel_req)
            
            tx_id = airtel_res.data.get("transaction", {}).get("id", "UNKNOWN") if airtel_res.data else "UNKNOWN"
            return UnifiedPaymentResponse(
                provider="airtel_money",
                status="pending",
                transaction_id=tx_id,
                original_response=airtel_res
            )

        # ==========================================
        # TIPS (Tanzania Instant Payment System) Adapter
        # ==========================================
        elif provider == "tips":
            tips_req = TIPSCheckoutRequest(
                account_number=request.phone_number,
                amount=request.amount,
                reference=request.reference,
                payer_name=request.name
            )
            tips_res = await client.create_checkout(tips_req)
            
            return UnifiedPaymentResponse(
                provider="tips",
                status="pending",
                transaction_id=tips_res.transaction_reference,
                original_response=tips_res
            )

        raise ValueError(f"Unsupported provider: {provider}")

    async def close(self):
        """Clean up all initialized async HTTP clients."""
        for client in self._clients.values():
            await client.close()
            
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
