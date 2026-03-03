import pytest
import respx
import httpx
from lipa_py.mpesa.client import MPesaClient, MpesaError
from lipa_py.mpesa.schemas import STKPushRequest

@pytest.fixture
def mpesa_client(mock_rsa_keys, mpesa_api_key):
    """Provides a Sandbox MPesaClient initialized with valid-looking keys."""
    _, public_pem = mock_rsa_keys
    return MPesaClient(
        api_key=mpesa_api_key, 
        public_key=public_pem,
        environment="sandbox"
    )

@pytest.mark.asyncio
@respx.mock
async def test_mpesa_get_session_token_success(mpesa_client):
    """
    Mock Mpesa server returning a valid SessionToken from /getSession/
    """
    # Create the mock endpoint matching MPesaClient init base_url + path
    mock_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/getSession/"
    respx.get(mock_url).mock(return_value=httpx.Response(
        200, 
        json={
            "output_ResponseCode": "INS-0",
            "output_ResponseDesc": "Request processed successfully",
            "output_SessionID": "mock_session_token_xyz"
        }
    ))
    
    # Run the client method directly
    session_token = await mpesa_client._get_session_token()
    
    assert session_token == "mock_session_token_xyz"

@pytest.mark.asyncio
@respx.mock
async def test_mpesa_stk_push_success(mpesa_client):
    """
    Mock an STK Push which requires:
    1. Getting a session token via GET /getSession/
    2. Pushing the payload to POST /c2bPayment/singleStage/
    """
    session_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/getSession/"
    respx.get(session_url).mock(return_value=httpx.Response(
        200, json={"output_ResponseCode": "0", "output_ResponseDesc": "Success", "output_SessionID": "token_123"}
    ))
    
    push_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/c2bPayment/singleStage/"
    respx.post(push_url).mock(return_value=httpx.Response(
        200, json={
            "output_ResponseCode": "0",
            "output_ResponseDesc": "Success",
            "output_TransactionID": "MPX123456",
            "output_ConversationID": "CONV_ABC",
            "output_ThirdPartyConversationID": "TICK-789"
        }
    ))
    
    # Initialize Request Schema
    req = STKPushRequest(
        phone_number="255754000000",
        amount=1500,
        reference="TICK-789",
        third_party_conversation_id="TICK-789"
    )
    
    response = await mpesa_client.stk_push(req)
    
    # Verify Schema parsed response
    assert response.output_TransactionID == "MPX123456"
    assert response.output_ConversationID == "CONV_ABC"
    
@pytest.mark.asyncio
@respx.mock
async def test_mpesa_http_error(mpesa_client):
    """Ensures our custom MpesaError Exception is thrown when upstream fails (401, 500, etc)."""
    session_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/getSession/"
    
    # Return 401 Unauthorized
    respx.get(session_url).mock(return_value=httpx.Response(
        401, text="Invalid API Key or Public Key"
    ))
    
    with pytest.raises(MpesaError) as excinfo:
        await mpesa_client._get_session_token()
        
    assert "Failed to get session token" in str(excinfo.value)
