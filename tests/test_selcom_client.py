import pytest
import respx
import httpx
from lipa_py.selcom.client import SelcomClient, SelcomError
from lipa_py.selcom.schemas import SelcomCheckoutRequest

@pytest.fixture
def selcom_client(selcom_credentials):
    """Provides a Sandbox SelcomClient initialized with dummy credentials."""
    return SelcomClient(
        vendor_id=selcom_credentials["vendor_id"],
        api_key=selcom_credentials["api_key"],
        api_secret=selcom_credentials["api_secret"],
        environment="sandbox"
    )

@pytest.mark.asyncio
@respx.mock
async def test_selcom_create_checkout_success(selcom_client):
    """
    Mock Selcom server returning a valid checkout token.
    """
    mock_url = f"{selcom_client.base_url}/checkout/create-order"
    respx.post(mock_url).mock(return_value=httpx.Response(
        200, 
        json={
            "result": "SUCCESS",
            "message": "Order created successfully",
            "data": [
                {
                    "order_id": "ORD-123456",
                    "payment_token": "selcom_tkn_789",
                    "checkout_url": "https://selcom.example.com/checkout/ORD-123456"
                }
            ]
        }
    ))
    
    req = SelcomCheckoutRequest(
        vendor="VEND123",
        order_id="ORD-123456",
        buyer_email="customer@example.com",
        buyer_name="John Doe",
        buyer_phone="255754000000",
        amount=10000.0
    )
    
    response = await selcom_client.create_checkout(req)
    
    assert response.result == "SUCCESS"
    assert response.order_id == "ORD-123456"
    assert response.payment_token == "selcom_tkn_789"

@pytest.mark.asyncio
@respx.mock
async def test_selcom_http_error(selcom_client):
    """Ensures our custom SelcomError Exception is thrown when upstream fails."""
    mock_url = f"{selcom_client.base_url}/checkout/create-order"
    
    # Return 401 Unauthorized (e.g., bad HMAC signature)
    respx.post(mock_url).mock(return_value=httpx.Response(
        401, text="Invalid HMAC Signature"
    ))
    
    req = SelcomCheckoutRequest(
        vendor="VEND123",
        order_id="ORD-000",
        buyer_email="test@example.com",
        buyer_name="Test Person",
        buyer_phone="255123456789",
        amount=500.0
    )
    
    with pytest.raises(SelcomError) as excinfo:
        await selcom_client.create_checkout(req)
        
    assert "Selcom API request failed" in str(excinfo.value)
