import logging
import random
from typing import Optional

logger = logging.getLogger("flex_bot")


class ProxyManager:
    def __init__(self, config: dict):
        proxy_cfg = config.get("proxy", {})
        self.enabled: bool = proxy_cfg.get("enabled", False)
        self.rotate: bool = proxy_cfg.get("rotate", False)
        self._proxies: list[dict] = []
        self._index: int = 0

        if not self.enabled:
            return

        list_file = proxy_cfg.get("list_file", "")
        if list_file:
            self._load_from_file(list_file)
        else:
            single = self._build_single(proxy_cfg)
            if single:
                self._proxies.append(single)

        if self._proxies:
            logger.info(f"[PROXY] {len(self._proxies)} proxy(s) cargado(s).")
        else:
            logger.warning("[PROXY] Proxy habilitado pero no se encontraron proxies validos.")

    def _build_single(self, cfg: dict) -> Optional[dict]:
        host = cfg.get("host", "")
        port = cfg.get("port", "")
        if not host or not port:
            return None
        ptype = cfg.get("type", "http")
        user = cfg.get("username", "")
        pwd = cfg.get("password", "")
        auth = f"{user}:{pwd}@" if user and pwd else ""
        url = f"{ptype}://{auth}{host}:{port}"
        return {"http": url, "https": url}

    def _load_from_file(self, path: str) -> None:
        try:
            with open(path) as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for line in lines:
                if "://" not in line:
                    line = "http://" + line
                self._proxies.append({"http": line, "https": line})
        except FileNotFoundError:
            logger.error(f"[PROXY] Archivo de proxies no encontrado: {path}")

    def get(self) -> Optional[dict]:
        if not self.enabled or not self._proxies:
            return None
        if self.rotate:
            return random.choice(self._proxies)
        proxy = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        return proxy

    def mark_failed(self, proxy: dict) -> None:
        if proxy in self._proxies:
            self._proxies.remove(proxy)
            logger.warning(f"[PROXY] Proxy removido por fallo. Quedan {len(self._proxies)}.")
