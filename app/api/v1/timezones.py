from datetime import datetime, timezone
from functools import lru_cache
from typing import Iterable, List, Set

from fastapi import APIRouter

try:
    from zoneinfo import ZoneInfo, available_timezones
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency fallback
    import pytz
except ImportError:  # pragma: no cover
    pytz = None  # type: ignore[assignment]


router = APIRouter()


@lru_cache(maxsize=1)
def _build_timezone_catalog() -> List[str]:
    """Build a sorted list of timezones formatted as `UTC±HH:MM <region/name>`."""
    zones = _collect_timezone_names()
    if not zones:
        return ["UTC+00:00 UTC"]

    now_utc = datetime.now(timezone.utc)
    catalog = []

    for tz_name in zones:
        offset_minutes = _calculate_offset_minutes(tz_name, now_utc)
        if offset_minutes is None:
            continue

        sign = "+" if offset_minutes >= 0 else "-"
        hours, minutes = divmod(abs(offset_minutes), 60)
        catalog.append(
            (
                offset_minutes,
                tz_name,
                f"UTC{sign}{hours:02d}:{minutes:02d} {tz_name}",
            )
        )

    catalog.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in catalog]


def _collect_timezone_names() -> Set[str]:
    zones: Iterable[str] = set()
    if ZoneInfo is not None:
        try:
            zones = available_timezones()
        except Exception:
            zones = set()

    if (not zones or len(zones) == 0) and pytz is not None:
        zones = set(pytz.all_timezones)

    return set(zones)


def _calculate_offset_minutes(tz_name: str, now_utc: datetime) -> int | None:
    if ZoneInfo is not None:
        try:
            tz = ZoneInfo(tz_name)
            offset = now_utc.astimezone(tz).utcoffset()
            if offset is not None:
                return int(offset.total_seconds() // 60)
        except Exception:
            pass

    if pytz is not None:
        try:
            tz = pytz.timezone(tz_name)
            utc_dt = pytz.utc.localize(now_utc.replace(tzinfo=None))
            offset = tz.utcoffset(utc_dt)
            if offset is not None:
                return int(offset.total_seconds() // 60)
        except Exception:
            return None

    return None


@router.get("", response_model=List[str])
async def get_timezones() -> List[str]:
    """Return all supported timezones with their current UTC offsets."""
    return _build_timezone_catalog()
