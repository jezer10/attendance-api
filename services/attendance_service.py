import logging
from typing import Dict, Tuple
from urllib.parse import urljoin
from datetime import datetime
from httpx import Response, AsyncClient, RequestError, HTTPStatusError
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from models import (
    AttendanceRequest,
    AttendanceResponse,
    AttendanceAction,
    LocationData,
    UserCredentials,
)
from exceptions import AuthenticationError, NetworkError, FormParsingError
from config import settings
from bs4 import BeautifulSoup

from utils.html import get_user_info, get_date_info, extract_attendance_data, get_error_message
from utils.time import time_diff_seconds
from utils.location import generate_random_points_geopy

logger = logging.getLogger(__name__)


class AttendanceService:
    def __init__(self):
        self.base_url = settings.base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Origin": self.base_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9",
        }

    async def __aenter__(self):
        self.client = AsyncClient(
            headers=self.headers, timeout=settings.request_timeout, follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @staticmethod
    def extract_form_data(html: str) -> Tuple[Dict[str, str], str, str]:
        """Extract form data, action URL, and method from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            form = soup.find("form")

            if not form:
                raise FormParsingError("No form found in the HTML")

            form_data = {}
            for input_tag in form.find_all("input"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value

            action = form.get("action", "")
            method = form.get("method", "GET").upper()

            return form_data, action, method

        except Exception as e:
            logger.error(f"Error parsing form data: {e}")
            raise FormParsingError(f"Failed to parse form data: {str(e)}")

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(NetworkError),
    )
    async def make_request(self, method: str, url: str, data: Dict = None) -> Response:
        """Make HTTP request with retry logic"""
        try:
            response = await self.client.request(method, url, data=data)
            response.raise_for_status()
            return response
        except RequestError as e:
            logger.error(f"Network error: {e}")
            raise NetworkError(f"Network request failed: {str(e)}")
        except HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise NetworkError(f"HTTP error {e.response.status_code}")

    async def get_ip_address(self):
        """Get the public IP address of the client"""
        try:
            response = await self.make_request("GET", "https://api.ipify.org")
            return response.text
        except Exception as e:
            logger.error(f"Failed to get IP address: {e}")
            raise NetworkError(f"Failed to get IP address: {str(e)}")

    async def login(self, credentials: UserCredentials) -> Response:
        """Authenticate user"""
        # Get login page
        login_response = await self.make_request("GET", self.base_url)
        login_data, login_action, login_method = self.extract_form_data(
            login_response.text
        )

        # Fill login credentials
        login_data.update(
            {
                "txt_id_empresa": settings.company_id,
                "txt_id_usuario": credentials.user_id,
                "txt_pass": credentials.password,
                "__EVENTTARGET": "lnk_ingreso",
            }
        )
        logger.info(f"Login data: {login_data}")

        # Submit login
        login_url = urljoin(self.base_url, login_action)
        response = await self.make_request(login_method, login_url, login_data)
        error_message = get_error_message(response.text)
        if error_message:
            logger.error(f"Login error: {error_message}")
            raise AuthenticationError(error_message)

        return response, get_user_info(response.text)

      

    async def submit_location(
        self, location_response: Response, location: LocationData
    ) -> Response:
        """Submit location data"""
        geo_data, geo_action, geo_method = self.extract_form_data(
            location_response.text
        )

        geo_data.update(
            {
                "txt_lat": location.latitude,
                "txt_lon": location.longitude,
                "hf_lat": location.latitude,
                "hf_lon": location.longitude,
                "__EVENTTARGET": "lnk_proceso",
            }
        )

        geo_url = urljoin(self.base_url, geo_action)
        response = await self.make_request(geo_method, geo_url, geo_data)
        return response, get_date_info(response.text)

    async def mark_attendance(
        self, attendance_response: Response, action: AttendanceAction
    ) -> Response:
        """Mark attendance (entry or exit)"""
        assist_data, assist_action, assist_method = self.extract_form_data(
            attendance_response.text
        )
        assist_data["__EVENTTARGET"] = action.value

        assist_url = urljoin(self.base_url, assist_action)
        return await self.make_request(assist_method, assist_url, assist_data)

    def parse_response_success(self, response_text: str) -> Tuple[bool, str]:
        """Parse response to determine if attendance was successful"""
        soup = BeautifulSoup(response_text, "html.parser")

        success_indicators = [
            "éxito",
            "registrado",
            "completado",
            "success",
            "entrada",
            "salida",
        ]
        error_indicators = ["error", "fallo", "problema", "failed", "incorrect"]

        response_text_lower = soup.get_text().lower()

        if any(indicator in response_text_lower for indicator in success_indicators):
            return True, "Attendance marked successfully"
        elif any(indicator in response_text_lower for indicator in error_indicators):
            return False, "Failed to mark attendance"
        else:
            return True, "Attendance request processed"

    async def process_attendance(
        self, request: AttendanceRequest
    ) -> AttendanceResponse:
        """Main method to process attendance request"""
        try:
            logger.info(f"Processing attendance for user {request.credentials.user_id}")

            ip_address = await self.get_ip_address()
            # Step 1: Login
            location_response, user_info = await self.login(request.credentials)

            if not location_response or not user_info:
                raise AuthenticationError("Failed to retrieve user information")
      

            if ip_address != user_info["ip"]:
                raise AuthenticationError("IP address mismatch")

            # Step 2: Submit location
            attendance_response, date_info = await self.submit_location(
                location_response, request.location
            )
            seconds = time_diff_seconds(date_info)

            if seconds is None:
                raise AuthenticationError("Time difference exceeded")

            # with open("response-template.html", "r", encoding="utf-8") as f:
            #     template = f.read()

            # print(extract_attendance_data(template))
            element = generate_random_points_geopy(
                settings.latitude, settings.longitude
            )


            for lat,long in element:
                pass
            print(lat, long)
            # Step 3: Mark attendance
            final_response = await self.mark_attendance(
                attendance_response, request.action
            )

            # Parse response to determine success
            success, message = self.parse_response_success(final_response.text)
            html_content = final_response.text

            print(extract_attendance_data(html_content))


            with open("page.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            return AttendanceResponse(
                success=True,
                message="Attendance marked successfully",
                action=request.action,
                timestamp=datetime.now(),
                location=request.location,
            )
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return AttendanceResponse(
                success=False,
                message=str(e),
                action=request.action,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Attendance processing failed: {e}")
            return AttendanceResponse(
                success=False,
                message=f"Process failed: {str(e)}",
                action=request.action,
                timestamp=datetime.now(),
            )
