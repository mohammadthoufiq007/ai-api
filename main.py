from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

tasks_db = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Do laundry", "done": True}
]

@app.get("/")
def get_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks_db

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

