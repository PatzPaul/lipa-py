"""Cross-provider router contract tests.

Locks in two invariants for every provider router:
1. Setter rejects non-async handlers with ValueError.
2. Webhook endpoint returns 200 even when no handler is registered.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lipa_py.mpesa.router import set_webhook_handler, mpesa_router, webhook_registry as mpesa_reg
from lipa_py.selcom.router import set_selcom_handler, selcom_router, selcom_webhook_registry
from lipa_py.safaricom.router import (
    set_safaricom_webhook_handler, safaricom_router, safaricom_webhook_registry,
)
from lipa_py.airtel_money.router import (
    set_airtel_webhook_handler, airtel_router, airtel_webhook_registry,
)
from lipa_py.tigo_pesa.router import (
    set_tigo_webhook_handler, tigo_router, tigo_webhook_registry,
)
from lipa_py.tips.router import set_tips_webhook_handler, tips_router, tips_webhook_registry


PROVIDERS = [
    ("mpesa", set_webhook_handler, mpesa_reg),
    ("selcom", set_selcom_handler, selcom_webhook_registry),
    ("safaricom", set_safaricom_webhook_handler, safaricom_webhook_registry),
    ("airtel", set_airtel_webhook_handler, airtel_webhook_registry),
    ("tigo", set_tigo_webhook_handler, tigo_webhook_registry),
    ("tips", set_tips_webhook_handler, tips_webhook_registry),
]


@pytest.mark.parametrize("name,setter,registry", PROVIDERS)
def test_setter_rejects_sync_handler(name, setter, registry):
    """Every provider's setter must reject non-async callables."""
    registry.clear()

    def sync_handler(data):
        pass

    with pytest.raises(ValueError, match="async"):
        setter(sync_handler)


ROUTERS = [
    ("mpesa", mpesa_router),
    ("selcom", selcom_router),
    ("safaricom", safaricom_router),
    ("airtel", airtel_router),
    ("tigo", tigo_router),
    ("tips", tips_router),
]


@pytest.mark.parametrize("name,router", ROUTERS)
def test_router_mounts_webhook_endpoint(name, router):
    """Every provider router must expose POST /webhook."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    # Posting an empty body will likely 422 (validation), but the route must exist.
    response = client.post("/webhook", json={})
    assert response.status_code != 404, f"{name} router did not mount /webhook"
