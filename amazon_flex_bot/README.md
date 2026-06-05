# Amazon Flex Block Grabber Bot

Bot en Python para agarrar bloques de Amazon Flex automaticamente.

> ¿Vas a continuar el desarrollo? Lee **HANDOFF.md** — tiene el estado completo,
> arquitectura, endpoints y las tareas pendientes.

## Instalacion

```bash
cd amazon_flex_bot
pip install -r requirements.txt
```

## Configuracion

Edita `config.json` con tu email, password y filtros. Parametros clave:

| Campo | Descripcion |
|-------|-------------|
| `region` | `NA` USA/Canada, `EU` Europa, `FE` Japon/Australia |
| `service_areas` | Vacio `[]` = detectar automatico (ver `--discover-areas`) |
| `min_pay` | Pago minimo total en dolares |
| `min_pay_per_hour` | Pago minimo por hora (0 = desactivado) |
| `max/min_duration_hours` | Duracion del bloque |
| `accepted_stations` | Codigos aceptados, ej `["DLA5"]`. Vacio = todas |
| `blocked_stations` | Estaciones a ignorar |
| `start_time_from/to` | Rango de hora de inicio `HH:MM` |
| `days_of_week` | Dias permitidos: `["lun","vie"]` o `[0,4]`. Vacio = todos |
| `max_start_days_ahead` | Maximo dias de anticipacion (`null` = sin limite) |
| `poll_interval_seconds` | Segundos entre consultas |
| `max_grabs_per_day` | Maximo de bloques por dia |
| `proxy.enabled` | Activar proxy / rotacion de IPs |

## Uso

```bash
python main.py                    # Iniciar el bot
python main.py --dry-run          # Ver bloques SIN aceptarlos (probar filtros)
python main.py --once             # Un solo ciclo de polling y salir
python main.py --debug            # Logs detallados (request/response API)
python main.py --discover-areas   # Listar tus service area IDs
python main.py --schedule         # Ver tus bloques ya agendados
python main.py --help             # Ver toda la ayuda
```

El bot guarda tokens en `tokens.json` (no hace login cada vez) y logs en
`flex_bot.log`. Para detenerlo: `Ctrl+C` (muestra resumen de la sesion).

## 2FA / Verificacion en 2 pasos

Si tu cuenta tiene 2FA activado, el bot te pedira el codigo automaticamente
en la terminal durante el login. No necesitas desactivar nada.

## Notificaciones

### Telegram
1. Crea un bot con @BotFather y copia el token en `bot_token`
2. Obtiene tu `chat_id` con @userinfobot
3. Pon `"enabled": true`

### Discord
1. Canal > Configuracion > Integraciones > Webhooks > crear webhook
2. Copia la URL en `webhook_url` y pon `"enabled": true`

## Proxy (opcional)

Para rotar IPs y reducir deteccion, en `config.json` -> `proxy`:
- Un solo proxy: llena `host`, `port`, opcionalmente `username`/`password`
- Varios proxies: pon la ruta en `list_file` (un proxy por linea) y `rotate: true`

## Advertencia

Este bot va en contra de los Terminos de Servicio de Amazon Flex.
Usarlo puede resultar en la desactivacion de tu cuenta. Usalo bajo tu propio riesgo.
