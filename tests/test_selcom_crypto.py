import hmac
import base64
import hashlib
from lipa_py.selcom.crypto import generate_selcom_signature, get_iso_timestamp

def test_selcom_crypto_signature(selcom_credentials):
    """
    Tests that generate_selcom_signature correctly creates an HMAC-SHA256 hash.
    It verifies the base64 encoding matches standard expectations.
    """
    api_key = selcom_credentials["api_key"]
    api_secret = selcom_credentials["api_secret"]
    timestamp = get_iso_timestamp()
    
    # Run the function
    signature = generate_selcom_signature(api_key, api_secret, timestamp)
    
    # Recreate signature logic inline to ensure consistency
    expected_message = f"timestamp={timestamp}&apikey={api_key}"
    expected_hmac = hmac.new(
        key=api_secret.encode("utf-8"),
        msg=expected_message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(expected_hmac).decode("utf-8")
    
    assert signature == expected_signature
    
def test_selcom_iso_timestamp():
    """Ensure timestamp properly formats as ISO 8601 for Selcom headers."""
    ts = get_iso_timestamp()
    
    assert "T" in ts
    assert "Z" in ts
