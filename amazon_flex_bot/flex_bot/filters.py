from datetime import datetime
from typing import Optional


class BlockFilter:
    def __init__(self, config: dict):
        f = config.get("filters", {})
        self.min_pay: float = f.get("min_pay", 0.0)
        self.max_duration_hours: float = f.get("max_duration_hours", 999)
        self.min_duration_hours: float = f.get("min_duration_hours", 0)
        self.accepted_stations: list = [s.lower() for s in f.get("accepted_stations", [])]
        self.blocked_stations: list = [s.lower() for s in f.get("blocked_stations", [])]
        self.start_time_from: Optional[str] = f.get("start_time_from")
        self.start_time_to: Optional[str] = f.get("start_time_to")

    def _parse_time(self, t: str) -> int:
        h, m = t.split(":")
        return int(h) * 60 + int(m)

    def passes(self, offer: dict) -> tuple[bool, str]:
        pay = self._extract_pay(offer)
        if pay is not None and pay < self.min_pay:
            return False, f"Pago ${pay:.2f} < minimo ${self.min_pay:.2f}"

        duration_hours = self._extract_duration(offer)
        if duration_hours is not None:
            if duration_hours > self.max_duration_hours:
                return False, f"Duracion {duration_hours:.1f}h > maximo {self.max_duration_hours}h"
            if duration_hours < self.min_duration_hours:
                return False, f"Duracion {duration_hours:.1f}h < minimo {self.min_duration_hours}h"

        station = self._extract_station(offer)
        if station:
            station_lower = station.lower()
            if self.blocked_stations and any(b in station_lower for b in self.blocked_stations):
                return False, f"Estacion bloqueada: {station}"
            if self.accepted_stations and not any(a in station_lower for a in self.accepted_stations):
                return False, f"Estacion no en lista aceptada: {station}"

        start_time = self._extract_start_time(offer)
        if start_time and self.start_time_from and self.start_time_to:
            block_minutes = start_time.hour * 60 + start_time.minute
            from_minutes = self._parse_time(self.start_time_from)
            to_minutes = self._parse_time(self.start_time_to)
            if not (from_minutes <= block_minutes <= to_minutes):
                return False, f"Hora {start_time.strftime('%H:%M')} fuera del rango permitido"

        return True, "OK"

    def _extract_pay(self, offer: dict) -> Optional[float]:
        try:
            value = offer.get("rateInfo", {}).get("priceAmount", {}).get("amount")
            if value is None:
                value = offer.get("pay", {}).get("amount")
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _extract_duration(self, offer: dict) -> Optional[float]:
        try:
            start = offer.get("startTime")
            end = offer.get("endTime")
            if start and end:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (end_dt - start_dt).total_seconds() / 3600
            duration_mins = offer.get("durationMinutes")
            if duration_mins:
                return float(duration_mins) / 60
            return None
        except (ValueError, TypeError):
            return None

    def _extract_station(self, offer: dict) -> Optional[str]:
        return (
            offer.get("serviceArea", {}).get("name")
            or offer.get("stationCode")
            or offer.get("station", {}).get("name")
        )

    def _extract_start_time(self, offer: dict) -> Optional[datetime]:
        try:
            start = offer.get("startTime")
            if start:
                return datetime.fromisoformat(start.replace("Z", "+00:00"))
            return None
        except (ValueError, TypeError):
            return None

    def describe_offer(self, offer: dict) -> str:
        pay = self._extract_pay(offer)
        duration = self._extract_duration(offer)
        station = self._extract_station(offer)
        start = self._extract_start_time(offer)
        offer_id = offer.get("offerId", "???")[:12]

        parts = [f"ID:{offer_id}"]
        if station:
            parts.append(f"Estacion:{station}")
        if pay is not None:
            parts.append(f"${pay:.2f}")
        if duration is not None:
            parts.append(f"{duration:.1f}h")
        if start:
            parts.append(f"Inicio:{start.strftime('%a %H:%M')}")

        return " | ".join(parts)
