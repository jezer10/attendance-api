from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from core.config import settings
from exceptions import PersistenceError

try:
    from postgrest.exceptions import APIError
    from supabase import Client, create_client
    from supabase_auth.errors import AuthApiError
except ImportError:  # pragma: no cover
    Client = Any  # type: ignore[assignment]

    class APIError(Exception):
        """Fallback APIError when supabase dependencies are missing."""

    class AuthApiError(Exception):
        """Fallback AuthApiError when supabase dependencies are missing."""

    def create_client(*_: Any, **__: Any) -> Any:  # type: ignore[override]
        raise PersistenceError(
            "Supabase client is unavailable. Install supabase dependencies to persist data."
        )


logger = logging.getLogger(__name__)


class AttendanceCredentialsRepository:
    """Persistence gateway for attendance login credentials."""

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or self._build_client()

    @staticmethod
    def _build_client() -> Client:
        key = settings.supabase_service_key or settings.supabase_key
        return create_client(settings.supabase_url, key)

    def upsert_credentials(
        self,
        *,
        user_id: str,
        company_id: int,
        user_id_number: int,
        password: str,
    ) -> None:
        existing = self._fetch_credentials_row(user_id=user_id)
        secret_id = existing.get("vault_secret_id") if existing else None

        if secret_id:
            self._update_secret(secret_id=secret_id, password=password)
        else:
            secret_id = self._create_secret(user_id=user_id, password=password)

        payload = {
            "user_id": user_id,
            "company_id": company_id,
            "user_id_number": user_id_number,
            "vault_secret_id": secret_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            (
                self._client.table("attendance_credentials")
                .upsert(payload, on_conflict="user_id", ignore_duplicates=False)
                .execute()
            )
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error persisting credentials for user %s: %s", user_id, exc
            )
            raise PersistenceError("Unable to persist attendance credentials") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected persistence error for user %s", user_id)
            raise PersistenceError("Unable to persist attendance credentials") from exc

    def fetch_credentials(self, *, user_id: str) -> Optional[dict]:
        record = self._fetch_credentials_row(user_id=user_id)
        if not record:
            return None
        secret_id = record.get("vault_secret_id")
        password = self._read_secret(secret_id=secret_id) if secret_id else None
        return {
            "company_id": record.get("company_id"),
            "user_id_number": record.get("user_id_number"),
            "password": password,
        }

    def _fetch_credentials_row(self, *, user_id: str) -> Optional[dict]:
        try:
            response = (
                self._client.table("attendance_credentials")
                .select("user_id,company_id,user_id_number,vault_secret_id")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error fetching credentials for user %s: %s", user_id, exc
            )
            raise PersistenceError("Unable to fetch attendance credentials") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected fetch error for user %s", user_id)
            raise PersistenceError("Unable to fetch attendance credentials") from exc

        if not getattr(response, "data", None):
            return None
        return response.data[0]

    def _create_secret(self, *, user_id: str, password: str) -> str:
        params = {
            "secret": password,
            "secret_name": f"attendance:{user_id}",
            "secret_description": "Attendance login password",
        }
        try:
            response = self._client.rpc("create_attendance_secret", params).execute()
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error creating vault secret for user %s: %s", user_id, exc
            )
            raise PersistenceError("Unable to store attendance credentials") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected vault error for user %s", user_id)
            raise PersistenceError("Unable to store attendance credentials") from exc

        secret_id = response.data
        if not secret_id:
            raise PersistenceError("Unable to store attendance credentials")
        return str(secret_id)

    def _update_secret(self, *, secret_id: str, password: str) -> None:
        params = {"secret_id": secret_id, "secret": password}
        try:
            self._client.rpc("update_attendance_secret", params).execute()
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error updating vault secret %s: %s", secret_id, exc
            )
            raise PersistenceError("Unable to update attendance credentials") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected vault update error for secret %s", secret_id)
            raise PersistenceError("Unable to update attendance credentials") from exc

    def _read_secret(self, *, secret_id: str) -> Optional[str]:
        params = {"secret_id": secret_id}
        try:
            response = self._client.rpc("read_attendance_secret", params).execute()
        except (AuthApiError, APIError) as exc:
            logger.warning("Supabase error reading vault secret %s: %s", secret_id, exc)
            raise PersistenceError("Unable to read attendance credentials") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected vault read error for secret %s", secret_id)
            raise PersistenceError("Unable to read attendance credentials") from exc
        return response.data if response else None
