import pytest
from unittest.mock import patch, MagicMock
from lipa_py.safaricom import SafaricomClient, SafaricomSTKPushRequest

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
    mock_response.status_code = 200
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
    mock_auth_response.status_code = 200
    mock_auth_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }
    
    mock_stk_response = MagicMock()
    mock_stk_response.status_code = 200
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
