import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

@pytest.fixture
def mock_rsa_keys():
    """Generates a real RSA keypair for mock encrypt/decrypt testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    # Export public key to PEM format as M-Pesa expects
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_key, public_pem

@pytest.fixture
def mpesa_api_key():
    return "dummy_mpesa_api_key_12345"

@pytest.fixture
def selcom_credentials():
    return {
        "api_key": "selcom_key_abc",
        "api_secret": "selcom_secret_xyz",
        "vendor_id": "VEND123"
    }
