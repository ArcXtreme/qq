# backend/app/api/v1/token.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import RefreshToken, User
from app.core.security import create_access_token
from pydantic import BaseModel

router = APIRouter()

class RefreshIn(BaseModel):
    refresh_token: str

class RefreshOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/refresh", response_model=RefreshOut)
def refresh_token(payload: RefreshIn, db: Session = Depends(get_db)):
    rt = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == rt.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(subject=str(user.id))
    return {"access_token": access}
