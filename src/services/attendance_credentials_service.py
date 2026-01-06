from __future__ import annotations

import logging
from typing import Optional

from src.exceptions import ValidationError
from src.services.attendance_credentials_repository import (
    AttendanceCredentialsRepository,
)

logger = logging.getLogger(__name__)


class AttendanceCredentialsService:
    """Handles attendance login credential management."""

    def __init__(
        self, repository: Optional[AttendanceCredentialsRepository] = None
    ) -> None:
        self._repository = repository or AttendanceCredentialsRepository()

    def save_credentials(
        self,
        *,
        user_id: Optional[str],
        company_id: int,
        user_id_number: int,
        password: str,
    ) -> None:
        if not user_id:
            raise ValidationError("Authenticated user context is required")
        self._repository.upsert_credentials(
            user_id=user_id,
            company_id=company_id,
            user_id_number=user_id_number,
            password=password,
        )

    def get_credentials(self, *, user_id: Optional[str]) -> Optional[dict]:
        if not user_id:
            raise ValidationError("Authenticated user context is required")
        return self._repository.fetch_credentials(user_id=user_id)
