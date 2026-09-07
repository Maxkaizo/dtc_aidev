# Our home — Shared Household Chores

A Django app for a couple to share household chores. The initial MVP is implemented. `week1/` contains the application, Docker setup, and dependency configuration; `_docs/` contains the product plan.

## Stack

Python 3.12, Django 5.2, server-rendered templates with plain CSS, SQLite, uv, and Docker Compose. Exact dependency versions are recorded in `uv.lock`.

See [product plan](_docs/plan.md) for product scope and [AGENTS.md](AGENTS.md) for development conventions.

[Plan 2](_docs/plan2.md) covers planned board filters, recurring chore controls, editing, and assignment during creation. These additions are not implemented yet.

## Run with Docker Compose

Run these commands from `week1/`. Docker must be running; on WSL, enable Docker Desktop's integration for your distribution.

```bash
docker compose up --build -d
docker compose exec web python manage.py setup_household
```

The setup command prompts for two usernames and passwords. There are no default credentials or public registration. Open **http://localhost:8000** and sign in as either partner. Use separate browser profiles or a private window to try both accounts at once.

```bash
# View application logs
docker compose logs -f web

# Stop the app while keeping its data
docker compose down

# Reset a partner's password
docker compose exec web python manage.py changepassword USERNAME
```

SQLite data lives in the `chore_data` Docker volume and survives container recreation. `docker compose down -v` deletes that volume and its data. Source files are mounted for Django's automatic reload. Rebuild the image after changing dependencies.

This setup uses Django's development server and binds to localhost. It is intended for local development.

## Local uv environment

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py setup_household
uv run python manage.py runserver
```

`uv sync` creates `.venv/` for editor support and local tooling. The optional local server uses a separate `db.sqlite3`; it does not share accounts or chores with the Docker volume. Stop the Docker app before running the local server on the same port.

## Using the app

1. Add a chore with a title, required due date, and optional description.
2. Choose one-off, daily, weekly, or monthly recurrence.
3. Either partner selects **I'll do it** to reserve an available chore.
4. The owner can **Mark done** or **Release** it.

Overdue chores retain their owner. Due dates are calendar dates; a chore becomes overdue the following day in the household timezone (default: `America/Mexico_City`).

Recurring chores keep their original schedule. Opening the board generates any missing occurrences through today plus the next future occurrence. Missed occurrences remain visible. Monthly chores anchored on the 29th–31st use the last valid day in shorter months and return to the original day afterward. Generation does not require a background service; it can also be run explicitly:

```bash
docker compose exec web python manage.py generate_chores
```

The MVP does not include editing/deleting chores, notifications, or recurrence cancellation.

## Checks

```bash
uv run python manage.py test
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

To test inside the container:

```bash
docker compose exec web python manage.py test
```

The 16 tests cover authentication, the two-partner limit, creation, ownership, claim exclusivity, CSRF protection, completion/release, recurring catch-up, and month-end dates. Claim exclusivity is checked with sequential competing requests; simultaneous-request testing remains a follow-up.

## Configuration

Compose accepts `TIME_ZONE` and `DJANGO_SECRET_KEY` from the shell or an optional local `.env` file. App settings also accept `DATABASE_PATH`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS`. Secrets, virtual environments, and local database files are ignored by Git.
