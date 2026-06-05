import time
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("flex_bot")


@dataclass
class SessionStats:
    start_time: float = field(default_factory=time.time)
    polls: int = 0
    offers_seen: int = 0
    offers_new: int = 0
    offers_matched: int = 0
    offers_accepted: int = 0
    offers_failed: int = 0
    offers_skipped: int = 0
    errors: int = 0

    def elapsed_str(self) -> str:
        secs = int(time.time() - self.start_time)
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def print_summary(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("")
        logger.info("=" * 55)
        logger.info("  RESUMEN DE SESION")
        logger.info("=" * 55)
        logger.info(f"  Fecha/hora fin : {now}")
        logger.info(f"  Tiempo activo  : {self.elapsed_str()}")
        logger.info(f"  Polls realizados : {self.polls}")
        logger.info(f"  Bloques vistos   : {self.offers_seen}")
        logger.info(f"  Bloques nuevos   : {self.offers_new}")
        logger.info(f"  Bloques matchean : {self.offers_matched}")
        logger.info(f"  Bloques aceptados: {self.offers_accepted}")
        logger.info(f"  Bloques fallidos : {self.offers_failed}")
        logger.info(f"  Bloques saltados : {self.offers_skipped}")
        logger.info(f"  Errores          : {self.errors}")
        logger.info("=" * 55)
        logger.info("")
