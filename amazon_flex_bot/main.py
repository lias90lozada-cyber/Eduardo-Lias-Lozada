#!/usr/bin/env python3
"""
Amazon Flex Block Grabber Bot
Configura config.json antes de ejecutar.
"""

import json
import logging
import signal
import sys
import os
from flex_bot import FlexAuth, FlexAPI, BlockGrabber, BlockFilter, Notifier

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
TOKENS_FILE = os.path.join(os.path.dirname(__file__), "tokens.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("flex_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("flex_bot")


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Archivo config.json no encontrado en {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)


def validate_config(config: dict) -> None:
    creds = config.get("credentials", {})
    if creds.get("email") in ("", "TU_EMAIL@amazon.com"):
        logger.error("Configura tu email en config.json")
        sys.exit(1)
    if creds.get("password") in ("", "TU_CONTRASEÑA"):
        logger.error("Configura tu password en config.json")
        sys.exit(1)


def main() -> None:
    config = load_config()
    validate_config(config)

    creds = config["credentials"]
    region = config.get("region", "NA")

    auth = FlexAuth(
        email=creds["email"],
        password=creds["password"],
        region=region,
    )

    logger.info(f"Iniciando sesion como {creds['email']} (region: {region})")

    if auth.load_tokens(TOKENS_FILE):
        logger.info("Tokens cargados desde archivo.")
        if not auth.is_token_valid():
            logger.info("Tokens expirados, renovando...")
            if not auth.refresh_access_token():
                logger.info("Renovacion fallida, iniciando sesion nueva...")
                if not auth.login():
                    logger.error("No se pudo iniciar sesion. Verifica tus credenciales.")
                    sys.exit(1)
    else:
        if not auth.login():
            logger.error("No se pudo iniciar sesion. Verifica tus credenciales.")
            sys.exit(1)

    auth.save_tokens(TOKENS_FILE)
    logger.info("Sesion iniciada correctamente.")

    api = FlexAPI(auth)
    block_filter = BlockFilter(config)
    notifier = Notifier(config)
    grabber = BlockGrabber(api, block_filter, notifier, config)

    def handle_signal(sig, frame):
        logger.info("Senal recibida, deteniendo bot...")
        grabber.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    grabber.start()


if __name__ == "__main__":
    main()
