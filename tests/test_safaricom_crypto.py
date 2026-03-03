import base64
from datetime import datetime
from lipa_py.safaricom.crypto import generate_password, generate_timestamp, generate_auth_header

def test_generate_timestamp():
    timestamp = generate_timestamp()
    assert len(timestamp) == 14
    # Ensure it's digits
    assert timestamp.isdigit()
    # Check if it corresponds roughly to now
    now_str = datetime.now().strftime("%Y%m%d")
    assert timestamp.startswith(now_str)

def test_generate_password():
    shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = "20231104150058"
    
    password = generate_password(shortcode, passkey, timestamp)
    expected_data = f"{shortcode}{passkey}{timestamp}"
    expected_password = base64.b64encode(expected_data.encode()).decode()
    
    assert password == expected_password

def test_generate_auth_header():
    consumer_key = "my_key"
    consumer_secret = "my_secret"
    
    auth_header = generate_auth_header(consumer_key, consumer_secret)
    expected_data = f"{consumer_key}:{consumer_secret}"
    expected_header = base64.b64encode(expected_data.encode()).decode()
    
    assert auth_header == expected_header
