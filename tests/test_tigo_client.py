import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.tigo_pesa import TigoClient, TigoSTKPushRequest


def _http_status_error(status_code: int, text: str) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, text=text, request=request)
    return httpx.HTTPStatusError(text, request=request, response=response)

@pytest.fixture
def tigo_client():
    return TigoClient(
        client_id="test_client",
        client_secret="test_secret",
        biller_code="12345",
        environment="sandbox"
    )

@pytest.mark.asyncio
async def test_tigo_authenticate_success(tigo_client):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "access_token": "mocked_tigo_token",
        "expires_in": "3599"
    }

    with patch.object(tigo_client.client, 'post', return_value=mock_response):
        await tigo_client._authenticate()
        
        assert tigo_client._access_token == "mocked_tigo_token"
        assert tigo_client._token_expires_at > 0

@pytest.mark.asyncio
async def test_tigo_stk_push_success(tigo_client):
    mock_auth_response = MagicMock()
    mock_auth_response.raise_for_status.return_value = None
    mock_auth_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }

    mock_stk_response = MagicMock()
    mock_stk_response.raise_for_status.return_value = None
    mock_stk_response.json.return_value = {
        "ResponseCode": "0000",
        "ResponseDescription": "Success",
        "ReferenceID": "TIGO12345"
    }

    with patch.object(tigo_client.client, 'post', side_effect=[mock_auth_response, mock_stk_response]):
        request = TigoSTKPushRequest(
            phone_number="255712345678",
            amount=1000.0,
            reference="TestRef"
        )

        response = await tigo_client.stk_push(request)

        assert response.ResponseCode == "0000"
        assert response.ReferenceID == "TIGO12345"

@pytest.mark.asyncio
async def test_tigo_authenticate_failure_raises_tigo_error(tigo_client):
    from lipa_py.tigo_pesa.client import TigoError
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = _http_status_error(401, "Unauthorized")

    with patch.object(tigo_client.client, 'post', return_value=mock_response):
        with pytest.raises(TigoError) as excinfo:
            await tigo_client._authenticate()
        assert "Failed to authenticate with Tigo" in str(excinfo.value)

@pytest.mark.asyncio
async def test_tigo_stk_push_failure_raises_tigo_error(tigo_client):
    from lipa_py.tigo_pesa.client import TigoError
    mock_auth = MagicMock()
    mock_auth.raise_for_status.return_value = None
    mock_auth.json.return_value = {"access_token": "tok", "expires_in": "3599"}

    mock_fail = MagicMock()
    mock_fail.raise_for_status.side_effect = _http_status_error(503, "Service Unavailable")

    with patch.object(tigo_client.client, 'post', side_effect=[mock_auth, mock_fail]):
        request = TigoSTKPushRequest(phone_number="255712345678", amount=500.0, reference="Ref")
        with pytest.raises(TigoError) as excinfo:
            await tigo_client.stk_push(request)
        assert "Tigo STK Push failed" in str(excinfo.value)

@pytest.mark.asyncio
async def test_tigo_context_manager():
    async with TigoClient("cid", "csecret", "bcode") as client:
        assert isinstance(client, TigoClient)
    assert client.client.is_closed
