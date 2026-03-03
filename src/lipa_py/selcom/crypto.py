import base64
import hashlib
import hmac
from datetime import datetime, timezone

def generate_selcom_signature(
    api_key: str, 
    api_secret: str, 
    timestamp: str, 
    data: dict = None
) -> str:
    """
    Generates a HMAC-SHA256 signature for Selcom API requests.
    Selcom typically requires a signature created from hashing the timestamp
    and specific payload parameters with the API secret.
    """
    # For a simplified MVP, we use the timestamp and API key.
    # Selcom's exact signature logic expects ordered query string or JSON payload components.
    # This is a general representation of HMAC-SHA256 for payment gateways like Selcom.
    message = f"timestamp={timestamp}&apikey={api_key}"
    
    # Generate HMAC using SHA256
    signature = hmac.new(
        key=api_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    
    # Return Base64 encoded signature
    return base64.b64encode(signature).decode("utf-8")

def get_iso_timestamp() -> str:
    """Returns current timestamp in ISO 8601 format required by Selcom."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%zZ")
