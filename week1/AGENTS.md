# Development Guidelines

## Scope

`week1/` is the main folder for the shared household chores app. Keep its application code, dependency configuration, and Docker files here. Follow [product plan](_docs/plan.md) for MVP behavior and scope.

## Agreed Stack

- **Python and Django:** use Django for application logic, routing, forms, and database access through its ORM.
- **Django templates:** render the interface on the server, with minimal CSS.
- **Authentication:** use Django's built-in authentication with one account per partner.
- **uv:** manage dependencies and a local `.venv`; keep dependency declarations in `pyproject.toml` and commit `uv.lock` for reproducible installs.
- **SQLite:** use SQLite for the initial MVP and persist the container's database in a Docker volume.
- **Docker Compose:** run one Django service locally, with source changes available to the container and automatic development reload.

## Development Workflow

- Use the local uv environment for editor support and development tools; use Docker Compose as the local application runtime.
- Provide `docker compose up --build` as the app startup command from `week1/`.
- Keep database data across container recreation through persistent storage.
- Keep virtual environments, local databases, secrets, and generated files out of Git.
- Keep setup, migrations, account creation, and run commands current in `README.md`.
- Use Python 3.12 and Django 5.2; exact dependency versions are recorded in `uv.lock`.
- Run `uv run python manage.py test` and `uv run python manage.py check` after application changes.
- Recurrence is generated on board visits through today plus one future occurrence; preserve the original date anchor and unfinished occurrences.

## Architecture Boundaries

Keep the MVP as a single Django application with a server-rendered interface. PostgreSQL may be considered later if deployment needs justify it. The current Docker setup is intended for local development.
