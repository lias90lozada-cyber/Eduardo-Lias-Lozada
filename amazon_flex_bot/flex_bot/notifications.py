import requests


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

    def notify(self, message: str) -> None:
        if self.tg_enabled and self.tg_token and self.tg_chat_id:
            self._send_telegram(message)
        if self.discord_enabled and self.discord_webhook:
            self._send_discord(message)

    def _send_telegram(self, message: str) -> None:
        try:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            requests.post(
                url,
                json={"chat_id": self.tg_chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
        except requests.RequestException as e:
            print(f"[NOTIF] Error Telegram: {e}")

    def _send_discord(self, message: str) -> None:
        try:
            requests.post(
                self.discord_webhook,
                json={"content": message},
                timeout=10,
            )
        except requests.RequestException as e:
            print(f"[NOTIF] Error Discord: {e}")
