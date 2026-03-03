import base64
from datetime import datetime

def generate_timestamp() -> str:
    """Generates the timestamp needed for Safaricom Daraja STK Push requests in format YYYYMMDDHHmmss"""
    return datetime.now().strftime("%Y%m%d%H%M%S")

def generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """
    Generates the base64 encoded password required for the STK Push request.
    Format: base64.encode(shortcode + passkey + timestamp)
    """
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data_to_encode.encode("utf-8")).decode("utf-8")

def generate_auth_header(consumer_key: str, consumer_secret: str) -> str:
    """
    Generates the base64 encoded authorization header for Daraja authentication.
    Format: base64.encode(consumer_key:consumer_secret)
    """
    auth_string = f"{consumer_key}:{consumer_secret}"
    return base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
