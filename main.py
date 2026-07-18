from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from typing import Optional

app = FastAPI(title="CRUD API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input: " + str(exc.errors()[0]["msg"])}
    )

class TaskCreate(BaseModel):
    title: str

    @field_validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('title cannot be empty')
        return v

class TaskUpdate(BaseModel):
    title: str
    done: Optional[bool] = None

    @field_validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('title cannot be empty')
        return v

tasks_db = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Do laundry", "done": True}
]

@app.get("/", description="Get API information including name, version, and endpoints")
def get_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health", description="Check API health status")
def get_health():
    return {"status": "ok"}

@app.get("/tasks", description="Get all tasks with optional filtering and pagination")
def get_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    result = tasks_db
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search is not None:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result[offset : offset + limit]

@app.get("/stats", description="Get task statistics")
def get_stats():
    total = len(tasks_db)
    done_count = sum(1 for t in tasks_db if t["done"])
    return {
        "total": total,
        "done": done_count,
        "open": total - done_count
    }

@app.post("/reset", description="Reset tasks to initial state")
def reset_tasks():
    global tasks_db
    tasks_db.clear()
    tasks_db.extend([
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk the dog", "done": False},
        {"id": 3, "title": "Do laundry", "done": True}
    ])
    return {"message": "Tasks reset"}

@app.get("/tasks/{task_id}", description="Get a single task by ID")
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post("/tasks", status_code=201, description="Create a new task")
def create_task(task: TaskCreate):
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks_db.append(new_task)
    return new_task

@app.put("/tasks/{task_id}", description="Update an existing task")
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks_db:
        if task["id"] == task_id:
            task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.delete("/tasks/{task_id}", status_code=204, description="Delete a task")
def delete_task(task_id: int):
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return Response(status_code=204)
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

