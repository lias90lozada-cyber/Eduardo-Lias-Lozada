import logging
import requests

logger = logging.getLogger("flex_bot")


class Notifier:
    def __init__(self, config: dict):
        notif = config.get("notifications", {})

        tg = notif.get("telegram", {})
        self.tg_enabled: bool = tg.get("enabled", False)
        self.tg_token: str = tg.get("bot_token", "")
        self.tg_chat_id: str = tg.get("chat_id", "")

        disc = notif.get("discord", {})
        self.discord_enabled: bool = disc.get("enabled", False)
        self.discord_webhook: str = disc.get("webhook_url", "")

    def notify(self, message: str, on_match: bool = False) -> None:
        if self.tg_enabled and self.tg_token and self.tg_chat_id:
            self._send_telegram(message)
        if self.discord_enabled and self.discord_webhook:
            self._send_discord(message)

    def _send_telegram(self, message: str) -> None:
        try:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            resp = requests.post(
                url,
                json={"chat_id": self.tg_chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
            if not resp.ok:
                logger.warning(f"[NOTIF] Telegram error: {resp.text[:200]}")
        except requests.RequestException as e:
            logger.warning(f"[NOTIF] Telegram sin conexion: {e}")

    def _send_discord(self, message: str) -> None:
        try:
            resp = requests.post(
                self.discord_webhook,
                json={"content": message},
                timeout=10,
            )
            if not resp.ok:
                logger.warning(f"[NOTIF] Discord error: {resp.text[:200]}")
        except requests.RequestException as e:
            logger.warning(f"[NOTIF] Discord sin conexion: {e}")
