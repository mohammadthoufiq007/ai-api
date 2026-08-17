from fastapi.testclient import TestClient
from main import app
import os

# Clean up db before test
if os.path.exists("tasks.db"):
    os.remove("tasks.db")

with TestClient(app) as client:
    print("Testing /public/info")
    resp = client.get("/public/info")
    assert resp.status_code == 200
    print(resp.json())

    print("\nTesting POST /auth/signup")
    resp = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert resp.status_code == 201
    user = resp.json()
    print("Created user:", user)
    
    print("\nTesting POST /auth/signup duplicate email")
    resp = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert resp.status_code == 400

    print("\nTesting POST /auth/login")
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert resp.status_code == 200
    token_data = resp.json()
    access_token = token_data["access_token"]
    print("Logged in, token received.")

    print("\nTesting GET /protected/profile WITHOUT token")
    resp = client.get("/protected/profile")
    assert resp.status_code in (401, 403), f"Expected 401 or 403, got {resp.status_code}: {resp.text}"

    print("\nTesting GET /protected/profile WITH token")
    resp = client.get("/protected/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    print("Profile data:", resp.json())

    print("\nTesting POST /auth/logout")
    resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 204
    print("Logged out")

    print("\nTesting GET /protected/profile AFTER logout")
    resp = client.get("/protected/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 401
    print("Access correctly denied.")
    
    print("\nTesting original CRUD routes")
    resp = client.get("/tasks")
    assert resp.status_code == 200
    
print("\nAll tests passed successfully!")
