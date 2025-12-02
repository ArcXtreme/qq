from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db, Base, engine
from app.schemas.schemas import UserCreate, Token, UserOut
from app.models.models import User
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

# Create DB tables if not present (simple approach for hackathon)
Base.metadata.create_all(bind=engine)

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if user:
        raise HTTPException(status_code=400, detail="Phone already registered")
    hashed = get_password_hash(payload.password)
    new = User(name=payload.name, phone=payload.phone, hashed_password=hashed, language_preference=payload.language_preference)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
