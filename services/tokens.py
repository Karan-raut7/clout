import secrets
import hashlib


def generate_verification_token():
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    return token, token_hash