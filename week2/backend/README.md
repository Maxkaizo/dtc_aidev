# Chip In backend

FastAPI implementation of `../openapi.yaml`, using an in-memory store and optional authentication.

## Start

```sh
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://127.0.0.1:8000/api
- Interactive documentation: http://127.0.0.1:8000/docs
- Generated OpenAPI: http://127.0.0.1:8000/openapi.json
- Seeded event: http://127.0.0.1:8000/api/events/demo

Run one worker. Events, accounts, and tokens live only in this process and reset on restart, including development reloads. A new app instance seeds the specification's Ana/Luis example with event ID `demo`. POST `/api/events/demo` creates an independent copy with a new ID.

## Modules

- `app/routers/`: public event routes and optional account routes.
- `app/models.py`: event request/response models and validation.
- `app/store.py`: seeded, locked in-memory store; atomic writes and detached snapshots.
- `app/auth.py`: account models, Argon2 password hashing, token issuance and verification.
- `app/main.py`: application factory, exception handlers, CORS, and router registration.

## Authentication

All five event operations remain public, as required by the contract. Optional accounts do not establish ownership or restrict event access.

| Method | Path | Authentication |
| --- | --- | --- |
| POST | `/api/auth/register` | Public; JSON `username` and `password` |
| POST | `/api/auth/login` | Public; JSON `username` and `password` |
| GET | `/api/auth/me` | `Authorization: Bearer <access_token>` |

Register a username (3–50 ASCII letters, digits, underscores, dots or hyphens) and a password (8–128 characters). Usernames are trimmed and lowercased; passwords are preserved exactly. Register returns only the account ID and username. Login returns `access_token`, `token_type: "bearer"`, and `expires_in: 3600`. Use the token with Swagger's **Authorize** button to try `/api/auth/me`.

Passwords use salted Argon2id hashes through pwdlib. Tokens are random opaque values, expire after one hour, and are stored only as SHA-256 digests. Missing, invalid, or expired tokens return 401 with `WWW-Authenticate: Bearer`. No preconfigured account/password is seeded.

## Frontend integration

The existing frontend still uses its localStorage mock; this task adds the backend without replacing that client. To connect it later, replace the five methods in `frontend/src/api.js` with HTTP calls to these routes. Every success returns the complete event object. The server seed can be loaded using `getEvent('demo')` once connected.

CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`. Override with a comma-separated `CORS_ORIGINS` environment variable. Use the backend on port 8000; the existing Node frontend server does not proxy `/api`.

## Tests and lint

```sh
uv run pytest
uv run ruff check .
```

Tests exercise all endpoints, specification response schemas, the seed, registration ordering, category normalization, integer cents, total limits, atomic rejection, concurrent writes, CORS, password storage, optional account flow, invalid tokens, token expiration, and isolation across app instances. Dependencies are pinned in `uv.lock`.
