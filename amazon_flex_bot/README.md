# Amazon Flex Block Grabber Bot

Bot en Python para agarrar bloques de Amazon Flex automaticamente.

## Instalacion

```bash
cd amazon_flex_bot
pip install -r requirements.txt
```

## Configuracion

Edita `config.json`:

```json
{
  "credentials": {
    "email": "tu@email.com",
    "password": "tu_contraseña"
  },
  "region": "NA",
  "service_areas": [],
  "filters": {
    "min_pay": 25.00,
    "max_duration_hours": 4,
    "min_duration_hours": 2,
    "accepted_stations": ["DLA5", "LAX9"],
    "blocked_stations": [],
    "start_time_from": "08:00",
    "start_time_to": "20:00"
  },
  "bot": {
    "poll_interval_seconds": 30,
    "max_grabs_per_day": 2,
    "randomize_interval": true,
    "randomize_range_seconds": 10
  },
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "TU_BOT_TOKEN",
      "chat_id": "TU_CHAT_ID"
    },
    "discord": {
      "enabled": false,
      "webhook_url": ""
    }
  }
}
```

### Parametros de configuracion

| Campo | Descripcion |
|-------|-------------|
| `region` | `NA` (Norte America), `EU` (Europa), `FE` (Lejano Oriente) |
| `service_areas` | Dejar vacio `[]` para detectar automaticamente |
| `min_pay` | Pago minimo en dolares para aceptar un bloque |
| `max_duration_hours` | Duracion maxima en horas |
| `min_duration_hours` | Duracion minima en horas |
| `accepted_stations` | Lista de codigos de estacion aceptados (vacio = todas) |
| `blocked_stations` | Lista de estaciones a ignorar |
| `start_time_from/to` | Rango de hora de inicio aceptable (formato 24h) |
| `poll_interval_seconds` | Cada cuantos segundos buscar bloques |
| `max_grabs_per_day` | Maximo de bloques a aceptar por dia |
| `randomize_interval` | Variar el intervalo para evitar patrones |

## Uso

```bash
python main.py
```

El bot guarda los tokens en `tokens.json` para no tener que iniciar sesion cada vez.
Los logs se guardan en `flex_bot.log`.

Para detener el bot: `Ctrl+C`

## Notificaciones

### Telegram
1. Crea un bot con @BotFather en Telegram
2. Copia el token en `bot_token`
3. Obtiene tu `chat_id` con @userinfobot
4. Pon `"enabled": true`

### Discord
1. En tu servidor Discord, ve a Configuracion del canal > Integraciones > Webhooks
2. Crea un webhook y copia la URL
3. Pon `"enabled": true`

## Advertencia

Este bot va en contra de los Terminos de Servicio de Amazon Flex.
Usarlo puede resultar en la desactivacion de tu cuenta.
Usalo bajo tu propio riesgo.
