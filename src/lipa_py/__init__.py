"""
lipa-py
A modern, async-first Python package designed to integrate Tanzanian Mobile Network Operators
and Gateways into Python backend applications.
"""

from lipa_py.unified.client import UnifiedPaymentClient
from lipa_py.unified.schemas import (
    UnifiedPaymentRequest,
    UnifiedPaymentResponse,
    UnifiedPaymentConfig,
    MpesaConfig,
    SelcomConfig,
    SafaricomConfig,
    TigoConfig,
    AirtelConfig,
    TIPSConfig,
)

from lipa_py.mpesa.client import MPesaClient, MpesaError
from lipa_py.mpesa.schemas import STKPushRequest, MpesaResponse, MpesaWebhookData

from lipa_py.selcom.client import SelcomClient, SelcomError
from lipa_py.selcom.schemas import SelcomCheckoutRequest, SelcomCheckoutResponse, SelcomWebhookData

from lipa_py.safaricom.client import SafaricomClient, SafaricomError
from lipa_py.safaricom.schemas import SafaricomSTKPushRequest, SafaricomSTKPushResponse, SafaricomWebhookData

from lipa_py.airtel_money.client import AirtelClient, AirtelError
from lipa_py.airtel_money.schemas import AirtelSTKPushRequest, AirtelSTKPushResponse, AirtelWebhookData

from lipa_py.tigo_pesa.client import TigoClient, TigoError
from lipa_py.tigo_pesa.schemas import TigoSTKPushRequest, TigoSTKPushResponse, TigoWebhookData

from lipa_py.tips.client import TIPSClient, TIPSError
from lipa_py.tips.schemas import TIPSCheckoutRequest, TIPSCheckoutResponse, TIPSWebhookData

__version__ = "0.1.3"
__all__ = [
    # Unified
    "UnifiedPaymentClient",
    "UnifiedPaymentConfig",
    "UnifiedPaymentRequest",
    "UnifiedPaymentResponse",
    # Provider config models
    "MpesaConfig",
    "SelcomConfig",
    "SafaricomConfig",
    "TigoConfig",
    "AirtelConfig",
    "TIPSConfig",
    # M-Pesa
    "MPesaClient",
    "MpesaError",
    "STKPushRequest",
    "MpesaResponse",
    "MpesaWebhookData",
    # Selcom
    "SelcomClient",
    "SelcomError",
    "SelcomCheckoutRequest",
    "SelcomCheckoutResponse",
    "SelcomWebhookData",
    # Safaricom
    "SafaricomClient",
    "SafaricomError",
    "SafaricomSTKPushRequest",
    "SafaricomSTKPushResponse",
    "SafaricomWebhookData",
    # Airtel Money
    "AirtelClient",
    "AirtelError",
    "AirtelSTKPushRequest",
    "AirtelSTKPushResponse",
    "AirtelWebhookData",
    # Tigo Pesa
    "TigoClient",
    "TigoError",
    "TigoSTKPushRequest",
    "TigoSTKPushResponse",
    "TigoWebhookData",
    # TIPS
    "TIPSClient",
    "TIPSError",
    "TIPSCheckoutRequest",
    "TIPSCheckoutResponse",
    "TIPSWebhookData",
]
