import json
import uuid
import hashlib
import time
import logging
import requests
from typing import Optional

logger = logging.getLogger("flex_bot")

AMAZON_AUTH_URL = "https://api.amazon.com/auth/register"
AMAZON_TOKEN_URL = "https://api.amazon.com/auth/token"

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

OTP_CODES = {"OTP_REQUIRED", "MISSING_TOKEN", "MFA_REQUIRED", "2FA_REQUIRED"}
CAPTCHA_CODES = {"CAPTCHA_REQUIRED", "CAPTCHA_ERROR"}


class AuthError(Exception):
    pass


class OTPRequired(AuthError):
    pass


class CaptchaRequired(AuthError):
    pass


def _backoff(attempt: int, base: float = 2.0, cap: float = 30.0) -> None:
    delay = min(base ** attempt, cap)
    logger.debug(f"Backoff {delay:.1f}s (intento {attempt})")
    time.sleep(delay)


class FlexAuth:
    def __init__(self, email: str, password: str, region: str = "NA",
                 proxies: Optional[dict] = None, debug: bool = False):
        self.email = email
        self.password = password
        self.region = region
        self.base_url = REGION_URLS.get(region, REGION_URLS["NA"])
        self.debug = debug
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: float = 0.0
        self.device_id = self._generate_device_id()
        self.session = requests.Session()
        self.session.headers.update(HEADERS_BASE)
        if proxies:
            self.session.proxies.update(proxies)

    def _generate_device_id(self) -> str:
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32].upper()

    def is_token_valid(self) -> bool:
        return self.access_token is not None and time.time() < self.token_expires_at - 60

    def _build_register_payload(self, otp: Optional[str] = None) -> dict:
        auth_data: dict = {
            "user_id_password": {
                "user_id": self.email,
                "password": self.password,
            }
        }
        if otp:
            auth_data["otp"] = otp.strip()

        return {
            "auth_data": auth_data,
            "registration_data": {
                "domain": "DeviceLegacy",
                "device_type": "A3NWHXTQ4EBCZS",
                "device_serial": self.device_id,
                "device_model": "iPhone",
                "device_name": "%FIRST_NAME%'s iPhone",
                "os_version": "16.0",
                "software_version": "1",
            },
            "requested_token_type": ["bearer", "website_cookies"],
            "cookies": {"website_cookies": [], "domain": ".amazon.com"},
            "requested_extensions": ["device_info", "customer_info"],
        }

    def _post_with_retry(self, url: str, payload: dict, retries: int = 4) -> requests.Response:
        for attempt in range(retries):
            try:
                resp = self.session.post(url, json=payload, timeout=15)
                if self.debug:
                    logger.debug(f"POST {url} -> {resp.status_code} | {resp.text[:500]}")
                return resp
            except requests.RequestException as e:
                logger.warning(f"Error de red (intento {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    _backoff(attempt)
                else:
                    raise

    def login(self, otp: Optional[str] = None) -> bool:
        payload = self._build_register_payload(otp)
        try:
            resp = self._post_with_retry(AMAZON_AUTH_URL, payload)
        except requests.RequestException as e:
            logger.error(f"[AUTH] Sin conexion: {e}")
            return False

        data = resp.json()

        if resp.status_code == 200:
            return self._extract_tokens(data)

        error = data.get("response", {}).get("error", {})
        code = error.get("code", "")
        message = error.get("message", resp.text)

        if code in OTP_CODES:
            raise OTPRequired(f"Amazon requiere codigo 2FA: {message}")

        if code in CAPTCHA_CODES:
            raise CaptchaRequired(f"Amazon requiere CAPTCHA: {message}")

        logger.error(f"[AUTH] Login fallido [{code}]: {message}")
        return False

    def _extract_tokens(self, data: dict) -> bool:
        tokens = data.get("response", {}).get("success", {}).get("tokens", {})
        bearer = tokens.get("bearer", {})
        self.access_token = bearer.get("access_token")
        self.refresh_token = bearer.get("refresh_token")
        expires_in = int(bearer.get("expires_in", 3600))
        self.token_expires_at = time.time() + expires_in
        return bool(self.access_token)

    def login_interactive(self) -> bool:
        """Login con soporte interactivo para 2FA."""
        try:
            return self.login()
        except OTPRequired as e:
            logger.warning(str(e))
            otp = input(">>> Ingresa tu codigo de verificacion de Amazon (OTP/2FA): ").strip()
            if not otp:
                logger.error("No se ingreso codigo OTP.")
                return False
            return self.login(otp=otp)

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return self.login_interactive()

        payload = {
            "app_name": "com.amazon.rabbit",
            "app_version": "1.0",
            "source_token_type": "refresh_token",
            "source_token": self.refresh_token,
            "requested_token_type": "access_token",
        }

        try:
            resp = self._post_with_retry(AMAZON_TOKEN_URL, payload)
        except requests.RequestException:
            return self.login_interactive()

        if resp.status_code != 200:
            logger.warning("[AUTH] Refresh fallido, haciendo login nuevo...")
            return self.login_interactive()

        data = resp.json()
        self.access_token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        self.token_expires_at = time.time() + expires_in
        return bool(self.access_token)

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
            loaded_device = data.get("device_id")
            if loaded_device:
                self.device_id = loaded_device
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
