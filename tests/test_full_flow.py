import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Test Data
USER_DATA = {"name": "Test Auto", "phone": "9999900000", "password": "testpassword"}
FARM_DATA = {
    "name": "Test Farm",
    "geom": {
        "type": "Polygon",
        "coordinates": [[[77, 20], [77, 20.001], [77.001, 20.001], [77.001, 20], [77, 20]]]
    }
}

@pytest.mark.asyncio
async def test_full_backend_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Register
        # Use a random phone to avoid duplicate errors on re-runs
        import random
        phone = f"999{random.randint(1000000, 9999999)}"
        USER_DATA["phone"] = phone
        
        resp = await ac.post("/api/v1/auth/register", json=USER_DATA)
        assert resp.status_code == 200
        
        # 2. Login
        resp = await ac.post("/api/v1/auth/login", json=USER_DATA)
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Farm
        resp = await ac.post("/api/v1/farms/", json=FARM_DATA, headers=headers)
        assert resp.status_code == 200
        farm_id = resp.json()["id"]
        
        # 4. List Farms
        resp = await ac.get("/api/v1/farms/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        # Check that our farm is in the list
        farm_names = [f["name"] for f in resp.json()]
        assert "Test Farm" in farm_names
        
        # 5. Update Farm
        resp = await ac.put(f"/api/v1/farms/{farm_id}", json={"name": "Renamed Farm"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Farm"
        
        # 6. Add Soil Sample
        soil_data = {"farm_id": farm_id, "n": 0.5, "p": 10, "k": 20, "ph": 6.0}
        resp = await ac.post("/api/v1/soil_samples/", json=soil_data, headers=headers)
        assert resp.status_code == 200
        sample_id = resp.json()["id"]
        
        # 7. Update Soil Sample
        resp = await ac.put(f"/api/v1/soil_samples/{sample_id}", json={"ph": 7.5}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["ph"] == 7.5
        
        # 8. Run Prediction
        predict_data = {"farm_id": farm_id, "crop": "wheat"}
        resp = await ac.post("/api/v1/predict/", json=predict_data, headers=headers)
        assert resp.status_code == 200
        assert "predicted_yield" in resp.json()
        
        # 9. Get Farm Predictions History
        resp = await ac.get(f"/api/v1/predict/farm/{farm_id}", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        
        # 10. Delete Soil Sample
        resp = await ac.delete(f"/api/v1/soil_samples/{sample_id}", headers=headers)
        assert resp.status_code == 200 # or 204
        
        # 11. Delete Farm
        resp = await ac.delete(f"/api/v1/farms/{farm_id}", headers=headers)
        assert resp.status_code == 200 # or 204
        
        # 12. Verify Deletion
        resp = await ac.get(f"/api/v1/farms/{farm_id}", headers=headers)
        assert resp.status_code == 404

    print("\n✅ All backend tests passed successfully!")
