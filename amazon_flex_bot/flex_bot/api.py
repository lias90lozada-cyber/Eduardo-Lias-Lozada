import uuid
import time
import requests
from typing import Optional
from .auth import FlexAuth

REGION_URLS = {
    "NA": "https://flex-capacity-na.amazon.com",
    "EU": "https://flex-capacity-eu.amazon.com",
    "FE": "https://flex-capacity-fe.amazon.com",
}


class FlexAPI:
    def __init__(self, auth: FlexAuth):
        self.auth = auth
        self.base_url = REGION_URLS.get(auth.region, REGION_URLS["NA"])
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

    def get_service_areas(self) -> list:
        try:
            resp = self.session.get(
                f"{self.base_url}/ServiceAreas",
                headers=self._headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("serviceAreaIds", [])
            return []
        except requests.RequestException as e:
            print(f"[API] Error obteniendo service areas: {e}")
            return []

    def get_offers(self, service_area_ids: list) -> list:
        if not service_area_ids:
            return []

        payload = {
            "serviceAreaIds": service_area_ids,
            "apiVersion": "V2",
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/GetOffersForProvider",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("offerList", [])
            if resp.status_code == 401:
                print("[API] Token expirado, renovando...")
                self.auth.refresh_access_token()
            return []
        except requests.RequestException as e:
            print(f"[API] Error obteniendo bloques: {e}")
            return []

    def accept_offer(self, offer_id: str) -> bool:
        payload = {
            "offerId": offer_id,
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/AcceptOffer",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[API] Error aceptando bloque: {e}")
            return False

    def forfeit_offer(self, offer_id: str) -> bool:
        payload = {
            "offerId": offer_id,
            "forfeited": True,
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/ForfeitOffer",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[API] Error abandonando bloque: {e}")
            return False

    def get_schedule(self) -> list:
        try:
            resp = self.session.get(
                f"{self.base_url}/Shifts",
                headers=self._headers(),
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("shiftList", [])
            return []
        except requests.RequestException as e:
            print(f"[API] Error obteniendo horario: {e}")
            return []
