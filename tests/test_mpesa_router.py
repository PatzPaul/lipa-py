import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lipa_py.mpesa.router import mpesa_router, set_webhook_handler, webhook_registry
from lipa_py.mpesa.schemas import MpesaWebhookData


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure each test starts with a clean handler registry."""
    webhook_registry.clear()
    yield
    webhook_registry.clear()


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(mpesa_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_webhook_no_handler_returns_200(client):
    """Without a handler registered, the endpoint must still return 200."""
    payload = {
        "input_TransactionID": "TX123",
        "input_ResultCode": "0",
        "input_ResultDesc": "Success",
        "input_ThirdPartyConversationID": "CONV1"
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_webhook_dispatches_to_registered_handler(client):
    """A registered default handler must be called with the parsed webhook data."""
    received = []

    async def my_handler(data: MpesaWebhookData):
        received.append(data)

    set_webhook_handler(my_handler)

    payload = {
        "input_TransactionID": "TX999",
        "input_ResultCode": "0",
        "input_ResultDesc": "Success",
        "input_ThirdPartyConversationID": "CONV99"
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    # TestClient runs background tasks synchronously
    assert len(received) == 1
    assert received[0].input_TransactionID == "TX999"


def test_set_webhook_handler_rejects_sync_function():
    """set_webhook_handler must reject non-async callables."""

    def sync_handler(data: MpesaWebhookData):
        pass

    with pytest.raises(ValueError, match="async"):
        set_webhook_handler(sync_handler)


def test_webhook_accepts_extra_fields(client):
    """MpesaWebhookData allows extra fields — unknown keys must not cause 422."""
    payload = {
        "input_TransactionID": "TX1",
        "input_ResultCode": "0",
        "input_ResultDesc": "Desc",
        "input_ThirdPartyConversationID": "C1",
        "unknown_field": "some_value"
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
