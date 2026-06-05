from datetime import datetime
from typing import Optional

DAYS_MAP = {
    "lun": 0, "lunes": 0, "mon": 0, "monday": 0,
    "mar": 1, "martes": 1, "tue": 1, "tuesday": 1,
    "mie": 2, "miercoles": 2, "wed": 2, "wednesday": 2,
    "jue": 3, "jueves": 3, "thu": 3, "thursday": 3,
    "vie": 4, "viernes": 4, "fri": 4, "friday": 4,
    "sab": 5, "sabado": 5, "sat": 5, "saturday": 5,
    "dom": 6, "domingo": 6, "sun": 6, "sunday": 6,
}


class BlockFilter:
    def __init__(self, config: dict):
        f = config.get("filters", {})
        self.min_pay: float = f.get("min_pay", 0.0)
        self.min_pay_per_hour: float = f.get("min_pay_per_hour", 0.0)
        self.max_duration_hours: float = f.get("max_duration_hours", 999)
        self.min_duration_hours: float = f.get("min_duration_hours", 0)
        self.accepted_stations: list = [s.lower() for s in f.get("accepted_stations", [])]
        self.blocked_stations: list = [s.lower() for s in f.get("blocked_stations", [])]
        self.start_time_from: Optional[str] = f.get("start_time_from")
        self.start_time_to: Optional[str] = f.get("start_time_to")
        self.max_start_days_ahead: Optional[int] = f.get("max_start_days_ahead")
        raw_days = f.get("days_of_week", [])
        self.days_of_week: Optional[list] = self._parse_days(raw_days) if raw_days else None

    def _parse_days(self, raw: list) -> list:
        result = []
        for d in raw:
            key = str(d).lower().strip()
            if key in DAYS_MAP:
                result.append(DAYS_MAP[key])
            elif key.isdigit() and 0 <= int(key) <= 6:
                result.append(int(key))
        return result

    def _parse_time(self, t: str) -> int:
        h, m = t.split(":")
        return int(h) * 60 + int(m)

    def passes(self, offer: dict) -> tuple[bool, str]:
        pay = self._extract_pay(offer)
        duration_hours = self._extract_duration(offer)

        if pay is not None and pay < self.min_pay:
            return False, f"Pago ${pay:.2f} < minimo ${self.min_pay:.2f}"

        if pay is not None and duration_hours is not None and self.min_pay_per_hour > 0:
            pph = pay / duration_hours if duration_hours > 0 else 0
            if pph < self.min_pay_per_hour:
                return False, f"${pph:.2f}/h < minimo ${self.min_pay_per_hour:.2f}/h"

        if duration_hours is not None:
            if duration_hours > self.max_duration_hours:
                return False, f"Duracion {duration_hours:.1f}h > maximo {self.max_duration_hours}h"
            if duration_hours < self.min_duration_hours:
                return False, f"Duracion {duration_hours:.1f}h < minimo {self.min_duration_hours}h"

        station = self._extract_station(offer)
        if station:
            sl = station.lower()
            if self.blocked_stations and any(b in sl for b in self.blocked_stations):
                return False, f"Estacion bloqueada: {station}"
            if self.accepted_stations and not any(a in sl for a in self.accepted_stations):
                return False, f"Estacion no en lista: {station}"

        start_time = self._extract_start_time(offer)
        if start_time:
            if self.start_time_from and self.start_time_to:
                block_mins = start_time.hour * 60 + start_time.minute
                if not (self._parse_time(self.start_time_from) <= block_mins
                        <= self._parse_time(self.start_time_to)):
                    return False, f"Hora {start_time.strftime('%H:%M')} fuera del rango"

            if self.days_of_week is not None:
                if start_time.weekday() not in self.days_of_week:
                    return False, f"Dia {start_time.strftime('%A')} no permitido"

            if self.max_start_days_ahead is not None:
                now = datetime.now(tz=start_time.tzinfo)
                days_ahead = (start_time - now).total_seconds() / 86400
                if days_ahead > self.max_start_days_ahead:
                    return False, f"Bloque empieza en {days_ahead:.1f} dias (max {self.max_start_days_ahead})"

        return True, "OK"

    def _extract_pay(self, offer: dict) -> Optional[float]:
        try:
            v = offer.get("rateInfo", {}).get("priceAmount", {}).get("amount")
            if v is None:
                v = offer.get("pay", {}).get("amount")
            if v is None:
                v = offer.get("totalPayment", {}).get("amount")
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    def _extract_duration(self, offer: dict) -> Optional[float]:
        try:
            start = offer.get("startTime")
            end = offer.get("endTime")
            if start and end:
                s = datetime.fromisoformat(start.replace("Z", "+00:00"))
                e = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (e - s).total_seconds() / 3600
            mins = offer.get("durationMinutes")
            if mins:
                return float(mins) / 60
            return None
        except (ValueError, TypeError):
            return None

    def _extract_station(self, offer: dict) -> Optional[str]:
        return (
            offer.get("serviceArea", {}).get("name")
            or offer.get("stationCode")
            or offer.get("station", {}).get("name")
            or offer.get("serviceAreaName")
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
            parts.append(f"{station}")
        if pay is not None:
            if duration and duration > 0:
                pph = pay / duration
                parts.append(f"${pay:.2f} (${pph:.2f}/h)")
            else:
                parts.append(f"${pay:.2f}")
        if duration is not None:
            parts.append(f"{duration:.1f}h")
        if start:
            parts.append(f"{start.strftime('%a %m/%d %H:%M')}")

        return " | ".join(parts)
