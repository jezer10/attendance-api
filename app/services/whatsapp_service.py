import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.exceptions import NotificationError

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self) -> None:
        self._url = settings.whatsapp_template_url
        self._template_name = settings.whatsapp_template_name
        self._language_code = settings.whatsapp_language_code
        self._login_url = settings.whatsapp_auth_login_url
        self._refresh_url = settings.whatsapp_auth_refresh_url
        self._username = settings.whatsapp_auth_username
        self._password = settings.whatsapp_auth_password
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    async def send_template(
        self,
        *,
        wa_id: str,
        employee_name: str,
        checkin_date: str,
        checkin_time: str,
        location_address: str,
        location_latitude: float,
        location_longitude: float,
    ) -> Dict[str, Any]:
        payload = {
            "templateName": self._template_name,
            "languageCode": self._language_code,
            "body": {
                "map": {
                    "employee_name": {"type": "text", "text": employee_name},
                    "checkin_date": {"type": "text", "text": checkin_date},
                    "checkin_time": {"type": "text", "text": checkin_time},
                    "checkin_location": {
                        "type": "text",
                        "text": location_address,
                    },
                }
            },
            "header": {
                "type": "location",
                "location": {
                    "latitude": location_latitude,
                    "longitude": location_longitude,
                    "name": location_address,
                    "address": location_address,
                },
            },
            "waId": wa_id,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await self._post_template(client, payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("WhatsApp template request failed: %s", exc)
            raise NotificationError("Unable to send WhatsApp notification") from exc

        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code}

    async def _post_template(
        self, client: httpx.AsyncClient, payload: Dict[str, Any]
    ) -> httpx.Response:
        await self._ensure_access_token(client)
        response = await client.post(
            self._url,
            json=payload,
            headers=self._auth_headers(),
        )

        if response.status_code != 401:
            return response

        refreshed = await self._refresh_access_token(client)
        if refreshed:
            response = await client.post(
                self._url,
                json=payload,
                headers=self._auth_headers(),
            )
            if response.status_code != 401:
                return response

        await self._login(client)
        return await client.post(
            self._url,
            json=payload,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> Dict[str, str]:
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _ensure_access_token(self, client: httpx.AsyncClient) -> None:
        if self._access_token:
            return
        await self._login(client)

    async def _login(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            self._login_url, auth=(self._username, self._password)
        )
        if response.status_code >= 400:
            raise NotificationError("Unable to authenticate WhatsApp provider")
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if not access_token or not refresh_token:
            raise NotificationError("Missing WhatsApp authentication token")
        self._access_token = access_token
        self._refresh_token = refresh_token

    async def _refresh_access_token(self, client: httpx.AsyncClient) -> bool:
        if not self._refresh_token:
            return False
        response = await client.post(
            self._refresh_url,
            headers={"Authorization": f"Bearer {self._refresh_token}"},
        )
        if response.status_code >= 400:
            self._access_token = None
            self._refresh_token = None
            return False
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if not access_token:
            return False
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        return True
