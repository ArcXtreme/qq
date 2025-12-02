# backend/app/api/v1/sync.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.models import SyncLog, SoilSample, Farm
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ClientRecord(BaseModel):
    client_id: str  # unique UUID from client
    record_type: str
    payload: Dict[str, Any]

class PushIn(BaseModel):
    records: List[ClientRecord]

class PushOutItem(BaseModel):
    client_id: str
    record_type: str
    server_id: Optional[int]

class PushOut(BaseModel):
    results: List[PushOutItem]

@router.post("/push", response_model=PushOut)
def sync_push(body: PushIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    results = []
    for rec in body.records:
        # Check idempotency: same user_id + client_id + record_type
        existing = db.query(SyncLog).filter(
            SyncLog.user_id == user.id,
            SyncLog.client_id == rec.client_id,
            SyncLog.record_type == rec.record_type
        ).first()
        if existing:
            results.append({"client_id": rec.client_id, "record_type": rec.record_type, "server_id": existing.server_id})
            continue

        server_id = None
        # handle known types
        try:
            if rec.record_type == "soil_sample":
                payload = rec.payload
                # payload must contain farm_id (client will use server farm_id or mapping)
                farm_id = payload.get("farm_id")
                # If farm_id is client-generated, mobile should push farm first; else assume correct
                ss = SoilSample(
                    farm_id=farm_id,
                    ph=payload.get("ph"),
                    n=payload.get("n"),
                    p=payload.get("p"),
                    k=payload.get("k"),
                    extra=payload.get("extra", None)
                )
                db.add(ss)
                db.commit()
                db.refresh(ss)
                server_id = ss.id
            elif rec.record_type == "farm":
                # For farms pushed from client (with geojson), create farm entry
                p = rec.payload
                # p should include name and geom (GeoJSON). We store geom as NULL here for simplicity OR try to convert.
                f = Farm(user_id=user.id, name=p.get("name"), area_ha=p.get("area_ha"))
                db.add(f)
                db.commit()
                db.refresh(f)
                server_id = f.id
            else:
                # For unknown types, just record payload
                pass

            sync = SyncLog(user_id=user.id, client_id=rec.client_id, record_type=rec.record_type, server_id=server_id, payload=rec.payload)
            db.add(sync)
            db.commit()
            results.append({"client_id": rec.client_id, "record_type": rec.record_type, "server_id": server_id})
        except IntegrityError:
            db.rollback()
            existing = db.query(SyncLog).filter(
                SyncLog.user_id == user.id,
                SyncLog.client_id == rec.client_id,
                SyncLog.record_type == rec.record_type
            ).first()
            server_id = existing.server_id if existing else None
            results.append({"client_id": rec.client_id, "record_type": rec.record_type, "server_id": server_id})
    return {"results": results}

class PullOutRecord(BaseModel):
    record_type: str
    server_id: int
    payload: Dict[str, Any]
    updated_at: Optional[datetime]

class PullOut(BaseModel):
    records: List[PullOutRecord]

@router.get("/pull", response_model=PullOut)
def sync_pull(since: Optional[str] = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Pull records changed since timestamp `since` (ISO format). If not provided, pull last 100 records.
    For demo we will pull soil_samples and farms.
    """
    q_since = None
    if since:
        try:
            q_since = datetime.fromisoformat(since)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid since timestamp. Use ISO format.")

    records = []
    # Farms
    farm_q = db.query(Farm).filter(Farm.user_id == user.id)
    if q_since:
        farm_q = farm_q.filter(Farm.created_at >= q_since)
    farms = farm_q.limit(200).all()
    for f in farms:
        payload = {"id": f.id, "name": f.name, "area_ha": f.area_ha}
        records.append({"record_type": "farm", "server_id": f.id, "payload": payload, "updated_at": f.created_at})

    # Soil samples
    ss_q = db.query(SoilSample).join(Farm).filter(Farm.user_id == user.id)
    if q_since:
        ss_q = ss_q.filter(SoilSample.sample_date >= q_since)
    soils = ss_q.limit(500).all()
    for s in soils:
        payload = {"id": s.id, "farm_id": s.farm_id, "ph": s.ph, "n": s.n, "p": s.p, "k": s.k, "extra": s.extra}
        records.append({"record_type": "soil_sample", "server_id": s.id, "payload": payload, "updated_at": s.sample_date})

    return {"records": records}
