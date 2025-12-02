from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth ---
class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    language_preference: Optional[str] = "en"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    name: str
    phone: str
    language_preference: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# --- Farm ---
class FarmCreate(BaseModel):
    name: Optional[str] = None
    # Expect GeoJSON Polygon as dict
    geom: dict

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    geom: Optional[dict] = None

class FarmOut(BaseModel):
    id: int
    name: Optional[str]
    area_ha: Optional[float]
    geom: dict

    model_config = ConfigDict(from_attributes=True)

# --- Soil Sample ---
class SoilSampleIn(BaseModel):
    farm_id: int
    ph: Optional[float] = None
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    extra: Optional[Dict] = None

class SoilSampleUpdate(BaseModel):
    ph: Optional[float] = None
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    extra: Optional[Dict] = None

class SoilSampleOut(BaseModel):
    id: int
    farm_id: int
    sample_date: datetime
    ph: Optional[float]
    n: Optional[float]
    p: Optional[float]
    k: Optional[float]
    extra: Optional[Dict]

    model_config = ConfigDict(from_attributes=True)

# --- Recommendation ---
class RecommendationStep(BaseModel):
    step: str  # message_key
    params: Optional[Dict[str, Any]] = None
    text: Optional[str] = None # Localized text for frontend

class RecommendationOut(BaseModel):
    title_key: str
    title_params: Optional[Dict[str, Any]] = None
    title_text: Optional[str] = None
    
    summary_key: str
    summary_text: Optional[str] = None
    
    steps: List[RecommendationStep]
    cost_estimate: Optional[float] = None
    raw_text_en: Optional[str] = None

# --- Prediction ---
class PredictIn(BaseModel):
    farm_id: int
    crop: str

class PredictOut(BaseModel):
    predicted_yield: float
    confidence: float
    recommendation: Optional[RecommendationOut] = None

class PredictionOut(BaseModel):
    id: int
    farm_id: int
    crop: str
    date_run: datetime
    predicted_yield_kg_per_ha: Optional[float]
    
    # Fix for "model_" namespace warning in Pydantic v2
    model_version: Optional[str] = Field(default=None, alias="model_version") 
    
    inputs: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

# --- Device / Sync ---
class DeviceBindOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class ClientRecord(BaseModel):
    client_id: str
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
