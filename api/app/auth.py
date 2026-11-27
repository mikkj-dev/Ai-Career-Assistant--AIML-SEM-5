from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def issue_token(user: User, *, demo=False) -> str:
    expires = datetime.now(UTC) + timedelta(days=settings.jwt_ttl_days)
    return jwt.encode({"sub": str(user.id), "exp": expires, "demo": demo}, settings.jwt_secret, algorithm="HS256")


def verify_google(credential: str) -> dict:
    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in is unavailable")
    try:
        return id_token.verify_oauth2_token(credential, google_requests.Request(), settings.google_client_id)
    except ValueError as exc:
        raise HTTPException(401, "Invalid Google token") from exc


def optional_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                  db: Session = Depends(get_db)) -> User | None:
    if creds is None:
        return None
    try:
        claims = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"],
                            options={"require": ["exp", "sub"]})
        identifier = UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(401, "Invalid or expired token") from exc
    if claims.get("demo") and not settings.local_demo:
        raise HTTPException(401, "Local demo session is unavailable")
    user = db.get(User, identifier)
    if user is None or bool(claims.get("demo")) != user.synthetic:
        raise HTTPException(401, "User session is unavailable")
    return user


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(401, "Not signed in")
    return user
