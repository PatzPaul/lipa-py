import pytest
import httpx
from unittest.mock import patch, MagicMock
from lipa_py.tips import TIPSClient, TIPSCheckoutRequest

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
    mock_stk_response.status_code = 200
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
