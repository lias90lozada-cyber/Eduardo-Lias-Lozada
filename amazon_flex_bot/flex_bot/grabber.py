import time
import random
import logging
from datetime import datetime, date
from .api import FlexAPI
from .filters import BlockFilter
from .notifications import Notifier

logger = logging.getLogger("flex_bot")


class BlockGrabber:
    def __init__(self, api: FlexAPI, filters: BlockFilter, notifier: Notifier, config: dict):
        self.api = api
        self.filters = filters
        self.notifier = notifier

        bot_cfg = config.get("bot", {})
        self.poll_interval: int = int(bot_cfg.get("poll_interval_seconds", 30))
        self.retry_interval: int = int(bot_cfg.get("retry_on_error_seconds", 60))
        self.max_grabs_per_day: int = int(bot_cfg.get("max_grabs_per_day", 2))
        self.randomize: bool = bot_cfg.get("randomize_interval", True)
        self.random_range: int = int(bot_cfg.get("randomize_range_seconds", 10))

        self.service_areas: list = config.get("service_areas", [])
        self.grabs_today: int = 0
        self.today: date = date.today()
        self.seen_offers: set = set()
        self.running: bool = False

    def _reset_daily_counter(self) -> None:
        today = date.today()
        if today != self.today:
            self.today = today
            self.grabs_today = 0
            self.seen_offers.clear()
            logger.info("Nuevo dia, contador reiniciado.")

    def _sleep_interval(self) -> None:
        interval = self.poll_interval
        if self.randomize:
            interval += random.uniform(-self.random_range, self.random_range)
            interval = max(5, interval)
        time.sleep(interval)

    def _ensure_service_areas(self) -> bool:
        if not self.service_areas:
            logger.info("Buscando service areas automaticamente...")
            self.service_areas = self.api.get_service_areas()
            if not self.service_areas:
                logger.error("No se encontraron service areas. Verifica tu ubicacion.")
                return False
            logger.info(f"Service areas encontradas: {self.service_areas}")
        return True

    def _try_grab_offers(self) -> None:
        offers = self.api.get_offers(self.service_areas)
        if not offers:
            logger.debug("Sin bloques disponibles.")
            return

        logger.info(f"{len(offers)} bloque(s) disponible(s).")

        for offer in offers:
            offer_id = offer.get("offerId", "")
            if not offer_id or offer_id in self.seen_offers:
                continue
            self.seen_offers.add(offer_id)

            desc = self.filters.describe_offer(offer)
            passes, reason = self.filters.passes(offer)

            if not passes:
                logger.info(f"  SKIP [{reason}] -> {desc}")
                continue

            logger.info(f"  MATCH -> {desc}")
            self._accept_offer(offer_id, desc)

            if self.grabs_today >= self.max_grabs_per_day:
                logger.info(f"Limite diario alcanzado ({self.max_grabs_per_day}). Deteniendo por hoy.")
                return

    def _accept_offer(self, offer_id: str, desc: str) -> None:
        logger.info(f"  Intentando aceptar bloque {offer_id[:12]}...")
        success = self.api.accept_offer(offer_id)

        if success:
            self.grabs_today += 1
            ts = datetime.now().strftime("%H:%M:%S")
            msg = (
                f"✅ BLOQUE ACEPTADO [{ts}]\n"
                f"{desc}\n"
                f"Bloques hoy: {self.grabs_today}/{self.max_grabs_per_day}"
            )
            logger.info(msg)
            self.notifier.notify(msg)
        else:
            logger.warning(f"  No se pudo aceptar el bloque {offer_id[:12]}")

    def start(self) -> None:
        logger.info("=" * 50)
        logger.info("Amazon Flex Bot iniciado")
        logger.info(f"Intervalo: {self.poll_interval}s | Max/dia: {self.max_grabs_per_day}")
        logger.info("=" * 50)

        self.running = True

        if not self._ensure_service_areas():
            logger.error("No se puede iniciar sin service areas.")
            return

        while self.running:
            self._reset_daily_counter()

            if self.grabs_today >= self.max_grabs_per_day:
                logger.info(f"Limite diario ({self.max_grabs_per_day}) ya alcanzado. Esperando manana...")
                time.sleep(3600)
                continue

            try:
                self._try_grab_offers()
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                time.sleep(self.retry_interval)
                continue

            self._sleep_interval()

    def stop(self) -> None:
        self.running = False
        logger.info("Bot detenido.")
