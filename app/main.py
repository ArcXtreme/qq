from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers (NOTE: 'predictions' is removed because it is inside 'predict')
from app.api.v1 import auth, farms, predict, device, token, sync, soil_samples, onboarding

app = FastAPI(title="SIH Crop Backend - MVP", version="0.1")

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(farms.router, prefix="/api/v1/farms", tags=["farms"])
app.include_router(device.router, prefix="/api/v1/device", tags=["device"])
app.include_router(token.router, prefix="/api/v1/token", tags=["token"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(soil_samples.router, prefix="/api/v1/soil_samples", tags=["soil_samples"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])

# Note: The GET /prediction/{id} route is inside 'predict.py', so we reuse that router
app.include_router(predict.router, prefix="/api/v1/predict", tags=["predict"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
