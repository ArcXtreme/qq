from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Farm, User
from app.schemas.schemas import FarmCreate, FarmOut, FarmUpdate
from shapely.geometry import shape, mapping
from geoalchemy2.shape import from_shape, to_shape
from app.core.auth import get_current_user

router = APIRouter()


def wkb_to_geojson(wkb_element):
    """Convert WKBElement to GeoJSON dict"""
    if wkb_element is None:
        return None
    shapely_geom = to_shape(wkb_element)
    return mapping(shapely_geom)


def calculate_area_ha(geom_obj, db: Session = None):
    """Calculate area in hectares using geodesic calculation"""
    try:
        if geom_obj.geom_type == 'Polygon':
            # Use Shapely's area (planar in degrees) and convert to hectares
            # For WGS84 (EPSG:4326), we need to account for latitude
            coords = list(geom_obj.exterior.coords)
            if len(coords) > 0:
                # Calculate average latitude for accurate conversion
                avg_lat = sum(coord[1] for coord in coords) / len(coords)
                
                # Convert degrees to meters at this latitude
                # 1 degree latitude ≈ 111,320 meters (constant)
                # 1 degree longitude ≈ 111,320 * cos(latitude) meters
                lat_meters_per_deg = 111320.0
                lon_meters_per_deg = 111320.0 * abs(geom_obj.centroid.x) * 0.017453292519943295
                
                # Area in square degrees (from Shapely)
                area_sq_deg = abs(geom_obj.area)
                
                # Convert to square meters, then to hectares
                # Approximation: use average of lat/lon factors
                meters_per_deg_avg = (lat_meters_per_deg + lon_meters_per_deg) / 2
                area_sq_m = area_sq_deg * (meters_per_deg_avg ** 2)
                area_ha = area_sq_m / 10000  # convert m² to hectares
                
                return round(area_ha, 2)
    except Exception:
        pass
    return None


@router.get("/", response_model=List[FarmOut])
def list_farms(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all farms belonging to the current user"""
    farms = db.query(Farm).filter(Farm.user_id == user.id).order_by(Farm.created_at.desc()).all()
    result = []
    for farm in farms:
        geom_json = wkb_to_geojson(farm.geom) if farm.geom else None
        result.append(FarmOut(
            id=farm.id,
            name=farm.name,
            area_ha=farm.area_ha,
            geom=geom_json or {"type": "Polygon", "coordinates": []}
        ))
    return result


@router.post("/", response_model=FarmOut)
def create_farm(payload: FarmCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new farm with GeoJSON polygon boundary"""
    # payload.geom expected to be GeoJSON Polygon
    try:
        geom_obj = shape(payload.geom)
        if geom_obj.geom_type != 'Polygon':
            raise HTTPException(status_code=400, detail="Geometry must be a Polygon")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid geometry: {str(e)}")
    
    geom_wkb = from_shape(geom_obj, srid=4326)
    area_ha = calculate_area_ha(geom_obj)
    
    farm = Farm(user_id=user.id, name=payload.name, geom=geom_wkb, area_ha=area_ha)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    
    geom_json = wkb_to_geojson(farm.geom)
    return FarmOut(id=farm.id, name=farm.name, area_ha=farm.area_ha, geom=geom_json or payload.geom)


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific farm by ID"""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    geom_json = wkb_to_geojson(farm.geom) if farm.geom else None
    return FarmOut(
        id=farm.id,
        name=farm.name,
        area_ha=farm.area_ha,
        geom=geom_json or {"type": "Polygon", "coordinates": []}
    )


@router.put("/{farm_id}", response_model=FarmOut)
@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a farm (name and/or geometry)"""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Update name if provided
    if payload.name is not None:
        farm.name = payload.name
    
    # Update geometry if provided
    if payload.geom is not None:
        try:
            geom_obj = shape(payload.geom)
            if geom_obj.geom_type != 'Polygon':
                raise HTTPException(status_code=400, detail="Geometry must be a Polygon")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid geometry: {str(e)}")
        
        geom_wkb = from_shape(geom_obj, srid=4326)
        farm.geom = geom_wkb
        # Recalculate area
        farm.area_ha = calculate_area_ha(geom_obj)
    
    db.commit()
    db.refresh(farm)
    
    geom_json = wkb_to_geojson(farm.geom) if farm.geom else None
    return FarmOut(
        id=farm.id,
        name=farm.name,
        area_ha=farm.area_ha,
        geom=geom_json or {"type": "Polygon", "coordinates": []}
    )


@router.delete("/{farm_id}")
def delete_farm(farm_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a farm and all associated data"""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Note: In production, you might want to check for associated soil samples/predictions
    # and either cascade delete or prevent deletion if data exists
    db.delete(farm)
    db.commit()
    return {"message": "Farm deleted successfully"}
