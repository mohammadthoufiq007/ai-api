import sqlite3
import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional
from contextlib import asynccontextmanager
from src.llm.schema import TaskEnrichmentRequest, TaskEnrichmentResponse
from src.llm.client import enrich_task
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "tasks.db"
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_for_dev_must_be_32_bytes")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Existing tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Token blocklist table (for logout)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_blocklist (
            token TEXT PRIMARY KEY,
            blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if empty (tasks)
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

# Auth Utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()}) # PyJWT expects unix timestamp
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    # Check blocklist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM token_blocklist WHERE token = ?", (token,))
    is_blocked = cursor.fetchone()
    conn.close()
    
    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Verify user exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users WHERE email = ?", (user_email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")
            
        return {"id": user["id"], "email": user["email"], "created_at": user["created_at"], "token": token}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="CRUD API with Auth", lifespan=lifespan)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input: " + str(exc.errors()[0]["msg"])}
    )

# Models
class UserAuth(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def password_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('password cannot be empty')
        return v

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

# Auth Routes
@app.post("/auth/signup", status_code=201, description="Create a new user account")
def signup(user: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                      (user.email, get_password_hash(user.password)))
        new_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT id, email, created_at FROM users WHERE id = ?", (new_id,))
        new_user = cursor.fetchone()
        return dict(new_user)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

@app.post("/auth/login", description="Authenticate user & return JWT")
def login(user: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
        )
        
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout", status_code=204, description="Terminate the user session")
def logout(current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    # current_user includes the raw token string
    cursor.execute("INSERT INTO token_blocklist (token) VALUES (?)", (current_user["token"],))
    conn.commit()
    conn.close()
    return Response(status_code=204)

# Public & Protected Routes
@app.get("/public/info", description="Read public, unprotected data")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile", description="Read private user profile data")
def protected_profile(current_user: dict = Depends(verify_token)):
    # Remove the raw token before sending to client
    user_info = current_user.copy()
    user_info.pop("token", None)
    return user_info

# Original Routes
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

# AI endpoints
@app.post("/enrich", response_model=TaskEnrichmentResponse, description="Enrich a task description with AI categorization")
def enrich(request: TaskEnrichmentRequest):
    return enrich_task(request.description)

