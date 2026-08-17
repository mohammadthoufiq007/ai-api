# CRUD API (W3 · A1 - Database Connected)

🌟 **Live API Documentation:** [https://crud-api-4881.onrender.com/docs](https://crud-api-4881.onrender.com/docs)

## Goal
A small API that manages a to-do list: you can create tasks, read them, update them, and delete them — the four CRUD operations. The API is built with **Python 3.10+** and **FastAPI**, tested via a visual page called **Swagger UI**, and uses strictly in-memory storage. 

## Purpose
This project represents the heartbeat of almost every backend in the world: the request → response loop. Two professional habits start here:
1. Data lives in a database (we are using SQLite to persist data).
2. Everything is published and version-controlled through GitHub.

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

# Start the server on port 8000
uvicorn main:app --reload
```

## 🛠️ Endpoints & Features Built

This project was built strictly in stages, fulfilling all requirements and optional extras.

| Feature / Stage | Method | Path | Success |
|---|---|---|---|
| **Root (Stage 1)** | GET | `/` | 200 |
| **Health (Stage 1)** | GET | `/health` | 200 |
| **Read All (Stage 2)** | GET | `/tasks` | 200 |
| **Read One (Stage 2)** | GET | `/tasks/{id}` | 200 |
| **Create (Stage 3)** | POST | `/tasks` | 201 |
| **Update (Stage 4)** | PUT | `/tasks/{id}` | 200 |
| **Delete (Stage 4)** | DELETE | `/tasks/{id}` | 204 |
| **Filter/Paginate (Extra)** | GET | `/tasks?done=true&search=milk&limit=2&offset=0` | 200 |
| **Statistics (Extra)** | GET | `/stats` | 200 |
| **Reset (Extra)** | POST | `/reset` | 200 |

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

You can interact with the API using the built-in Swagger UI (Stage 5) at:
- **Live Deployment:** [https://crud-api-4881.onrender.com/docs](https://crud-api-4881.onrender.com/docs)
- **Local Environment:** `http://localhost:8000/docs`

Every endpoint features a custom description to make the interface self-explanatory.

