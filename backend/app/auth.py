import os, hmac, hashlib, time, base64
from fastapi import Header, HTTPException

SECRET = os.getenv("AUTH_SECRET", "change-this-secret")
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "changeme")
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

def _sign(payload: str) -> str:
    return hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()

def create_token(username: str) -> str:
    expiry = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{username}:{expiry}"
    sig = _sign(payload)
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def verify_token(token: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, expiry, sig = raw.rsplit(":", 2)
        if _sign(f"{username}:{expiry}") != sig:
            return False
        if int(expiry) < time.time():
            return False
        return True
    except Exception:
        return False

def check_credentials(username: str, password: str) -> bool:
    return username == APP_USERNAME and password == APP_PASSWORD

async def require_auth(authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return True