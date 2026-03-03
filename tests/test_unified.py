import pytest
import respx
import httpx
from lipa_py.unified import UnifiedPaymentClient, UnifiedPaymentRequest, UnifiedPaymentResponse

@pytest.fixture
def unified_client(mock_rsa_keys, mpesa_api_key, selcom_credentials):
    """Provides the Orchestrator initialized with both M-Pesa and Selcom"""
    _, public_pem = mock_rsa_keys
    
    config = {
        "mpesa": {
            "api_key": mpesa_api_key,
            "public_key": public_pem,
            "environment": "sandbox"
        },
        "selcom": {
            "vendor_id": selcom_credentials["vendor_id"],
            "api_key": selcom_credentials["api_key"],
            "api_secret": selcom_credentials["api_secret"],
            "environment": "sandbox"
        },
        "safaricom": {
            "consumer_key": "test_safaricom",
            "consumer_secret": "test_safaricom_secret",
            "passkey": "test",
            "shortcode": "123",
            "environment": "sandbox"
        },
        "tigo_pesa": {
            "client_id": "test_tigo",
            "client_secret": "test_tigo_secret",
            "biller_code": "123",
            "environment": "sandbox"
        },
        "airtel_money": {
            "client_id": "test_airtel",
            "client_secret": "test_airtel_secret",
            "environment": "sandbox"
        },
        "tips": {
            "api_key": "test_tips",
            "institution_id": "test",
            "environment": "sandbox"
        }
    }
    
    return UnifiedPaymentClient(config)
    
def test_unified_detect_provider(unified_client):
    """Ensure it correctly parses Tanzania phone number prefixes"""
    
    # 075-> Vodacom M-Pesa
    assert unified_client._detect_provider("0754000000") == "mpesa"
    assert unified_client._detect_provider("255762000000") == "mpesa"
    assert unified_client._detect_provider("0742123456") == "mpesa"
    
    # 071, 065 -> Tigo Pesa
    assert unified_client._detect_provider("255716000000") == "tigo_pesa"
    assert unified_client._detect_provider("0654123123") == "tigo_pesa"

    # 078, 068 -> Airtel Money
    assert unified_client._detect_provider("255786000000") == "airtel_money"
    assert unified_client._detect_provider("0684123123") == "airtel_money"

    # 254 -> Safaricom Kenya
    assert unified_client._detect_provider("254708374149") == "safaricom"

@pytest.mark.asyncio
@respx.mock
async def test_unified_request_payment_mpesa_route(unified_client):
    """Tests the orchestrator translating the abstract request precisely down to M-Pesa client"""
    
    mpesa_client = unified_client._clients["mpesa"]
    
    # Mock specific MPesa Endpoints
    session_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/getSession/"
    respx.get(session_url).mock(return_value=httpx.Response(
        200, json={"output_ResponseCode": "0", "output_ResponseDesc": "Success", "output_SessionID": "token"}
    ))
    
    push_url = f"{mpesa_client.base_url}/ipg/v2/vodacomTZN/c2bPayment/singleStage/"
    respx.post(push_url).mock(return_value=httpx.Response(
        200, json={
            "output_ResponseCode": "0",
            "output_ResponseDesc": "Success",
            "output_TransactionID": "123",
            "output_ConversationID": "CONV_ABC",
            "output_ThirdPartyConversationID": "123"
        }
    ))
    
    request = UnifiedPaymentRequest(
        phone_number="0754000000", # Implicitly M-Pesa
        amount=5000,
        reference="TICKET"
    )
    
    unified_response = await unified_client.request_payment(request)
    
    assert isinstance(unified_response, UnifiedPaymentResponse)
    assert unified_response.provider == "mpesa"
    assert unified_response.transaction_id == "CONV_ABC"
    assert unified_response.status == "pending"
