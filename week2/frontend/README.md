# Chip In frontend

Interactive Spanish interface with real HTTP calls to the FastAPI backend. Built with JavaScript, CSS, and Node.js tooling; no npm dependencies.

## Run

From `week2/`, start these commands in separate terminals:

```sh
make run       # FastAPI backend on port 8000
make frontend  # Frontend on port 5173
```

Open http://localhost:5173. Create an event, choose **Explorar un ejemplo**, or open http://localhost:5173/?event=demo for the backend's seeded event.

Alternatively run `npm run dev` from `frontend/` while the backend is running. The Node server proxies `/api` to `http://127.0.0.1:8000`. Override with `BACKEND_URL`, for example `BACKEND_URL=http://127.0.0.1:8001 npm run dev`. `PORT` changes the frontend port. With Make, pass `BACKEND_PORT=8001` to both startup commands, or set `BACKEND_URL` explicitly on `make frontend`.

## Data and sharing

All backend access is centralized in `src/api.js`. Event endpoints are public and require no login. The five methods create events and demos, fetch events, and append groups and expenses. All successful responses contain the complete event. Validation and connection errors are displayed in Spanish.

Shared links retrieve the same event from the server, including from a fresh browser. Other devices must be able to reach the frontend server; a localhost URL only works on the same computer. The frontend refreshes when returning to its window; reload to fetch changes while staying in the same window. It does not poll or provide live updates.

Backend data is persisted through SQLAlchemy in SQLite by default and survives restarts. Configure the backend database with `DATABASE_URL`. Old localStorage-only events are not migrated. Group selection stays local to the current page and does not verify identity.

`src/calculations.js` computes exact-cent allocations and settlements. Google Fonts are optional, with system-font fallbacks.

## Verify

```sh
npm test                  # HTTP client and calculation unit tests
npm run test:integration   # Real backend + frontend proxy, requires uv
```

The integration check starts and stops an isolated backend with a temporary SQLite database on port 18080 and a frontend on an available port. Set `INTEGRATION_BACKEND_PORT` if 18080 is occupied. It exercises all five client methods, fresh-client access, exact settlement, validation, missing events, and backend unavailability.
