from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.models import SoilSample, Farm, User
from app.schemas.schemas import SoilSampleIn, SoilSampleOut, SoilSampleUpdate

router = APIRouter()


@router.post("/", response_model=SoilSampleOut)
def create_soil_sample(
    payload: SoilSampleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new soil sample for a farm"""
    # validate farm ownership
    farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or not owned by user")
    
    s = SoilSample(
        farm_id=payload.farm_id,
        ph=payload.ph,
        n=payload.n,
        p=payload.p,
        k=payload.k,
        extra=payload.extra
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/", response_model=List[SoilSampleOut])
def list_all_soil_samples(
    farm_id: Optional[int] = Query(None, description="Filter by farm ID"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all soil samples for the user, optionally filtered by farm_id"""
    query = db.query(SoilSample).join(Farm).filter(Farm.user_id == user.id)
    
    if farm_id is not None:
        # Verify farm ownership
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == user.id).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found or not owned by user")
        query = query.filter(SoilSample.farm_id == farm_id)
    
    samples = query.order_by(SoilSample.sample_date.desc()).all()
    return samples


@router.get("/farm/{farm_id}", response_model=List[SoilSampleOut])
def list_soil_samples_for_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all soil samples for a specific farm"""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or not owned by user")
    
    samples = db.query(SoilSample).filter(SoilSample.farm_id == farm_id).order_by(SoilSample.sample_date.desc()).all()
    return samples


@router.get("/{sample_id}", response_model=SoilSampleOut)
def get_soil_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific soil sample by ID"""
    s = db.query(SoilSample).filter(SoilSample.id == sample_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Soil sample not found")
    
    # Verify farm ownership
    if s.farm.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return s


@router.put("/{sample_id}", response_model=SoilSampleOut)
@router.patch("/{sample_id}", response_model=SoilSampleOut)
def update_soil_sample(
    sample_id: int,
    payload: SoilSampleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update a soil sample"""
    s = db.query(SoilSample).filter(SoilSample.id == sample_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Soil sample not found")
    
    # Verify farm ownership
    if s.farm.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields if provided
    if payload.ph is not None:
        s.ph = payload.ph
    if payload.n is not None:
        s.n = payload.n
    if payload.p is not None:
        s.p = payload.p
    if payload.k is not None:
        s.k = payload.k
    if payload.extra is not None:
        s.extra = payload.extra
    
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{sample_id}")
def delete_soil_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a soil sample"""
    s = db.query(SoilSample).filter(SoilSample.id == sample_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Soil sample not found")
    
    # Verify farm ownership
    if s.farm.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(s)
    db.commit()
    return {"message": "Soil sample deleted successfully"}
