import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.tips import TIPSClient, TIPSCheckoutRequest


def _http_status_error(status_code: int, text: str) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, text=text, request=request)
    return httpx.HTTPStatusError(text, request=request, response=response)

@pytest.fixture
def tips_client():
    return TIPSClient(
        api_key="test_api_key",
        institution_id="INST001",
        environment="sandbox"
    )

@pytest.mark.asyncio
async def test_tips_checkout_success(tips_client):
    mock_stk_response = MagicMock()
    mock_stk_response.raise_for_status.return_value = None
    mock_stk_response.json.return_value = {
        "transaction_reference": "TIPS12345",
        "status": "APPROVED",
        "message": "Transaction Processed"
    }

    with patch.object(tips_client.client, 'post', return_value=mock_stk_response):
        request = TIPSCheckoutRequest(
            account_number="255123456789",
            amount=5000.0,
            reference="TestRef"
        )

        response = await tips_client.create_checkout(request)

        assert response.transaction_reference == "TIPS12345"
        assert response.status == "APPROVED"
        assert response.message == "Transaction Processed"

@pytest.mark.asyncio
async def test_tips_checkout_failure_raises_tips_error(tips_client):
    from lipa_py.tips.client import TIPSError
    mock_fail = MagicMock()
    mock_fail.raise_for_status.side_effect = _http_status_error(400, "Bad Request")

    with patch.object(tips_client.client, 'post', return_value=mock_fail):
        request = TIPSCheckoutRequest(account_number="255123456789", amount=100.0, reference="Ref")
        with pytest.raises(TIPSError) as excinfo:
            await tips_client.create_checkout(request)
        assert "TIPS Checkout failed" in str(excinfo.value)

@pytest.mark.asyncio
async def test_tips_context_manager():
    async with TIPSClient(api_key="k", institution_id="I") as client:
        assert isinstance(client, TIPSClient)
    assert client.client.is_closed
