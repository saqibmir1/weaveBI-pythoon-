import time
from typing import Dict
from jwt import encode, decode
from config.jwt_config import settings


def token_response(token: str):
    return {
        "access_token": token,
        "token_type": "Bearer"
    }
secret_key = settings.secret_key

def sign_jwt(email:str) -> Dict[str,str]:
    # set the expiry time
    payload = {"email": email, "expires": time.time()+86400}
    return token_response(encode(payload, secret_key, algorithm=settings.algorithm))


def decode_jwt(token:str) -> dict:
    decoded_token = decode(token.encode(), secret_key, algorithms=[settings.algorithm])
    return decoded_token if decoded_token["expires"] >= time.time() else {}