# Attendance Management API

A minimalist FastAPI service that records entry and exit events for employees. The current implementation responds deterministically without external integrations, making it ideal for demos or as a scaffold for richer attendance workflows.

## Requirements
- Python 3.11+
- pip
- Optional: Docker and Docker Compose

## Installation
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
make install
```

To install development tooling (pytest, black, flake8, mypy, isort):
```bash
make dev
```

## Running the API
```bash
make run               # Uvicorn with auto-reload on http://localhost:8000
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Docker users can start the service with:
```bash
make docker-build
make docker-run
```
Stop the container via `make docker-stop`.

## API Overview
| Method | Path                          | Description                               |
|--------|-------------------------------|-------------------------------------------|
| PUT    | `/api/v1/attendance`          | Save attendance schedule                  |
| GET    | `/api/v1/attendance`          | Fetch attendance schedule                 |
| POST   | `/api/v1/attendance/notify`   | Send WhatsApp notification for an event  |
| POST   | `/api/v1/attendance/credentials` | Save attendance login credentials     |
| GET    | `/api/v1/attendance/credentials` | Fetch attendance login metadata       |
| GET    | `/api/v1/health`              | Basic health probe                        |
| POST   | `/api/v1/auth/token`          | Issues a JWT for testing purposes         |

### Token generation
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"sub": "user-123"}'
```

Use the returned token in the `Authorization: Bearer <token>` header for protected routes.

### Sample attendance request
```bash
curl -X PUT http://localhost:8000/api/v1/attendance \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
           "isActive": true,
           "randomWindowMinutes": 0,
           "phoneNumber": "+51976387055",
           "schedule": {
             "entry": {
               "enabled": true,
               "localTime": "08:00:00",
               "utcTime": "13:00:00",
               "days": ["monday", "tuesday"]
             },
             "exit": {
               "enabled": false,
               "localTime": null,
               "utcTime": null,
               "days": []
             }
           },
           "location": {
             "address": "Avenida",
             "latitude": -6.758246,
             "longitude": -79.846117,
             "radiusMeters": 20
           },
           "timezone": "UTC-05:00 America/Lima"
         }'
```

### Attendance credentials
Save the per-user login credentials used by the marking workflow. The password is stored in
Supabase Vault and only the service-role backend can decrypt it.

Endpoint:
`POST /api/v1/attendance/credentials`

Request body:
```json
{
  "companyId": 7040,
  "userId": 77668171,
  "password": "Milagros1234"
}
```

Response body:
```json
{
  "success": true,
  "message": "Attendance credentials saved",
  "companyId": 7040,
  "userId": 77668171
}
```

Notes:
- Requires `Authorization: Bearer <token>`.
- One credential set per user; repeated calls overwrite the stored password.

Fetch saved credentials (password is never returned):
`GET /api/v1/attendance/credentials`

Response body:
```json
{
  "companyId": 7040,
  "userId": 77668171,
  "hasPassword": true
}
```

## Development Workflow
- `make format` → run black + isort
- `make lint` → run flake8 checks
- `make type-check` → run mypy
- `make test` → run pytest suite (ensures validation paths work)

## Environment variables
Configuration is managed through `.env` (see `.env.example`). All variables are prefixed with `APP_`:

| Variable             | Purpose                         | Default   |
|----------------------|---------------------------------|-----------|
| `APP_JWT_SECRET_KEY` | Secret key for signing JWTs     | `change-me` |
| `APP_JWT_ALGORITHM`  | Signing algorithm               | `HS256`   |
| `APP_LOG_LEVEL`      | Application log level           | `INFO`    |
| `APP_PORT`           | Port used when starting via `main.py` | `8000` |

## Testing & Quality
The pytest suite exercises the service layer to guarantee deterministic responses and validation errors. Extend `tests/test_attendance.py` when you add new scenarios.

Before opening a pull request run:
```bash
make format
make lint
make type-check
make test
```

## Docker Compose
The bundled `docker-compose.yml` spins up a single API container. Customise environment variables under the `attendance-api` service to match your deployment needs.

## License
MIT License. See `LICENSE` for details.
