from fastapi.testclient import TestClient
from main import app
import os
import sqlite3

# Clean up db before test
if os.path.exists("tasks.db"):
    os.remove("tasks.db")

# This will trigger lifespan events
with TestClient(app) as client:
    print("Testing GET /tasks")
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    print("Initial tasks:", tasks)

    print("\nTesting POST /tasks")
    response = client.post("/tasks", json={"title": "Test SQLite"})
    assert response.status_code == 201
    new_task = response.json()
    print("Created task:", new_task)
    assert new_task["title"] == "Test SQLite"
    task_id = new_task["id"]

    print("\nTesting GET /tasks/{task_id}")
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test SQLite"
    
    print("\nTesting PUT /tasks/{task_id}")
    response = client.put(f"/tasks/{task_id}", json={"title": "Updated SQLite", "done": True})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated SQLite"
    assert response.json()["done"] == True
    
    print("\nTesting DELETE /tasks/{task_id}")
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    
    print("\nTesting GET /tasks/{task_id} after deletion")
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404

print("\nAll tests passed successfully!")
