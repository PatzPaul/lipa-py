"""Webhook dispatch tests.

Verifies that posting a valid payload to each provider's /webhook endpoint:
1. Returns 200 immediately
2. Schedules the registered handler via BackgroundTasks

Uses an autouse fixture to clear all webhook registries between tests so
handlers registered in one test don't leak into the next (global singleton risk).
"""
import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lipa_py.mpesa.router import mpesa_router, set_webhook_handler, webhook_registry as mpesa_reg
from lipa_py.selcom.router import selcom_router, set_selcom_handler, selcom_webhook_registry
from lipa_py.safaricom.router import safaricom_router, set_safaricom_webhook_handler, safaricom_webhook_registry
from lipa_py.airtel_money.router import airtel_router, set_airtel_webhook_handler, airtel_webhook_registry
from lipa_py.tigo_pesa.router import tigo_router, set_tigo_webhook_handler, tigo_webhook_registry
from lipa_py.tips.router import tips_router, set_tips_webhook_handler, tips_webhook_registry

from lipa_py.mpesa.schemas import MpesaWebhookData
from lipa_py.selcom.schemas import SelcomWebhookData
from lipa_py.safaricom.schemas import SafaricomWebhookData
from lipa_py.airtel_money.schemas import AirtelWebhookData
from lipa_py.tigo_pesa.schemas import TigoWebhookData
from lipa_py.tips.schemas import TIPSWebhookData


ALL_REGISTRIES = [
    mpesa_reg, selcom_webhook_registry, safaricom_webhook_registry,
    airtel_webhook_registry, tigo_webhook_registry, tips_webhook_registry,
]


@pytest.fixture(autouse=True)
def clear_registries():
    """Isolate registry state between tests — prevents handler bleed-over."""
    for reg in ALL_REGISTRIES:
        reg.clear()
    yield
    for reg in ALL_REGISTRIES:
        reg.clear()


def _make_app(router):
    app = FastAPI()
    app.include_router(router)
    return app


# ── M-Pesa ────────────────────────────────────────────────────────────────────

def test_mpesa_webhook_dispatch():
    received: list[MpesaWebhookData] = []

    async def handler(data: MpesaWebhookData) -> None:
        received.append(data)

    set_webhook_handler(handler)
    client = TestClient(_make_app(mpesa_router))

    payload = {
        "input_TransactionID": "TX001",
        "input_ResultCode": "0",
        "input_ResultDesc": "Success",
        "input_ThirdPartyConversationID": "CONV001",
    }
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].input_TransactionID == "TX001"


# ── Selcom ────────────────────────────────────────────────────────────────────

def test_selcom_webhook_dispatch():
    received: list[SelcomWebhookData] = []

    async def handler(data: SelcomWebhookData) -> None:
        received.append(data)

    set_selcom_handler(handler)
    client = TestClient(_make_app(selcom_router))

    payload = {
        "transid": "SEL001",
        "reference": "REF001",
        "amount": 5000.0,
        "currency": "TZS",
        "gateway_buyer_uuid": "uuid-123",
        "gateway_buyer_msisdn": "255754000000",
        "resultcode": "000",
        "result": "SUCCESS",
    }
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].transid == "SEL001"
    assert received[0].is_successful() is True


# ── Safaricom ─────────────────────────────────────────────────────────────────

def test_safaricom_webhook_dispatch():
    received: list[SafaricomWebhookData] = []

    async def handler(data: SafaricomWebhookData) -> None:
        received.append(data)

    set_safaricom_webhook_handler(handler)
    client = TestClient(_make_app(safaricom_router))

    payload = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "MR1",
                "CheckoutRequestID": "ws_CO_123",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
            }
        }
    }
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].Body.stkCallback.ResultCode == 0


# ── Airtel ────────────────────────────────────────────────────────────────────

def test_airtel_webhook_dispatch():
    received: list[AirtelWebhookData] = []

    async def handler(data: AirtelWebhookData) -> None:
        received.append(data)

    set_airtel_webhook_handler(handler)
    client = TestClient(_make_app(airtel_router))

    payload = {"transaction_id": "AIRTEL_TX_001", "status": "TS", "message": "Success"}
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].transaction_id == "AIRTEL_TX_001"


# ── Tigo ──────────────────────────────────────────────────────────────────────

def test_tigo_webhook_dispatch():
    received: list[TigoWebhookData] = []

    async def handler(data: TigoWebhookData) -> None:
        received.append(data)

    set_tigo_webhook_handler(handler)
    client = TestClient(_make_app(tigo_router))

    payload = {"ReferenceID": "TIGO_REF_001", "Status": "SUCCESS", "Description": "Paid"}
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].ReferenceID == "TIGO_REF_001"


# ── TIPS ──────────────────────────────────────────────────────────────────────

def test_tips_webhook_dispatch():
    received: list[TIPSWebhookData] = []

    async def handler(data: TIPSWebhookData) -> None:
        received.append(data)

    set_tips_webhook_handler(handler)
    client = TestClient(_make_app(tips_router))

    payload = {
        "transaction_reference": "TIPS_REF_001",
        "status": "APPROVED",
        "status_code": "00",
        "amount": 1000.0,
    }
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert len(received) == 1
    assert received[0].transaction_reference == "TIPS_REF_001"


# ── No handler registered ─────────────────────────────────────────────────────

def test_webhook_returns_200_without_handler():
    """All routers must respond 200 even when no handler is registered."""
    client = TestClient(_make_app(mpesa_router))
    payload = {"input_TransactionID": "TX999"}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
