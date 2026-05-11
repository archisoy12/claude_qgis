import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

SECRET_KEY   = os.environ.get("JWT_SECRET", "change-this-secret")
ALGORITHM    = "HS256"
EXPIRE_HOURS = 24

ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "admin1234")
VIEWER_PASSWORD = os.environ.get("VIEWER_PASSWORD", "viewer1234")

bearer = HTTPBearer()


def create_token(role: str) -> str:
    payload = {
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")


def get_current_role(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    payload = decode_token(credentials.credentials)
    return payload["role"]


def require_admin(role: str = Depends(get_current_role)):
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return role


def require_any(role: str = Depends(get_current_role)):
    return role


def authenticate(password: str) -> Optional[str]:
    if password == ADMIN_PASSWORD:
        return "admin"
    if password == VIEWER_PASSWORD:
        return "viewer"
    return None
