# backend/app/api/v1/device.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.models.models import Device, RefreshToken
from app.schemas.schemas import DeviceBindOut

from app.core.security import create_access_token
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/bind", response_model=DeviceBindOut)

def bind_device(device_uid: str, user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Bind a device UID to the user and create a refresh token tied to device.
    Client provides a device_uid (UUID) from the mobile app.
    """
    d = db.query(Device).filter(Device.device_uid == device_uid, Device.user_id == user.id).first()
    if not d:
        d = Device(user_id=user.id, device_uid=device_uid)
        db.add(d)
        db.commit()
        db.refresh(d)

    # Create refresh token (random UUID)
    refresh_token = str(uuid.uuid4())
    rt = RefreshToken(user_id=user.id, device_id=d.id, token=refresh_token)
    db.add(rt)
    db.commit()

    # Also return access token for immediate use
    access = create_access_token(subject=str(user.id))
    return {"access_token": access, "token_type": "bearer", "refresh_token": refresh_token}
