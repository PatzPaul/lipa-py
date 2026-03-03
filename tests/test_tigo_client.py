import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.tigo_pesa import TigoClient, TigoSTKPushRequest

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
    mock_response.status_code = 200
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
    mock_auth_response.status_code = 200
    mock_auth_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }
    
    mock_stk_response = MagicMock()
    mock_stk_response.status_code = 200
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
