from __future__ import annotations

import logging
from typing import Dict, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.exceptions import MarkingError

logger = logging.getLogger(__name__)

BASE_URL = "https://movil.asisscad.cl"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Origin": BASE_URL,
}


class MarkingService:
    """Handles the attendance marking flow against the external provider."""

    def mark_attendance(
        self,
        *,
        company_id: int,
        user_id_number: int,
        password: str,
        latitude: float,
        longitude: float,
        event_type: str,
    ) -> None:
        event_target = self._map_event_target(event_type)
        session = requests.Session()
        session.headers.update(HEADERS)

        login_response = session.get(BASE_URL, timeout=30)
        self._ensure_ok(login_response, "login page")

        login_data, login_action, login_method = self._extract_form_data(
            login_response.text
        )
        login_data["txt_id_empresa"] = company_id
        login_data["txt_id_usuario"] = user_id_number
        login_data["txt_pass"] = password
        login_data["__EVENTTARGET"] = "lnk_ingreso"

        login_url = urljoin(BASE_URL, login_action)
        logged_in = session.request(
            login_method, login_url, data=login_data, timeout=30
        )
        self._ensure_ok(logged_in, "login submit")

        geo_data, geo_action, geo_method = self._extract_form_data(logged_in.text)
        geo_data["txt_lat"] = latitude
        geo_data["txt_lon"] = longitude
        geo_data["hf_lat"] = latitude
        geo_data["hf_lon"] = longitude
        geo_data["__EVENTTARGET"] = "lnk_proceso"

        geo_url = urljoin(BASE_URL, geo_action)
        geo_response = session.request(geo_method, geo_url, data=geo_data, timeout=30)
        self._ensure_ok(geo_response, "geo submit")

        assist_data, assist_action, assist_method = self._extract_form_data(
            geo_response.text
        )
        assist_data["__EVENTTARGET"] = event_target

        assist_url = urljoin(BASE_URL, assist_action)
        final_response = session.request(
            assist_method, assist_url, data=assist_data, timeout=30
        )
        self._ensure_ok(final_response, "attendance submit")

    @staticmethod
    def _map_event_target(event_type: str) -> str:
        if event_type == "entry":
            return "lnk_entrada"
        if event_type == "exit":
            return "lnk_salida"
        raise MarkingError("Unsupported attendance event type")

    @staticmethod
    def _extract_form_data(html: str) -> Tuple[Dict[str, str], str, str]:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form")
        if not form:
            raise MarkingError("No form found in response")

        form_data: Dict[str, str] = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                form_data[name] = value
        action = form.get("action", "")
        method = form.get("method", "GET").upper()
        return form_data, action, method

    @staticmethod
    def _ensure_ok(response: requests.Response, step: str) -> None:
        if response.status_code >= 400:
            logger.warning("Marking failed at %s: %s", step, response.status_code)
            raise MarkingError(f"Failed to complete attendance marking at {step}")
