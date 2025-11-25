from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()

fernet = Fernet(settings.fernet_encryption_key.encode())

def encrypt_refresh_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode('utf-8')

def decrypt_refresh_token(token: str) -> str:
    return fernet.decrypt(token.encode()).decode('utf-8')
