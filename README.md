# CRUD API (W4 · BE-03 - Auth & Protect)

🌟 **Live API Documentation:** [https://crud-api-4881.onrender.com/docs](https://crud-api-4881.onrender.com/docs)

## Goal
A small API that manages a to-do list: you can create tasks, read them, update them, and delete them — the four CRUD operations. The API is built with **Python 3.10+** and **FastAPI**, tested via a visual page called **Swagger UI**, and uses strictly in-memory storage. 

## Purpose
This project represents the heartbeat of almost every backend in the world: the request → response loop. Two professional habits start here:
1. Data lives in a database (we are using SQLite to persist data).
2. The API is secured using **JWT Authentication**.

## Authentication (Custom JWT via SQLite)
Instead of relying on a third-party Identity Provider like Supabase, this API implements a fully custom authentication system using SQLite, `passlib` (bcrypt) for password hashing, and `PyJWT` for issuing and verifying JSON Web Tokens (JWT).
- **Users Table**: Stores user credentials securely.
- **Token Blocklist**: When a user logs out, their token is blacklisted in the database, preventing further use.
- **Environment Variables**: The `SECRET_KEY` for signing JWTs is securely loaded from a `.env` file.

## Database (SQLite)
Instead of an in-memory array, this API uses **SQLite**, a lightweight database stored in a single file. 
- **Why SQLite?**: It requires no installation or separate server, making it perfect for development and small applications.
- **Where is it stored?**: The database is stored locally in a file named `tasks.db` in the root of the project. It is automatically created the first time you run the application.

### Example SQL Query
Here is an example query you can run to view all completed tasks:
```sql
SELECT * FROM tasks WHERE done = 1;
```


## The Big Idea
This API is a server — a program that waits for requests and sends back responses. It offers several **endpoints** (doors into the server defined by a path and an HTTP method). 

The four CRUD operations map onto the HTTP methods as implemented in this API:
| CRUD operation | HTTP method | Example endpoint | Meaning |
|---|---|---|---|
| Create | POST | `POST /tasks` | Add a new task |
| Read | GET | `GET /tasks` · `GET /tasks/3` | List all tasks / get task 3 |
| Update | PUT | `PUT /tasks/3` | Change task 3 |
| Delete | DELETE | `DELETE /tasks/3` | Remove task 3 |

---

## 🚀 Installation & Run Instructions

To install the dependencies and run the server locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file for JWT signing
echo "SECRET_KEY=your_super_secret_key_that_is_long_enough" > .env

# Start the server on port 8000
uvicorn main:app --reload
```

## 🛠️ Endpoints & Features Built

This project was built strictly in stages, fulfilling all requirements and optional extras.

| Feature / Stage | Method | Path | Auth Required |
|---|---|---|---|
| **Root** | GET | `/` | ❌ |
| **Health** | GET | `/health` | ❌ |
| **Public Info** | GET | `/public/info` | ❌ |
| **Sign Up** | POST | `/auth/signup` | ❌ |
| **Log In** | POST | `/auth/login` | ❌ |
| **Log Out** | POST | `/auth/logout` | ✅ |
| **Protected Profile** | GET | `/protected/profile` | ✅ |
| **Read All Tasks** | GET | `/tasks` | ❌ |
| **Read One Task** | GET | `/tasks/{id}` | ❌ |
| **Create Task** | POST | `/tasks` | ❌ |
| **Update Task** | PUT | `/tasks/{id}` | ❌ |
| **Delete Task** | DELETE | `/tasks/{id}` | ❌ |
| **Filter/Paginate** | GET | `/tasks?...` | ❌ |
| **Statistics** | GET | `/stats` | ❌ |
| **Reset** | POST | `/reset` | ❌ |

*Note: Real APIs paginate their list endpoints (like `/tasks?limit=2&offset=2`) to limit the amount of data returned in a single request, which improves performance and reduces server/client payload overhead.*

### Validation Rules
The server never trusts client input. If a `title` is missing or empty on a `POST` or `PUT` request, the server intentionally blocks it and returns a `400 Bad Request` with a JSON error explaining the issue. If an unknown ID is requested, it correctly returns a `404 Not Found` with a specific JSON error. 

## 💻 Example `curl` Output

```bash
$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
date: Sat, 18 Jul 2026 14:35:49 GMT
server: uvicorn
content-length: 129
content-type: application/json

[{"id":1,"title":"Buy milk","done":false},{"id":2,"title":"Walk the dog","done":false},{"id":3,"title":"Do laundry","done":true}]
```

## 📖 Swagger UI

You can interact with the API using the built-in Swagger UI at:
- **Local Environment:** `http://localhost:8000/docs`

The Swagger UI now includes an **"Authorize"** button (padlock icon) to test the protected routes. 

![Swagger UI Screenshot](./docs/swagger.png)

## AI vs Me Analysis

**How it handled token extraction:**
The AI utilized FastAPI's built-in `fastapi.security.HTTPBearer`, which correctly and safely parses the `Authorization: Bearer <token>` header without needing manual string splitting.

**Security flaws it might have introduced:**
Instead of relying on Supabase for robust session invalidation, the AI had to implement a custom token blocklist table in SQLite. If this table grows indefinitely, it could cause performance issues over time. A cron job to delete expired tokens from the blocklist would be needed in production.

**What the prompt missed and what the AI assumed:**
The prompt asked to avoid Supabase entirely, but didn't specify how to handle logging out (which is normally handled by the IdP). The AI correctly assumed it needed to build a `token_blocklist` table to invalidate active tokens when a user explicitly logs out.
