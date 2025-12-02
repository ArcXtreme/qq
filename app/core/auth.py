# backend/app/core/auth.py
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User

# This defines a Bearer auth security scheme for Swagger/OpenAPI
bearer_scheme = HTTPBearer(auto_error=True)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Read JWT only from the Authorization: Bearer <token> header.
    This also registers a proper HTTP Bearer security scheme in OpenAPI,
    so Swagger shows the Authorize (lock) button.
    """
    raw_token: str = credentials.credentials

    payload = decode_token(raw_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
