# Amazon Flex Block Grabber Bot — Handoff

## Objetivo
Bot en Python que monitorea la API privada de Amazon Flex y acepta bloques
de entrega automaticamente segun filtros configurables.

> **Como continuar en VS Code:** clona el repo, abre la carpeta `amazon_flex_bot`
> y dile a Claude Code: *"Lee HANDOFF.md y continua con las tareas pendientes"*.

---

## Estado actual

### Completado
- [x] Autenticacion con Amazon (login + refresh de tokens)
- [x] **2FA / OTP interactivo** — pide el codigo por terminal si Amazon lo exige
- [x] Deteccion de CAPTCHA (avisa, no lo resuelve aun)
- [x] Guardado/carga de tokens en `tokens.json` (no hace login cada vez)
- [x] Llamadas a la API privada de Flex (bloques, aceptar, abandonar, horario)
- [x] **Reintentos con backoff exponencial** (2s, 4s, 8s, 16s) en red y rate limit
- [x] Filtros: pago minimo, **pago por hora**, duracion, estaciones, rango horario
- [x] Filtros: **dias de la semana**, **dias de anticipacion maximos**
- [x] Loop de polling con intervalo aleatorio anti-deteccion
- [x] Limite de bloques aceptados por dia
- [x] **Modo dry-run** (ver bloques sin aceptarlos)
- [x] **Modo debug** (ver request/response raw de la API)
- [x] **Estadisticas de sesion** (polls, vistos, matcheados, aceptados, fallidos)
- [x] **Soporte de proxy / rotacion de IPs** (config o archivo de lista)
- [x] **CLI con argparse** (--debug, --dry-run, --once, --discover-areas, --schedule)
- [x] Notificaciones Telegram y Discord
- [x] Logs a consola y archivo `flex_bot.log`
- [x] Manejo de senales (Ctrl+C para detener limpio + resumen)
- [x] `.gitignore` (excluye tokens.json, __pycache__, logs)

### Pendiente / Mejoras sugeridas
- [ ] **Validar endpoints reales contra la API actual de Amazon Flex.** Los
      nombres de endpoints y la forma del JSON estan basados en ingenieria
      inversa de la comunidad y PUEDEN haber cambiado. Usar `--debug` con una
      cuenta real para verificar y ajustar (ver seccion "Verificacion real").
- [ ] Soporte para resolver CAPTCHA (servicio externo tipo 2captcha)
- [ ] Aceptar varios bloques en paralelo (threading) para mas velocidad
- [ ] Modo "auto-forfeit": abandonar bloques de bajo pago si aparece uno mejor
- [ ] Dashboard web simple (Flask) para ver estado en vivo
- [ ] Tests unitarios con pytest (hay tests manuales, faltan automatizados)
- [ ] Dockerfile para correr en un servidor 24/7
- [ ] Persistir estadisticas historicas (SQLite) entre sesiones
- [ ] Soporte multi-cuenta

---

## Estructura de archivos

```
amazon_flex_bot/
├── main.py                  # Punto de entrada + CLI (argparse)
├── config.json              # Toda la configuracion del usuario
├── requirements.txt         # Solo necesita: requests
├── HANDOFF.md               # Este archivo
├── README.md                # Guia de uso para el usuario final
├── .gitignore               # Excluye tokens.json, __pycache__, *.log
├── tokens.json              # Generado al correr — NO subir a git
├── flex_bot.log             # Generado al correr — logs
└── flex_bot/
    ├── __init__.py          # Exporta las clases principales
    ├── auth.py              # Autenticacion Amazon (login, 2FA, refresh)
    ├── api.py               # Wrapper de la API privada de Flex + retries
    ├── grabber.py           # Loop principal del bot + dry-run + stats
    ├── filters.py           # Logica de filtrado de bloques
    ├── notifications.py     # Telegram y Discord
    ├── proxy.py             # Gestion y rotacion de proxies
    └── stats.py             # Estadisticas de la sesion
```

---

## Como correr

```bash
cd amazon_flex_bot
pip install -r requirements.txt

# Editar config.json con credenciales y filtros, luego:
python main.py                    # Iniciar el bot
python main.py --dry-run          # Ver bloques SIN aceptarlos (probar filtros)
python main.py --once             # Un solo ciclo de polling y salir
python main.py --debug            # Logs detallados (request/response API)
python main.py --discover-areas   # Listar tus service area IDs
python main.py --schedule         # Ver tus bloques ya agendados
python main.py --config otro.json # Usar otro archivo de config
```

Para detener: `Ctrl+C` (muestra resumen de la sesion al salir).

---

## Configuracion (config.json)

```json
{
  "credentials": {
    "email": "tu@email.com",
    "password": "tu_contraseña"
  },
  "region": "NA",
  "service_areas": [],
  "filters": {
    "min_pay": 18.00,
    "min_pay_per_hour": 0.0,
    "max_duration_hours": 4,
    "min_duration_hours": 2,
    "accepted_stations": [],
    "blocked_stations": [],
    "start_time_from": "06:00",
    "start_time_to": "22:00",
    "days_of_week": [],
    "max_start_days_ahead": null
  },
  "bot": {
    "poll_interval_seconds": 30,
    "retry_on_error_seconds": 60,
    "max_grabs_per_day": 2,
    "randomize_interval": true,
    "randomize_range_seconds": 10
  },
  "proxy": {
    "enabled": false,
    "type": "http",
    "host": "",
    "port": "",
    "username": "",
    "password": "",
    "rotate": false,
    "list_file": ""
  },
  "notifications": {
    "telegram": { "enabled": false, "bot_token": "", "chat_id": "" },
    "discord": { "enabled": false, "webhook_url": "" }
  }
}
```

### Tabla de parametros

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `region` | string | `NA` USA/Canada, `EU` Europa, `FE` Japon/Australia |
| `service_areas` | array | Dejar `[]` para detectar automatico. Usa `--discover-areas` para verlos |
| `min_pay` | float | Pago minimo total en dolares |
| `min_pay_per_hour` | float | Pago minimo POR HORA (0 = desactivado) |
| `max_duration_hours` | float | Duracion maxima del bloque |
| `min_duration_hours` | float | Duracion minima del bloque |
| `accepted_stations` | array | Codigos aceptados, ej `["DLA5","LAX9"]`. Vacio = todas |
| `blocked_stations` | array | Estaciones a ignorar siempre |
| `start_time_from` | string | Hora minima de inicio `HH:MM` |
| `start_time_to` | string | Hora maxima de inicio `HH:MM` |
| `days_of_week` | array | Dias permitidos: `["lun","mar"]` o `[0,1]`. Vacio = todos |
| `max_start_days_ahead` | int/null | Maximo de dias de anticipacion. `null` = sin limite |
| `poll_interval_seconds` | int | Segundos entre cada consulta |
| `max_grabs_per_day` | int | Maximo de bloques aceptados por dia (reset a medianoche) |
| `randomize_interval` | bool | Variar el intervalo (anti-deteccion) |
| `randomize_range_seconds` | int | +/- segundos de variacion |
| `proxy.enabled` | bool | Activar uso de proxy |
| `proxy.rotate` | bool | Elegir proxy aleatorio en cada peticion |
| `proxy.list_file` | string | Ruta a archivo .txt con un proxy por linea |

### Dias de la semana aceptados en `days_of_week`
Acepta nombres en espanol o ingles (abreviados o completos) o numeros 0-6:
`lun/lunes/mon/monday=0`, `mar/martes/tue=1`, `mie/miercoles/wed=2`,
`jue/jueves/thu=3`, `vie/viernes/fri=4`, `sab/sabado/sat=5`, `dom/domingo/sun=6`.

---

## Flags de linea de comandos (main.py)

| Flag | Que hace |
|------|----------|
| `--config RUTA` | Usar otro archivo de configuracion |
| `--debug` | Logs detallados: imprime request/response raw de la API |
| `--dry-run` | Evalua y muestra bloques que matchean pero NO los acepta |
| `--once` | Ejecuta un solo ciclo de polling y termina (con resumen) |
| `--discover-areas` | Lista tus service area IDs y termina |
| `--schedule` | Muestra tus bloques ya agendados y termina |

---

## API privada de Amazon Flex

Amazon Flex **no tiene API publica**. Este bot usa los endpoints que la app
oficial usa internamente (ingenieria inversa de la comunidad). **Estos
endpoints pueden cambiar** — ver seccion "Verificacion real" abajo.

### Endpoints usados

| Metodo | Endpoint | Funcion |
|--------|----------|---------|
| POST | `api.amazon.com/auth/register` | Login inicial (+ OTP) |
| POST | `api.amazon.com/auth/token` | Refresh del access token |
| GET  | `{base_url}/ServiceAreas` | Obtener zonas de servicio |
| POST | `{base_url}/GetOffersForProvider` | Obtener bloques disponibles |
| POST | `{base_url}/AcceptOffer` | Aceptar un bloque |
| POST | `{base_url}/ForfeitOffer` | Abandonar un bloque |
| GET  | `{base_url}/Shifts` | Ver horario actual |
| GET  | `{base_url}/Eligibility` | Ver elegibilidad |

### URLs base por region

| Region | URL |
|--------|-----|
| NA | `https://flex-capacity-na.amazon.com` |
| EU | `https://flex-capacity-eu.amazon.com` |
| FE | `https://flex-capacity-fe.amazon.com` |

### Headers importantes

```
Authorization: Bearer <access_token>
x-flex-Instance-Id: <device_id_unico>
x-amzn-RequestId: <uuid_por_peticion>
User-Agent: com.amazon.rabbit/1.0/iOS/16.0/iPhone
```

### Campos del JSON de un bloque (offer)
El codigo intenta leer varias variantes porque la forma exacta varia:
- **Pago**: `rateInfo.priceAmount.amount` → `pay.amount` → `totalPayment.amount`
- **Duracion**: calculada de `startTime`/`endTime`, o `durationMinutes`
- **Estacion**: `serviceArea.name` → `stationCode` → `station.name` → `serviceAreaName`
- **Inicio**: `startTime` (formato ISO 8601)
- **ID**: `offerId`

Si los endpoints cambian, ajustar los metodos `_extract_*` en `filters.py`.

---

## Flujo de autenticacion

```
1. Cargar tokens.json si existe
   - Token valido?       -> usar
   - Token expirado?     -> refresh_access_token()
   - Refresh fallido?    -> login_interactive()

2. login_interactive()
   POST api.amazon.com/auth/register  { email, password, device_info }
   - 200 OK              -> extraer access_token + refresh_token
   - OTP_REQUIRED        -> pedir codigo al usuario, reintentar con OTP
   - CAPTCHA_REQUIRED    -> abortar (no soportado aun)

3. Guardar tokens en tokens.json

4. Antes de cada peticion API:
   - get_valid_token() verifica expiracion (margen 60s)
   - Si expira -> refresh automatico
   - Si la API responde 401 -> refresh + reintentar
```

---

## Flujo del bot (grabber.py)

```
BlockGrabber.start()
  loop:
    1. Reset contador si es dia nuevo
    2. Si grabs_today >= max_grabs_per_day -> dormir 1h
    3. stats.polls++
    4. FlexAPI.get_offers(service_areas)
    5. Filtrar offers ya vistas (seen_offers)
    6. Para cada oferta nueva:
       a. BlockFilter.passes(offer) -> si no pasa -> log SKIP + stats
       b. Si dry_run -> solo log, NO aceptar
       c. FlexAPI.accept_offer(offer_id)
       d. Si exito -> notificar + grabs_today++ + stats
    7. Dormir poll_interval +/- random_range segundos
    8. Volver a 1
  Al detener (Ctrl+C): imprimir resumen de stats
```

---

## Verificacion real (IMPORTANTE para la proxima tarea)

El codigo es funcional y esta probado a nivel de logica (filtros, imports,
parsing de JSON), pero **los endpoints NO se han validado contra la API real
de Amazon** porque eso requiere una cuenta de Amazon Flex activa.

### Pasos para verificar con una cuenta real (en VS Code):

1. Llenar `config.json` con email y password reales.
2. Correr el login aislado:
   ```bash
   python main.py --discover-areas --debug
   ```
3. Observar en `flex_bot.log` o consola:
   - **Si el login da 200** -> los tokens funcionan, seguir al paso 4.
   - **Si pide OTP** -> el flujo interactivo deberia activarse solo.
   - **Si da error de endpoint (404/400)** -> el nombre del endpoint cambio.
     Buscar el nombre actual y actualizarlo en `api.py`.
4. Con `--debug`, comparar el JSON real de un bloque contra los campos que
   lee `filters.py` (`_extract_pay`, `_extract_duration`, etc.) y ajustar.
5. Probar `python main.py --dry-run --debug` para ver bloques sin aceptar.
6. Cuando los filtros se vean bien en dry-run, correr normal.

### Donde ajustar si algo no coincide:
- **Endpoint cambio** -> `flex_bot/api.py` (metodos `get_offers`, `accept_offer`...)
- **Forma del JSON de login cambio** -> `flex_bot/auth.py` (`_build_register_payload`, `_extract_tokens`)
- **Campos del bloque cambiaron** -> `flex_bot/filters.py` (metodos `_extract_*`)

---

## Problemas comunes

### "No se pudo iniciar sesion"
- Verifica email y password en config.json
- Si tienes 2FA, el bot pedira el codigo en terminal automaticamente
- Si aparece CAPTCHA: inicia sesion manualmente en la app de Amazon Flex
  primero, luego reintenta

### "No se encontraron service areas"
- Tu cuenta puede no estar activa en esa region
- Prueba cambiar `region` entre `NA`/`EU`/`FE`
- Corre `python main.py --discover-areas --debug` para ver el error exacto

### "Sin bloques disponibles" siempre
- Normal en horas valle; los bloques son muy competidos
- Verifica que los filtros no sean demasiado estrictos (`--dry-run` ayuda)
- Considera bajar `poll_interval_seconds` (con cuidado del ban)

### Endpoint devuelve 404 o 400
- El endpoint cambio. Activar `--debug`, ver la URL exacta y la respuesta,
  y actualizar el nombre en `api.py`. (ver "Verificacion real")

---

## Como probar sin cuenta real
Los filtros y el parsing se pueden probar con datos simulados:

```python
from flex_bot import BlockFilter
config = {"filters": {"min_pay": 20, "min_pay_per_hour": 8,
          "max_duration_hours": 4, "min_duration_hours": 2}}
f = BlockFilter(config)
offer = {
    "offerId": "abc123",
    "rateInfo": {"priceAmount": {"amount": "30.00"}},
    "startTime": "2026-06-06T10:00:00Z",
    "endTime":   "2026-06-06T13:00:00Z",
    "serviceArea": {"name": "DLA5"},
}
print(f.passes(offer))          # (True, 'OK')
print(f.describe_offer(offer))  # ID:abc123 | DLA5 | $30.00 ($10.00/h) | 3.0h | ...
```

---

## Notas tecnicas

- `seen_offers` se limpia cada dia junto al contador para no crecer infinito.
- El `device_id` se genera una vez y se guarda en `tokens.json`. Regenerarlo
  puede disparar verificacion de "dispositivo nuevo" en Amazon.
- Tokens de Flex viven ~1h; el refresh token dura mas pero Amazon puede
  revocarlo si detecta actividad inusual.
- El parsing de pago/duracion/estacion intenta MULTIPLES nombres de campo
  porque la forma del JSON varia entre regiones y versiones de la API.
- `requests` es la unica dependencia. No se uso selenium/navegador para
  mantenerlo ligero, pero si Amazon bloquea la API directa, migrar a un
  enfoque con navegador headless seria el plan B.

---

## Advertencia legal

Este bot va en contra de los Terminos de Servicio de Amazon Flex.
Puede resultar en desactivacion de cuenta. Usar bajo propio riesgo.
