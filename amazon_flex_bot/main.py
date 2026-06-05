#!/usr/bin/env python3
"""Amazon Flex Block Grabber Bot — python main.py --help"""

import argparse
import json
import logging
import signal
import sys
import os

from flex_bot import (
    FlexAuth, FlexAPI, BlockGrabber, BlockFilter,
    Notifier, ProxyManager, OTPRequired, CaptchaRequired,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(BASE_DIR, "config.json")
DEFAULT_TOKENS = os.path.join(BASE_DIR, "tokens.json")
DEFAULT_LOG = os.path.join(BASE_DIR, "flex_bot.log")


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(DEFAULT_LOG, encoding="utf-8"),
    ]
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=handlers)
    if not debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        print(f"ERROR: config.json no encontrado en {path}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def validate_config(config: dict) -> None:
    creds = config.get("credentials", {})
    if creds.get("email", "").strip() in ("", "TU_EMAIL@amazon.com"):
        print("ERROR: Configura tu email en config.json")
        sys.exit(1)
    if creds.get("password", "").strip() in ("", "TU_CONTRASEÑA"):
        print("ERROR: Configura tu password en config.json")
        sys.exit(1)


def build_auth(config: dict, debug: bool) -> FlexAuth:
    logger = logging.getLogger("flex_bot")
    creds = config["credentials"]
    region = config.get("region", "NA")

    proxy_mgr = ProxyManager(config)
    proxies = proxy_mgr.get() if proxy_mgr.enabled else None

    auth = FlexAuth(
        email=creds["email"],
        password=creds["password"],
        region=region,
        proxies=proxies,
        debug=debug,
    )

    logger.info(f"Iniciando sesion como {creds['email']} (region: {region})")

    if auth.load_tokens(DEFAULT_TOKENS):
        logger.info("Tokens cargados.")
        if not auth.is_token_valid():
            logger.info("Token expirado, renovando...")
            if not auth.refresh_access_token():
                logger.info("Refresh fallido, login nuevo...")
                _do_login(auth, logger)
    else:
        _do_login(auth, logger)

    auth.save_tokens(DEFAULT_TOKENS)
    logger.info("Sesion activa.")
    return auth


def _do_login(auth: FlexAuth, logger) -> None:
    try:
        if not auth.login_interactive():
            logger.error("No se pudo iniciar sesion.")
            sys.exit(1)
    except CaptchaRequired as e:
        logger.error(f"CAPTCHA requerido — no se puede resolver automaticamente: {e}")
        logger.error("Intenta iniciar sesion manualmente en la app de Amazon Flex primero.")
        sys.exit(1)


def cmd_run(args, config: dict) -> None:
    logger = logging.getLogger("flex_bot")
    auth = build_auth(config, args.debug)
    proxy_mgr = ProxyManager(config)
    api = FlexAPI(auth, proxy_manager=proxy_mgr, debug=args.debug)
    block_filter = BlockFilter(config)
    notifier = Notifier(config)
    grabber = BlockGrabber(api, block_filter, notifier, config, dry_run=args.dry_run)

    def handle_signal(sig, frame):
        logger.info("Senal recibida, deteniendo...")
        grabber.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if args.once:
        grabber.run_once()
    else:
        grabber.start()


def cmd_discover(args, config: dict) -> None:
    logger = logging.getLogger("flex_bot")
    auth = build_auth(config, args.debug)
    api = FlexAPI(auth, debug=args.debug)

    logger.info("Buscando service areas disponibles...")
    areas = api.get_service_areas()
    if not areas:
        logger.warning("No se encontraron service areas.")
        logger.warning("Asegurate de tener tu cuenta de Amazon Flex activa y la region correcta.")
        return

    logger.info(f"Se encontraron {len(areas)} service area(s):")
    for area in areas:
        logger.info(f"  {area}")
    logger.info("")
    logger.info("Copia los IDs que quieras usar en config.json -> service_areas")


def cmd_schedule(args, config: dict) -> None:
    logger = logging.getLogger("flex_bot")
    auth = build_auth(config, args.debug)
    api = FlexAPI(auth, debug=args.debug)

    logger.info("Obteniendo horario actual...")
    shifts = api.get_schedule()
    if not shifts:
        logger.info("No hay bloques programados.")
        return

    logger.info(f"{len(shifts)} bloque(s) en tu horario:")
    for s in shifts:
        offer_id = s.get("offerId", s.get("shiftId", "???"))[:12]
        start = s.get("startTime", "?")
        end = s.get("endTime", "?")
        station = s.get("serviceArea", {}).get("name") or s.get("stationCode", "?")
        logger.info(f"  ID:{offer_id} | {station} | {start} -> {end}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Amazon Flex Block Grabber Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                    # Iniciar el bot
  python main.py --dry-run          # Ver bloques sin aceptarlos
  python main.py --once             # Un solo ciclo de polling
  python main.py --debug            # Modo verbose (ver respuestas API)
  python main.py --discover-areas   # Ver tus service area IDs
  python main.py --schedule         # Ver tus bloques agendados
  python main.py --config mi_config.json  # Usar otro archivo de config
        """,
    )

    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="Ruta al archivo config.json")
    parser.add_argument("--debug", action="store_true",
                        help="Activar logs detallados (muestra respuestas de la API)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Ver bloques disponibles sin aceptarlos")
    parser.add_argument("--once", action="store_true",
                        help="Ejecutar un solo ciclo de polling y terminar")
    parser.add_argument("--discover-areas", action="store_true",
                        help="Mostrar tus service area IDs y terminar")
    parser.add_argument("--schedule", action="store_true",
                        help="Mostrar tu horario actual de Amazon Flex y terminar")

    args = parser.parse_args()
    setup_logging(args.debug)

    config = load_config(args.config)
    validate_config(config)

    if args.discover_areas:
        cmd_discover(args, config)
    elif args.schedule:
        cmd_schedule(args, config)
    else:
        cmd_run(args, config)


if __name__ == "__main__":
    main()
