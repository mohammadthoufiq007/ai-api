# CRUD API

A simple in-memory CRUD API for managing a to-do list, built with FastAPI.

## Installation and Run Instructions

To install the dependencies and run the server locally:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

| CRUD op | Method | Path | Success |
|---|---|---|---|
| Create | POST | `/tasks` | 201 |
| Read (all) | GET | `/tasks` | 200 |
| Read (one) | GET | `/tasks/{id}` | 200 |
| Update | PUT | `/tasks/{id}` | 200 |
| Delete | DELETE | `/tasks/{id}` | 204 |
| Root | GET | `/` | 200 |
| Health | GET | `/health` | 200 |
| Filter/Paginate | GET | `/tasks?done=true&search=milk&limit=2&offset=0` | 200 |
| Statistics | GET | `/stats` | 200 |
| Reset | POST | `/reset` | 200 |

*Note: Real APIs paginate their list endpoints (like `/tasks?limit=2&offset=2`) to limit the amount of data returned in a single request, which improves performance and reduces server/client payload overhead.*

## Example `curl` Output

```bash
$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
date: Sat, 18 Jul 2026 14:35:49 GMT
server: uvicorn
content-length: 129
content-type: application/json

[{"id":1,"title":"Buy milk","done":false},{"id":2,"title":"Walk the dog","done":false},{"id":3,"title":"Do laundry","done":true}]
```

## Swagger UI

You can interact with the API using the built-in Swagger UI at `http://localhost:8000/docs`.

![Swagger UI Screenshot](./docs/swagger.png)
