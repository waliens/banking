from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    token: str = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    token: str = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token


def decode_refresh_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return None
        return int(payload["sub"])
    except Exception:
        return None
