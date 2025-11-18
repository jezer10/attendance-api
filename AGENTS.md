# Repository Guidelines

## Project Structure & Module Organization
- `main.py` boots FastAPI, configures CORS, and mounts the versioned router from `src/api`.
- Place routes under `src/api/v1/` (e.g., `attendance.py`) and re-export them in `src/api/v1/__init__.py` so the app exposes a single versioned entrypoint.
- Pull configuration from `src/core/config.py` via the `settings` object, which maps every `APP_` environment variable.
- Keep business logic in `src/services/` modules (`attendance_service.py`, `auth_service.py`) and mirror the code tree inside `src/tests/` using `test_<feature>.py`.

## Build, Test & Development Commands
- `make install` installs dependencies from `requirements.txt`; rerun only after dependency updates.
- `make run` starts Uvicorn on `http://localhost:8000` (override with `PORT=9000 make run`).
- `make dev` runs the contributor workflow: pytest, Black, Flake8, and mypy.
- `make docker-run` / `make docker-stop` control the Compose stack needed for Supabase-backed flows.
- Run `make format`, `make lint`, and `make type-check` before pushing to catch style or typing regressions early.

## Coding Style & Naming Conventions
- Target Python 3.11, four-space indentation, and Black’s 88-character line limit; use isort’s Black profile so imports stay stable.
- Apply explicit type hints to FastAPI endpoints and services; it keeps OpenAPI docs and editor tooling accurate.
- Name routers and services after the feature (`attendance_router`, `process_attendance`) and keep handlers stateless through dependency injection with `Depends`.

## Testing Guidelines
- Pytest powers the suite; `make test` (alias for `pytest -v`) is the required pre-push check.
- Follow pytest naming patterns: `src/tests/test_<feature>.py` files with `test_<behavior>` functions.
- Prefer synchronous tests; mark async paths with `@pytest.mark.asyncio` only when awaiting coroutines, and share reusable fixtures through `src/tests/conftest.py`.

## Commit & Pull Request Guidelines
- Write short, imperative commit messages such as `Add attendance router`, wrapping at roughly 72 characters.
- Confirm `make format`, `make lint`, and `make test` locally, then mention those results plus any manual API checks in the PR description.
- Reference linked issues, include screenshots or sample curl commands for user-facing changes, and call out config or migration impacts (`.env`, `config.py`, Supabase settings).

## Security & Configuration Tips
- Run `make setup-env` to copy `.env.example`, keep secrets out of version control, and document required variables in the example file.
- Tighten `settings.BACKEND_CORS_ORIGINS` in `main.py` before staging or production deployments.
- Use `make clean` to clear caches prior to packaging, and audit Docker images whenever dependencies change to limit the attack surface.
