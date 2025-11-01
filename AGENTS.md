# Repository Guidelines

## Project Structure & Module Organization
- `main.py` boots the FastAPI app, configures CORS, and mounts routers from `api/routes.py`.
- Domain logic is intentionally thin: `services/attendance_service.py` returns deterministic responses, while `services/auth_service.py` handles JWT tokens.
- Runtime configuration is centralized in `config.py`; adjust env vars via `.env` prefixed with `APP_`.
- Tests reside under `tests/`, currently `test_attendance.py`; mirror this layout for new suites.

## Build, Test & Development Commands
- `make install` installs runtime dependencies from `requirements.txt`; use `make dev` to add pytest, black, flake8, and mypy.
- `make run` starts Uvicorn on `http://localhost:8000`; `make docker-run` spins up the Docker Compose stack.
- Quality gates: `make lint` (flake8) and `make format` (black + isort) keep style consistent; `make type-check` runs mypy.
- Container workflows: `make docker-build` builds the API image, `make docker-shell` opens a shell inside `attendance-api` for interactive debugging.

## Coding Style & Naming Conventions
- Target Python 3.11; auto-format with Black (line length 88) and isort’s Black profile, then confirm with flake8 (max line length 127).
- Keep FastAPI routers feature-scoped and expose descriptive callables (e.g., `mark_attendance`); services should prefer short, explicit methods like `process_attendance`.
- Apply type hints throughout to preserve FastAPI docs and editor support; prefer simple return payloads that map directly to `pydantic` models.

## Testing Guidelines
- Author pytest modules as `tests/test_<feature>.py` with functions `test_<behavior>`; co-locate fixtures inside the test module or `conftest.py` when it appears.
- `make test` runs `pytest -v`; extend assertions to cover both success and failure paths when adding features.
- Add `pytest.mark.asyncio` only if you introduce async logic; default services are synchronous for clarity.

## Commit & Pull Request Guidelines
- History shows short descriptive commits (e.g., `last commit`); keep messages concise, prefer imperative voice, and wrap lines at ~72 characters.
- Ensure each commit passes `make format`, `make lint`, and `make test`; include a summary of user-facing effects.
- Pull requests should link issues, outline testing performed, and attach API samples or screenshots for UI-visible changes; highlight configuration updates touching `.env` or `config.py`.

## Environment & Security Tips
- Copy `.env.example` via `make setup-env`, fill local secrets locally, and never commit `.env`.
- Stop containers with `make docker-stop` when done and clear caches via `make clean` before packaging changes.
