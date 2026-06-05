import uuid
import time
import logging
import requests
from typing import Optional
from .auth import FlexAuth
from .proxy import ProxyManager

logger = logging.getLogger("flex_bot")

REGION_URLS = {
    "NA": "https://flex-capacity-na.amazon.com",
    "EU": "https://flex-capacity-eu.amazon.com",
    "FE": "https://flex-capacity-fe.amazon.com",
}


def _backoff(attempt: int, base: float = 2.0, cap: float = 30.0) -> None:
    delay = min(base ** attempt, cap)
    logger.debug(f"Backoff {delay:.1f}s (intento {attempt})")
    time.sleep(delay)


class FlexAPI:
    def __init__(self, auth: FlexAuth, proxy_manager: Optional[ProxyManager] = None,
                 debug: bool = False, retries: int = 4):
        self.auth = auth
        self.base_url = REGION_URLS.get(auth.region, REGION_URLS["NA"])
        self.proxy_manager = proxy_manager
        self.debug = debug
        self.retries = retries
        self.session = requests.Session()

    def _headers(self) -> dict:
        token = self.auth.get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "com.amazon.rabbit/1.0/iOS/16.0/iPhone",
            "Accept": "application/json",
            "Accept-Language": "en-US",
            "x-amzn-RequestId": str(uuid.uuid4()),
            "x-flex-Instance-Id": self.auth.device_id,
        }

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        proxy = self.proxy_manager.get() if self.proxy_manager else None

        for attempt in range(self.retries):
            try:
                if proxy:
                    kwargs["proxies"] = proxy
                resp = self.session.request(method, url, timeout=15, **kwargs)

                if self.debug:
                    body = kwargs.get("json", "")
                    logger.debug(f"{method} {url}")
                    logger.debug(f"  Body: {body}")
                    logger.debug(f"  Status: {resp.status_code}")
                    logger.debug(f"  Response: {resp.text[:800]}")

                if resp.status_code == 401:
                    logger.warning("[API] Token expirado, renovando...")
                    self.auth.refresh_access_token()
                    self.auth.save_tokens()
                    kwargs["headers"] = self._headers()
                    continue

                if resp.status_code == 429:
                    logger.warning("[API] Rate limit. Esperando...")
                    _backoff(attempt + 1, base=5.0)
                    continue

                return resp

            except requests.ProxyError:
                logger.warning(f"[PROXY] Fallo con proxy (intento {attempt + 1})")
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_failed(proxy)
                    proxy = self.proxy_manager.get()
                if attempt < self.retries - 1:
                    _backoff(attempt)

            except requests.RequestException as e:
                logger.warning(f"[API] Error de red (intento {attempt + 1}/{self.retries}): {e}")
                if attempt < self.retries - 1:
                    _backoff(attempt)

        return None

    def get_service_areas(self) -> list:
        resp = self._request("GET", f"{self.base_url}/ServiceAreas", headers=self._headers())
        if resp and resp.status_code == 200:
            return resp.json().get("serviceAreaIds", [])
        return []

    def get_offers(self, service_area_ids: list) -> list:
        if not service_area_ids:
            return []
        payload = {"serviceAreaIds": service_area_ids, "apiVersion": "V2"}
        resp = self._request("POST", f"{self.base_url}/GetOffersForProvider",
                             headers=self._headers(), json=payload)
        if resp and resp.status_code == 200:
            return resp.json().get("offerList", [])
        return []

    def accept_offer(self, offer_id: str) -> bool:
        payload = {"offerId": offer_id}
        resp = self._request("POST", f"{self.base_url}/AcceptOffer",
                             headers=self._headers(), json=payload)
        return resp is not None and resp.status_code == 200

    def forfeit_offer(self, offer_id: str) -> bool:
        payload = {"offerId": offer_id, "forfeited": True}
        resp = self._request("POST", f"{self.base_url}/ForfeitOffer",
                             headers=self._headers(), json=payload)
        return resp is not None and resp.status_code == 200

    def get_schedule(self) -> list:
        resp = self._request("GET", f"{self.base_url}/Shifts", headers=self._headers())
        if resp and resp.status_code == 200:
            return resp.json().get("shiftList", [])
        return []

    def get_eligibility(self) -> dict:
        resp = self._request("GET", f"{self.base_url}/Eligibility", headers=self._headers())
        if resp and resp.status_code == 200:
            return resp.json()
        return {}
