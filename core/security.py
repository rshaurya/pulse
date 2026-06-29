import jwt

from datetime import datetime, timedelta, timezone

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
    
def create_magic_token(email: str) -> str:
    """Creates a temporary, cryptographically signed VIP pass valid for 15 minutes."""
    
    # Set the expiration time
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Create the payload (The data written on the VIP pass)
    # 'sub' stands for subject (who this belongs to)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "magic_link"
    }
    
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_magic_token(token: str) -> str:
    """Checks the jwt secret key. Returns the email if valid, or None if fake/expired."""
    try:
        # Attempt to decode using our exact secret key
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        
        # Verify it's actually a magic link and not some other type of token
        if payload.get("type") != "magic_link":
            return None
            
        return payload.get("sub")
        
    except jwt.ExpiredSignatureError:
        print("[SECURITY] A user tried to use an expired magic link.")
        return None
    except jwt.InvalidTokenError:
        print("[SECURITY] A user tried to use a forged or invalid token.")
        return None
