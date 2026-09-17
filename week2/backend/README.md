# Chip In backend

FastAPI implementation of `../openapi.yaml`, using SQLAlchemy, SQLite by default, and optional authentication.

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

## Database configuration

The server reads `DATABASE_URL` at startup. If unset, it uses **`backend/chip_in.db`**, resolved to an absolute path independently of the working directory. The SQLite file and its tables are created on first startup. Events, groups, attendees, expenses, accounts, and token hashes persist across restarts. Unexpired tokens remain valid until their original one-hour expiry.

```sh
# From week2, use another SQLite file (parent directory must already exist):
DATABASE_URL=sqlite:////tmp/chip-in.db make run
```

A relative URL such as `sqlite:///chip_in.db` is relative to the backend process's working directory. Prefer absolute paths. See `.env.example`; export the variable yourself, as `.env` files are not loaded automatically. Database files are ignored by Git.

On startup, the Ana/Luis example is inserted under event ID `demo` only if it is absent. Existing demo changes are preserved. POST `/api/events/demo` creates a separate copy with a new ID. There is no automatic import of data from the previous process-local store.

### Portability and schema management

`app/database.py` owns engines, session factories, and dialect-specific settings. `app/db_models.py` uses portable SQLAlchemy types, composite foreign keys, explicit ordering, and integer cents. Categories use SQLAlchemy's portable JSON type; queries do not use dialect-specific JSON operators. Storage operations use transactions and SQLAlchemy queries instead of raw vendor-specific SQL.

SQLite-specific connection setup enables foreign keys and explicit transactions. Event writes first update the event row to serialize append order and expense-limit checks across connections. SQLite serializes writers; use it for this small local app, not high write concurrency.

A future PostgreSQL deployment can use a URL such as `postgresql+psycopg://user:password@host:5432/chip_in` after installing a driver with `uv add "psycopg[binary]"`. PostgreSQL schema compilation is tested, but live PostgreSQL support and deployment are not yet verified. Changing `DATABASE_URL` selects another database; it does not copy existing data.

Startup uses `Base.metadata.create_all()` to bootstrap missing tables without dropping data. It does **not** migrate existing schemas. Add a migration tool such as Alembic before changing a deployed schema. Bootstrap a new database with one server instance before starting multiple workers.

## Modules

- `app/routers/`: public event routes and optional account routes.
- `app/models.py`: event request/response models and validation.
- `app/store.py`: transactional event repository and idempotent demo seeding.
- `app/database.py`: environment-based engine/session configuration and startup/shutdown.
- `app/db_models.py`: SQLAlchemy database tables, separate from API schemas.
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

Passwords use salted Argon2id hashes through pwdlib. Tokens are random opaque values, expire after one hour, and are stored in the database only as SHA-256 digests. Missing, invalid, or expired tokens return 401 with `WWW-Authenticate: Bearer`. No preconfigured account/password is seeded.

## Frontend integration

The frontend uses HTTP calls centralized in `frontend/src/api.js`. Run `make run` and `make frontend` from week2 in separate terminals. The Node frontend server proxies `/api` to this backend, by default at http://127.0.0.1:8000. Set `BACKEND_URL` for another backend origin. Every successful event operation returns the full event object.

Open http://localhost:5173/?event=demo to use the seed. Shared links work for clients that can reach the frontend server. CORS also allows direct requests from localhost:5173 and 127.0.0.1:5173; override it with `CORS_ORIGINS`.

## Tests and lint

```sh
uv run pytest
uv run ruff check .
```

Tests exercise all endpoints, specification response schemas, the seed, registration ordering, category normalization, integer cents, total limits, atomic rejection, concurrent writes, CORS, password storage, optional account flow, invalid tokens, token expiration, persistence across restarts, separate-database isolation, foreign keys, and concurrent writes across engines. Every test uses its own temporary SQLite file. Dependencies are pinned in `uv.lock`.
