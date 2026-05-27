from cryptography.fernet import Fernet
from core.config import settings

# Initialize the Fernet cipher suite using your Master Key
# If the key is missing or invalid, the app will refuse to boot.
try:
    _cipher_suite = Fernet(settings.ENCRYPTION_MASTER_KEY.encode())
except ValueError:
    raise ValueError("[SECURITY FATAL] ENCRYPTION_MASTER_KEY is invalid or missing. Check your .env file.")

def encrypt_api_key(plaintext_key: str) -> str:
    """
    Takes a plaintext API key (e.g., 'gsk_12345') and encrypts it into a 
    secure Fernet token for database storage.
    """
    if not plaintext_key:
        return None
        
    # Fernet requires bytes, so we encode the string, encrypt it, and decode it back to a string for Postgres
    encrypted_bytes = _cipher_suite.encrypt(plaintext_key.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_api_key(encrypted_token: str) -> str:
    """
    Takes the encrypted Fernet token from PostgreSQL and decrypts it back 
    into a usable API key.
    """
    if not encrypted_token:
        return None
        
    try:
        decrypted_bytes = _cipher_suite.decrypt(encrypted_token.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"[SECURITY ALERT] Failed to decrypt an API key. Was the Master Key changed? Error: {e}")
        return None