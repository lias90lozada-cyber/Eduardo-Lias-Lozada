import time
import random
import logging
from datetime import datetime, date
from .api import FlexAPI
from .filters import BlockFilter
from .notifications import Notifier
from .stats import SessionStats

logger = logging.getLogger("flex_bot")


class BlockGrabber:
    def __init__(self, api: FlexAPI, filters: BlockFilter, notifier: Notifier,
                 config: dict, dry_run: bool = False):
        self.api = api
        self.filters = filters
        self.notifier = notifier
        self.dry_run = dry_run
        self.stats = SessionStats()

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
            logger.info("Nuevo dia — contador reiniciado.")

    def _sleep_interval(self) -> None:
        interval = float(self.poll_interval)
        if self.randomize:
            interval += random.uniform(-self.random_range, self.random_range)
            interval = max(5.0, interval)
        logger.debug(f"Esperando {interval:.1f}s...")
        time.sleep(interval)

    def _ensure_service_areas(self) -> bool:
        if not self.service_areas:
            logger.info("Buscando service areas automaticamente...")
            self.service_areas = self.api.get_service_areas()
            if not self.service_areas:
                logger.error("No se encontraron service areas.")
                return False
            logger.info(f"Service areas: {self.service_areas}")
        return True

    def _try_grab_offers(self) -> None:
        self.stats.polls += 1
        offers = self.api.get_offers(self.service_areas)

        if not offers:
            logger.debug("Sin bloques disponibles.")
            return

        self.stats.offers_seen += len(offers)
        new_offers = [o for o in offers if o.get("offerId") not in self.seen_offers]
        self.stats.offers_new += len(new_offers)

        if not new_offers:
            logger.debug(f"{len(offers)} bloques (todos ya vistos).")
            return

        logger.info(f"{len(offers)} bloque(s) — {len(new_offers)} nuevo(s).")

        for offer in new_offers:
            offer_id = offer.get("offerId", "")
            if not offer_id:
                continue
            self.seen_offers.add(offer_id)

            desc = self.filters.describe_offer(offer)
            passes, reason = self.filters.passes(offer)

            if not passes:
                self.stats.offers_skipped += 1
                logger.info(f"  SKIP  [{reason}] {desc}")
                continue

            self.stats.offers_matched += 1
            logger.info(f"  MATCH {desc}")
            self._accept_offer(offer_id, desc)

            if self.grabs_today >= self.max_grabs_per_day:
                logger.info(f"Limite diario ({self.max_grabs_per_day}) alcanzado.")
                return

    def _accept_offer(self, offer_id: str, desc: str) -> None:
        if self.dry_run:
            logger.info(f"  [DRY-RUN] No se acepto (modo prueba)")
            return

        logger.info(f"  Aceptando bloque {offer_id[:12]}...")
        success = self.api.accept_offer(offer_id)

        if success:
            self.grabs_today += 1
            self.stats.offers_accepted += 1
            ts = datetime.now().strftime("%H:%M:%S")
            msg = (
                f"✅ BLOQUE ACEPTADO [{ts}]\n"
                f"{desc}\n"
                f"Bloques hoy: {self.grabs_today}/{self.max_grabs_per_day}"
            )
            logger.info(msg)
            self.notifier.notify(msg)
        else:
            self.stats.offers_failed += 1
            logger.warning(f"  No se pudo aceptar {offer_id[:12]}")

    def run_once(self) -> None:
        """Un solo ciclo de polling — util para pruebas."""
        if self._ensure_service_areas():
            self._try_grab_offers()
        self.stats.print_summary()

    def start(self) -> None:
        mode = " [DRY-RUN]" if self.dry_run else ""
        logger.info("=" * 55)
        logger.info(f"  Amazon Flex Bot iniciado{mode}")
        logger.info(f"  Intervalo : {self.poll_interval}s (+/- {self.random_range}s)")
        logger.info(f"  Max/dia   : {self.max_grabs_per_day}")
        logger.info(f"  Areas     : {self.service_areas or 'auto'}")
        logger.info("=" * 55)

        self.running = True

        if not self._ensure_service_areas():
            logger.error("No se puede iniciar sin service areas.")
            return

        while self.running:
            self._reset_daily_counter()

            if self.grabs_today >= self.max_grabs_per_day:
                logger.info("Limite diario alcanzado. Esperando 1h...")
                time.sleep(3600)
                continue

            try:
                self._try_grab_offers()
            except Exception as e:
                self.stats.errors += 1
                logger.error(f"Error inesperado: {e}", exc_info=True)
                time.sleep(self.retry_interval)
                continue

            self._sleep_interval()

    def stop(self) -> None:
        self.running = False
        self.stats.print_summary()
        logger.info("Bot detenido.")
