import sqlite3
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from typing import Optional
from contextlib import asynccontextmanager

DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Check if empty
    cursor.execute('SELECT COUNT(*) FROM tasks')
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.executemany('''
            INSERT INTO tasks (title, done) VALUES (?, ?)
        ''', [
            ("Buy milk", False),
            ("Walk the dog", False),
            ("Do laundry", True)
        ])
    
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="CRUD API", lifespan=lifespan)

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

def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    
    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)
    
    if search is not None:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
        
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_dict(row) for row in rows]

@app.get("/stats", description="Get task statistics")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    done_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "done": done_count,
        "open": total - done_count
    }

@app.post("/reset", description="Reset tasks to initial state")
def reset_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks")
    cursor.executemany('''
        INSERT INTO tasks (title, done) VALUES (?, ?)
    ''', [
        ("Buy milk", False),
        ("Walk the dog", False),
        ("Do laundry", True)
    ])
    
    conn.commit()
    conn.close()
    
    return {"message": "Tasks reset"}

@app.get("/tasks/{task_id}", description="Get a single task by ID")
def get_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row_to_dict(row)
    
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post("/tasks", status_code=201, description="Create a new task")
def create_task(task: TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, False))
    new_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row_to_dict(row)

@app.put("/tasks/{task_id}", description="Update an existing task")
def update_task(task_id: int, task_update: TaskUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        
    new_title = task_update.title
    new_done = task_update.done if task_update.done is not None else row["done"]
    
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return row_to_dict(updated_row)

@app.delete("/tasks/{task_id}", status_code=204, description="Delete a task")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if deleted:
        return Response(status_code=204)
        
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
