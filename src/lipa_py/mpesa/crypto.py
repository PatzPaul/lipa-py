import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def encrypt_api_key(api_key: str, public_key_pem: str) -> str:
    """
    Encrypts the API key using the Tanzanian MNO's provided RSA Public Key.
    The output is a base64 encoded string of the encrypted payload.
    """
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    
    encrypted_key = public_key.encrypt(
        api_key.encode("utf-8"),
        padding.PKCS1v15()
    )
    
    # Base64 encode the encrypted bytes and convert to string
    return base64.b64encode(encrypted_key).decode("utf-8")
