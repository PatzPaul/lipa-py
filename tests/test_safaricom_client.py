import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.safaricom import SafaricomClient, SafaricomSTKPushRequest


def _http_status_error(status_code: int, text: str) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, text=text, request=request)
    return httpx.HTTPStatusError(text, request=request, response=response)

@pytest.fixture
def safaricom_client():
    return SafaricomClient(
        consumer_key="test_key",
        consumer_secret="test_secret",
        passkey="test_passkey",
        shortcode="174379",
        environment="sandbox"
    )

@pytest.mark.asyncio
async def test_authenticate_success(safaricom_client):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }

    with patch.object(safaricom_client.client, 'get', return_value=mock_response):
        await safaricom_client._authenticate()
        
        assert safaricom_client._access_token == "mocked_token"
        assert safaricom_client._token_expires_at > 0

@pytest.mark.asyncio
async def test_stk_push_success(safaricom_client):
    mock_auth_response = MagicMock()
    mock_auth_response.raise_for_status.return_value = None
    mock_auth_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }

    mock_stk_response = MagicMock()
    mock_stk_response.raise_for_status.return_value = None
    mock_stk_response.json.return_value = {
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": "ws_CO_191220191020363925",
        "ResponseCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "CustomerMessage": "Success. Request accepted for processing"
    }

    with patch.object(safaricom_client.client, 'get', return_value=mock_auth_response), \
         patch.object(safaricom_client.client, 'post', return_value=mock_stk_response):
        
        request = SafaricomSTKPushRequest(
            phone_number="254708374149",
            amount=1.0,
            reference="TestRef",
            callback_url="https://example.com/callback"
        )
        
        response = await safaricom_client.stk_push(request)
        
        assert response.ResponseCode == "0"
        assert response.MerchantRequestID == "29115-34620561-1"
        assert response.CheckoutRequestID == "ws_CO_191220191020363925"

@pytest.mark.asyncio
async def test_client_context_manager():
    async with SafaricomClient("key", "secret", "passkey", "shortcode") as client:
        assert isinstance(client, SafaricomClient)
    assert client.client.is_closed

@pytest.mark.asyncio
async def test_authenticate_failure_raises_safaricom_error(safaricom_client):
    from lipa_py.safaricom.client import SafaricomError
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = _http_status_error(401, "Unauthorized")

    with patch.object(safaricom_client.client, 'get', return_value=mock_response):
        with pytest.raises(SafaricomError) as excinfo:
            await safaricom_client._authenticate()
        assert "Safaricom authentication failed" in str(excinfo.value)

@pytest.mark.asyncio
async def test_stk_push_failure_raises_safaricom_error(safaricom_client):
    from lipa_py.safaricom.client import SafaricomError
    mock_auth_response = MagicMock()
    mock_auth_response.raise_for_status.return_value = None
    mock_auth_response.json.return_value = {"access_token": "tok", "expires_in": "3599"}

    mock_fail_response = MagicMock()
    mock_fail_response.raise_for_status.side_effect = _http_status_error(500, "Internal Server Error")

    with patch.object(safaricom_client.client, 'get', return_value=mock_auth_response), \
         patch.object(safaricom_client.client, 'post', return_value=mock_fail_response):
        request = SafaricomSTKPushRequest(
            phone_number="254708374149",
            amount=1.0,
            reference="TestRef",
            callback_url="https://example.com/callback"
        )
        with pytest.raises(SafaricomError) as excinfo:
            await safaricom_client.stk_push(request)
        assert "Safaricom STK Push failed" in str(excinfo.value)

@pytest.mark.asyncio
async def test_token_reused_on_second_call(safaricom_client):
    """Token cache: second call must NOT re-authenticate."""
    mock_auth = MagicMock()
    mock_auth.raise_for_status.return_value = None
    mock_auth.json.return_value = {"access_token": "cached_tok", "expires_in": "3599"}

    mock_stk = MagicMock()
    mock_stk.raise_for_status.return_value = None
    mock_stk.json.return_value = {
        "MerchantRequestID": "m1", "CheckoutRequestID": "c1",
        "ResponseCode": "0", "ResponseDescription": "OK", "CustomerMessage": "OK"
    }

    with patch.object(safaricom_client.client, 'get', return_value=mock_auth) as mock_get, \
         patch.object(safaricom_client.client, 'post', return_value=mock_stk):
        req = SafaricomSTKPushRequest(
            phone_number="254708374149", amount=1.0,
            reference="r1", callback_url="https://cb.example.com"
        )
        await safaricom_client.stk_push(req)
        await safaricom_client.stk_push(req)
        # GET /oauth only called once despite two stk_push calls
        assert mock_get.call_count == 1
