import json
import uuid
import hashlib
import time
import requests
from typing import Optional

AMAZON_AUTH_URL = "https://api.amazon.com/auth/register"
FLEX_AUTH_URL = "https://flex-capacity-na.amazon.com"

REGION_URLS = {
    "NA": "https://flex-capacity-na.amazon.com",
    "EU": "https://flex-capacity-eu.amazon.com",
    "FE": "https://flex-capacity-fe.amazon.com",
}

HEADERS_BASE = {
    "Content-Type": "application/json",
    "User-Agent": "com.amazon.rabbit/1.0/iOS/16.0/iPhone",
    "Accept": "application/json",
    "Accept-Language": "en-US",
    "x-amzn-identity-auth-domain": "api.amazon.com",
}


class FlexAuth:
    def __init__(self, email: str, password: str, region: str = "NA"):
        self.email = email
        self.password = password
        self.region = region
        self.base_url = REGION_URLS.get(region, REGION_URLS["NA"])
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: float = 0.0
        self.device_id = self._generate_device_id()
        self.session = requests.Session()
        self.session.headers.update(HEADERS_BASE)

    def _generate_device_id(self) -> str:
        unique = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32].upper()
        return unique

    def is_token_valid(self) -> bool:
        return self.access_token is not None and time.time() < self.token_expires_at - 60

    def login(self) -> bool:
        payload = {
            "auth_data": {
                "user_id_password": {
                    "user_id": self.email,
                    "password": self.password,
                }
            },
            "registration_data": {
                "domain": "DeviceLegacy",
                "device_type": "A3NWHXTQ4EBCZS",
                "device_serial": self.device_id,
                "device_model": "iPhone",
                "device_name": f"%FIRST_NAME%'s iPhone",
                "os_version": "16.0",
                "software_version": "1",
            },
            "requested_token_type": [
                "bearer",
                "website_cookies",
            ],
            "cookies": {
                "website_cookies": [],
                "domain": ".amazon.com",
            },
            "requested_extensions": [
                "device_info",
                "customer_info",
            ],
        }

        try:
            resp = self.session.post(
                AMAZON_AUTH_URL,
                json=payload,
                timeout=15,
            )
            data = resp.json()

            if resp.status_code != 200:
                error = data.get("response", {}).get("error", {})
                print(f"[AUTH] Error al iniciar sesion: {error.get('message', resp.text)}")
                return False

            tokens = data.get("response", {}).get("success", {}).get("tokens", {})
            bearer = tokens.get("bearer", {})
            self.access_token = bearer.get("access_token")
            self.refresh_token = bearer.get("refresh_token")
            expires_in = int(bearer.get("expires_in", 3600))
            self.token_expires_at = time.time() + expires_in
            return bool(self.access_token)

        except requests.RequestException as e:
            print(f"[AUTH] Error de red: {e}")
            return False

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return self.login()

        payload = {
            "app_name": "com.amazon.rabbit",
            "app_version": "1.0",
            "source_token_type": "refresh_token",
            "source_token": self.refresh_token,
            "requested_token_type": "access_token",
        }

        try:
            resp = self.session.post(
                "https://api.amazon.com/auth/token",
                json=payload,
                timeout=15,
            )
            data = resp.json()

            if resp.status_code != 200:
                return self.login()

            self.access_token = data.get("access_token")
            expires_in = int(data.get("expires_in", 3600))
            self.token_expires_at = time.time() + expires_in
            return bool(self.access_token)

        except requests.RequestException:
            return self.login()

    def get_valid_token(self) -> Optional[str]:
        if not self.is_token_valid():
            if not self.refresh_access_token():
                return None
        return self.access_token

    def save_tokens(self, path: str = "tokens.json") -> None:
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expires_at": self.token_expires_at,
            "device_id": self.device_id,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_tokens(self, path: str = "tokens.json") -> bool:
        try:
            with open(path) as f:
                data = json.load(f)
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.token_expires_at = float(data.get("token_expires_at", 0))
            self.device_id = data.get("device_id", self.device_id)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
