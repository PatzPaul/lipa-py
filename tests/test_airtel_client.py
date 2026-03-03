import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.airtel_money import AirtelClient, AirtelSTKPushRequest

@pytest.fixture
def airtel_client():
    return AirtelClient(
        client_id="test_client",
        client_secret="test_secret",
        environment="sandbox"
    )

@pytest.mark.asyncio
async def test_airtel_authenticate_success(airtel_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mocked_airtel_token",
        "expires_in": "3599"
    }

    with patch.object(airtel_client.client, 'post', return_value=mock_response):
        await airtel_client._authenticate()
        
        assert airtel_client._access_token == "mocked_airtel_token"
        assert airtel_client._token_expires_at > 0

@pytest.mark.asyncio
async def test_airtel_stk_push_success(airtel_client):
    mock_auth_response = MagicMock()
    mock_auth_response.status_code = 200
    mock_auth_response.json.return_value = {
        "access_token": "mocked_token",
        "expires_in": "3599"
    }
    
    mock_stk_response = MagicMock()
    mock_stk_response.status_code = 200
    mock_stk_response.json.return_value = {
        "status": {"success": True},
        "data": {"transaction": {"id": "AIRTEL12345"}}
    }

    with patch.object(airtel_client.client, 'post', side_effect=[mock_auth_response, mock_stk_response]):
        request = AirtelSTKPushRequest(
            phone_number="255681234567",
            amount=500.0,
            reference="TestRef"
        )
        
        response = await airtel_client.stk_push(request)
        
        assert response.status.get("success") is True
        assert response.data.get("transaction").get("id") == "AIRTEL12345"
