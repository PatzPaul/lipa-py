from typing import Optional, Dict, Callable, Awaitable
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

# Callable type alias for adapter methods
Adapter = Callable[[UnifiedPaymentRequest], Awaitable[UnifiedPaymentResponse]]


class UnifiedPaymentClient:
    """
    The main orchestrator for lipa-py.
    Automatically detects the provider based on phone prefix and routes
    the payment request to the correct MNO/Aggregator client.
    """

    def __init__(self, config: Dict):
        self._parsed_config = UnifiedPaymentConfig.model_validate(config)
        self._clients: Dict[str, object] = {}
        self._adapters: Dict[str, Adapter] = {}

        if self._parsed_config.mpesa:
            self._clients["mpesa"] = MPesaClient(**self._parsed_config.mpesa.model_dump())
            self._adapters["mpesa"] = self._mpesa_adapter

        if self._parsed_config.selcom:
            self._clients["selcom"] = SelcomClient(**self._parsed_config.selcom.model_dump())
            self._adapters["selcom"] = self._selcom_adapter

        if self._parsed_config.safaricom:
            self._clients["safaricom"] = SafaricomClient(
                **self._parsed_config.safaricom.model_dump(exclude={"callback_url"})
            )
            self._adapters["safaricom"] = self._safaricom_adapter

        if self._parsed_config.tigo_pesa:
            self._clients["tigo_pesa"] = TigoClient(**self._parsed_config.tigo_pesa.model_dump())
            self._adapters["tigo_pesa"] = self._tigo_adapter

        if self._parsed_config.airtel_money:
            self._clients["airtel_money"] = AirtelClient(**self._parsed_config.airtel_money.model_dump())
            self._adapters["airtel_money"] = self._airtel_adapter

        if self._parsed_config.tips:
            self._clients["tips"] = TIPSClient(**self._parsed_config.tips.model_dump())
            self._adapters["tips"] = self._tips_adapter

    def _detect_provider(self, phone: str) -> str:
        """
        Routes by phone number prefix.
        Tanzania: 075/076/074 → M-Pesa, 071/065/067 → Tigo, 078/068/069 → Airtel
        Kenya: 254 prefix → Safaricom
        Falls back to TIPS then Selcom if configured.
        """
        phone = phone.lstrip("+").replace(" ", "")
        if phone.startswith("0"):
            phone = "255" + phone[1:]

        prefix = phone[3:5] if phone.startswith("255") else phone[:2]

        if prefix in ["75", "76", "74"] and "mpesa" in self._clients:
            return "mpesa"
        if prefix in ["71", "65", "67"] and "tigo_pesa" in self._clients:
            return "tigo_pesa"
        if prefix in ["78", "68", "69"] and "airtel_money" in self._clients:
            return "airtel_money"
        if phone.startswith("254") and "safaricom" in self._clients:
            return "safaricom"
        if "tips" in self._clients:
            return "tips"
        if "selcom" in self._clients:
            return "selcom"

        raise ValueError(f"No configured provider could handle the phone number: {phone}")

    async def request_payment(self, request: UnifiedPaymentRequest, force_provider: Optional[str] = None) -> UnifiedPaymentResponse:
        """Executes the payment against the detected or forced provider."""
        provider = force_provider or self._detect_provider(request.phone_number)
        adapter = self._adapters.get(provider)
        if not adapter:
            raise ValueError(f"Provider '{provider}' is not configured.")
        return await adapter(request)

    # ── Adapters ──────────────────────────────────────────────────────────────

    async def _mpesa_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        client: MPesaClient = self._clients["mpesa"]
        res = await client.stk_push(STKPushRequest(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=request.reference,
            third_party_conversation_id=request.conversation_id or request.reference,
        ))
        return UnifiedPaymentResponse(
            provider="mpesa",
            status="pending",
            transaction_id=res.output_ConversationID,
            original_response=res,
        )

    async def _selcom_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        if not request.email:
            raise ValueError(
                "Selcom requires an email address. Set 'email' on UnifiedPaymentRequest."
            )
        client: SelcomClient = self._clients["selcom"]
        res = await client.create_checkout(SelcomCheckoutRequest(
            order_id=request.reference,
            buyer_email=request.email,
            buyer_name=request.name or "Guest User",
            buyer_phone=request.phone_number,
            amount=request.amount,
        ))
        return UnifiedPaymentResponse(
            provider="selcom",
            status="created",
            transaction_id=res.order_id,
            original_response=res,
        )

    async def _safaricom_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        client: SafaricomClient = self._clients["safaricom"]
        cfg = self._parsed_config.safaricom
        if not cfg.callback_url:
            raise ValueError(
                "Safaricom requires a callback_url. Set it on SafaricomConfig "
                "(this is the public URL Safaricom POSTs STK Push results to)."
            )
        res = await client.stk_push(SafaricomSTKPushRequest(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=request.reference,
            callback_url=cfg.callback_url,
            description=request.description or "Payment",
        ))
        return UnifiedPaymentResponse(
            provider="safaricom",
            status="pending",
            transaction_id=res.CheckoutRequestID,
            original_response=res,
        )

    async def _tigo_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        client: TigoClient = self._clients["tigo_pesa"]
        res = await client.stk_push(TigoSTKPushRequest(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=request.reference,
            customer_email=request.email,
        ))
        return UnifiedPaymentResponse(
            provider="tigo_pesa",
            status="pending",
            transaction_id=res.ReferenceID,
            original_response=res,
        )

    async def _airtel_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        client: AirtelClient = self._clients["airtel_money"]
        res = await client.stk_push(AirtelSTKPushRequest(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=request.reference,
        ))
        tx_id = (res.data.transaction.id if (res.data and res.data.transaction and res.data.transaction.id) else "UNKNOWN")
        return UnifiedPaymentResponse(
            provider="airtel_money",
            status="pending",
            transaction_id=tx_id,
            original_response=res,
        )

    async def _tips_adapter(self, request: UnifiedPaymentRequest) -> UnifiedPaymentResponse:
        client: TIPSClient = self._clients["tips"]
        res = await client.create_checkout(TIPSCheckoutRequest(
            account_number=request.phone_number,
            amount=request.amount,
            reference=request.reference,
            payer_name=request.name,
        ))
        return UnifiedPaymentResponse(
            provider="tips",
            status="pending",
            transaction_id=res.transaction_reference,
            original_response=res,
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def close(self):
        """Clean up all initialized async HTTP clients."""
        for client in self._clients.values():
            await client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
