from __future__ import annotations

import logging
from datetime import time as dt_time
from typing import Any, Dict, Optional

from src.core.config import settings
from src.exceptions import PersistenceError
from src.models import (
    AttendanceRequest,
    AttendanceSchedule,
    ScheduleWindow,
    LocationData,
    DayOfWeek,
)

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


class AttendanceRepository:
    """Persistence gateway for attendance schedules stored in Supabase/Postgres."""

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or self._build_client()

    @staticmethod
    def _build_client() -> Client:
        key = settings.supabase_service_key or settings.supabase_key
        return create_client(settings.supabase_url, key)

    def upsert_schedule(
        self, *, user_id: str, recorded_by: Optional[str], request: AttendanceRequest
    ) -> None:
        payload = self._build_payload(
            user_id=user_id, recorded_by=recorded_by, request=request
        )

        try:
            (
                self._client.table("attendance_records")
                .upsert(payload, on_conflict="user_id", ignore_duplicates=False)
                .execute()
            )
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error persisting attendance for user %s: %s", user_id, exc
            )
            raise PersistenceError(
                "Unable to persist attendance configuration"
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected persistence error for user %s", user_id)
            raise PersistenceError(
                "Unable to persist attendance configuration"
            ) from exc

    def fetch_schedule(self, *, user_id: str) -> Optional[AttendanceRequest]:
        try:
            response = (
                self._client.table("attendance_records")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
        except (AuthApiError, APIError) as exc:
            logger.warning(
                "Supabase error fetching attendance for user %s: %s", user_id, exc
            )
            raise PersistenceError("Unable to fetch attendance configuration") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected fetch error for user %s", user_id)
            raise PersistenceError("Unable to fetch attendance configuration") from exc

        data = response.data[0] if getattr(response, "data", None) else None
        if not data:
            return None

        return AttendanceRepository._parse_payload(data)

    @staticmethod
    def _build_payload(
        *, user_id: str, recorded_by: Optional[str], request: AttendanceRequest
    ) -> Dict[str, Any]:
        entry = request.schedule.entry
        exit_window = request.schedule.exit
        location = request.location

        def _serialize_time(value: Optional[dt_time]) -> Optional[str]:
            if value is None:
                return None
            return value.strftime("%H:%M:%S")

        return {
            "user_id": user_id,
            "recorded_by": recorded_by,
            "is_active": request.is_active,
            "timezone": request.timezone,
            "random_window_minutes": request.random_window_minutes,
            "phone_number": request.phone_number,
            "entry_enabled": entry.enabled,
            "entry_local_time": _serialize_time(entry.local_time),
            "entry_utc_time": _serialize_time(entry.utc_time),
            "entry_days": [day.value for day in entry.days],
            "exit_enabled": exit_window.enabled,
            "exit_local_time": _serialize_time(exit_window.local_time),
            "exit_utc_time": _serialize_time(exit_window.utc_time),
            "exit_days": [day.value for day in exit_window.days],
            "location_address": location.address,
            "location_latitude": float(location.latitude),
            "location_longitude": float(location.longitude),
            "location_radius_meters": float(location.radius_meters),
        }

    @staticmethod
    def _parse_payload(payload: Dict[str, Any]) -> AttendanceRequest:
        def _parse_time(value: Optional[str]) -> Optional[dt_time]:
            if not value:
                return None
            return dt_time.fromisoformat(value)

        entry_days = [DayOfWeek(day) for day in payload.get("entry_days", [])]

        entry_window = ScheduleWindow(
            enabled=payload.get("entry_enabled", False),
            local_time=_parse_time(payload.get("entry_local_time")),
            utc_time=_parse_time(payload.get("entry_utc_time")),
            days=entry_days,
        )

        exit_window = ScheduleWindow(
            enabled=payload.get("exit_enabled", False),
            local_time=_parse_time(payload.get("exit_local_time")),
            utc_time=_parse_time(payload.get("exit_utc_time")),
            days=[DayOfWeek(day) for day in payload.get("exit_days", [])],
        )

        location = LocationData(
            address=payload["location_address"],
            latitude=float(payload["location_latitude"]),
            longitude=float(payload["location_longitude"]),
            radius_meters=float(payload["location_radius_meters"]),
        )

        return AttendanceRequest(
            is_active=payload["is_active"],
            schedule=AttendanceSchedule(entry=entry_window, exit=exit_window),
            location=location,
            phone_number=payload.get("phone_number"),
            random_window_minutes=payload.get("random_window_minutes", 0),
            timezone=payload["timezone"],
        )

    def fetch_event(self, *, event_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = (
                self._client.table("attendance_events")
                .select("*")
                .eq("id", event_id)
                .limit(1)
                .execute()
            )
        except (AuthApiError, APIError) as exc:
            logger.warning("Supabase error fetching event %s: %s", event_id, exc)
            raise PersistenceError("Unable to fetch attendance event") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected event fetch error for %s", event_id)
            raise PersistenceError("Unable to fetch attendance event") from exc

        data = response.data[0] if getattr(response, "data", None) else None
        return data or None
