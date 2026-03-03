import base64
from cryptography.hazmat.primitives.asymmetric import padding
from lipa_py.mpesa.crypto import encrypt_api_key

def test_mpesa_encrypt_api_key(mock_rsa_keys, mpesa_api_key):
    """
    Tests that encrypt_api_key correctly encrypts the M-Pesa API key
    using the provided public key PEM, and that the original data can be recovered
    using the corresponding private key (which M-Pesa's servers would do).
    """
    private_key, public_pem = mock_rsa_keys
    
    # Run the function
    encrypted_b64 = encrypt_api_key(mpesa_api_key, public_pem)
    
    # Must be a valid base64 string
    assert isinstance(encrypted_b64, str)
    
    # Decode it and attempt to decrypt it using the mock private key 
    encrypted_bytes = base64.b64decode(encrypted_b64)
    decrypted_bytes = private_key.decrypt(
        encrypted_bytes,
        padding.PKCS1v15()
    )
    
    # The decrypted result must exactly match the input
    assert decrypted_bytes.decode('utf-8') == mpesa_api_key
