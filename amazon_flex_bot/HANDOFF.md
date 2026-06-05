# Amazon Flex Block Grabber Bot — Handoff

## Objetivo
Bot en Python que monitorea la API privada de Amazon Flex y acepta bloques
de entrega automaticamente segun filtros configurables.

---

## Estado actual

### Completado
- [x] Autenticacion con Amazon (login + refresh de tokens)
- [x] Guardado/carga de tokens en `tokens.json` (no hace login cada vez)
- [x] Llamadas a la API privada de Flex (obtener bloques, aceptar bloque)
- [x] Filtros: pago minimo, duracion, estaciones, rango horario
- [x] Loop de polling con intervalo aleatorio anti-deteccion
- [x] Limite de bloques aceptados por dia
- [x] Notificaciones Telegram y Discord
- [x] Logs a consola y archivo `flex_bot.log`
- [x] Manejo de senales (Ctrl+C para detener limpio)

### Pendiente / Mejoras sugeridas
- [ ] Soporte para 2FA/OTP (cuenta Amazon con verificacion en 2 pasos)
- [ ] Modo debug para ver respuestas raw de la API
- [ ] Script separado para descubrir service area IDs sin aceptar bloques
- [ ] Soporte de proxy / rotacion de IPs
- [ ] Interfaz de linea de comandos (argparse) con flags utiles
- [ ] Manejo de CAPTCHA si Amazon lo exige
- [ ] Retry con backoff exponencial en errores de red
- [ ] Estadisticas: bloques vistos, rechazados, aceptados por sesion

---

## Estructura de archivos

```
amazon_flex_bot/
├── main.py                  # Punto de entrada — ejecutar esto
├── config.json              # Toda la configuracion del usuario
├── requirements.txt         # Solo necesita: requests
├── HANDOFF.md               # Este archivo
├── tokens.json              # Generado al correr — NO subir a git
├── flex_bot.log             # Generado al correr — logs
└── flex_bot/
    ├── __init__.py          # Exporta las clases principales
    ├── auth.py              # Autenticacion Amazon (login, refresh)
    ├── api.py               # Wrapper de la API privada de Flex
    ├── grabber.py           # Loop principal del bot
    ├── filters.py           # Logica de filtrado de bloques
    └── notifications.py     # Telegram y Discord
```

---

## Como correr

```bash
cd amazon_flex_bot
pip install -r requirements.txt

# Editar config.json con credenciales y filtros
python main.py
```

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
    "max_duration_hours": 4,
    "min_duration_hours": 2,
    "accepted_stations": [],
    "blocked_stations": [],
    "start_time_from": "06:00",
    "start_time_to": "22:00"
  },
  "bot": {
    "poll_interval_seconds": 30,
    "retry_on_error_seconds": 60,
    "max_grabs_per_day": 2,
    "randomize_interval": true,
    "randomize_range_seconds": 10
  },
  "notifications": {
    "telegram": {
      "enabled": false,
      "bot_token": "",
      "chat_id": ""
    },
    "discord": {
      "enabled": false,
      "webhook_url": ""
    }
  }
}
```

### Tabla de parametros

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `region` | string | `NA` USA/Canada, `EU` Europa, `FE` Japon/Australia |
| `service_areas` | array | Dejar `[]` para detectar automatico |
| `min_pay` | float | Pago minimo en dolares para aceptar |
| `max_duration_hours` | float | Duracion maxima del bloque en horas |
| `min_duration_hours` | float | Duracion minima del bloque en horas |
| `accepted_stations` | array | Codigos de estacion aceptados, ej `["DLA5","LAX9"]`. Vacio = todas |
| `blocked_stations` | array | Estaciones a ignorar siempre |
| `start_time_from` | string | Hora minima de inicio del bloque, formato `HH:MM` |
| `start_time_to` | string | Hora maxima de inicio del bloque, formato `HH:MM` |
| `poll_interval_seconds` | int | Segundos entre cada consulta a la API |
| `max_grabs_per_day` | int | Maximo de bloques aceptados por dia (reset a medianoche) |
| `randomize_interval` | bool | Variar el intervalo para no tener patron fijo |
| `randomize_range_seconds` | int | +/- segundos de variacion aleatoria |

---

## API privada de Amazon Flex

Amazon Flex **no tiene API publica**. Este bot usa los endpoints que la app
oficial usa internamente (ingenieria inversa de la comunidad).

### Endpoints usados

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/auth/register` (api.amazon.com) | Login inicial |
| POST | `/auth/token` (api.amazon.com) | Refresh del access token |
| GET  | `{base_url}/ServiceAreas` | Obtener zonas de servicio |
| POST | `{base_url}/GetOffersForProvider` | Obtener bloques disponibles |
| POST | `{base_url}/AcceptOffer` | Aceptar un bloque |
| POST | `{base_url}/ForfeitOffer` | Abandonar un bloque |
| GET  | `{base_url}/Shifts` | Ver horario actual |

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

---

## Flujo de autenticacion

```
1. FlexAuth.login()
   POST api.amazon.com/auth/register
   Body: { email, password, device_info }
   Response: { access_token, refresh_token, expires_in }

2. Guardar tokens en tokens.json

3. Antes de cada peticion: verificar si el token sigue valido
   Si expira en menos de 60s → FlexAuth.refresh_access_token()
   POST api.amazon.com/auth/token
   Body: { refresh_token }
   Response: { access_token, expires_in }

4. Si el refresh falla → volver a hacer login completo
```

---

## Flujo del bot (grabber.py)

```
BlockGrabber.start()
  loop:
    1. Reset contador si es dia nuevo
    2. Si ya se alcanzo max_grabs_per_day → esperar 1h y continuar
    3. FlexAPI.get_offers(service_areas)
    4. Para cada oferta:
       a. Si ya se vio antes → skip
       b. BlockFilter.passes(offer) → si no pasa → log y skip
       c. FlexAPI.accept_offer(offer_id)
       d. Si exito → notificar, incrementar contador
    5. Dormir poll_interval +/- random_range segundos
    6. Volver a 1
```

---

## Problemas comunes

### "No se pudo iniciar sesion"
- Verifica email y password en config.json
- Si tienes 2FA activado en tu cuenta Amazon, el bot no puede manejar OTP todavia
  → **Solucion pendiente:** agregar soporte OTP (ver seccion Pendiente)

### "No se encontraron service areas"
- Tu cuenta de Amazon Flex puede no estar activa en esa region
- Prueba cambiar `"region"` en config.json a `"NA"`, `"EU"` o `"FE"`

### "Sin bloques disponibles" siempre
- Los bloques son muy competidos y a veces no hay en horas valle
- Reduce `poll_interval_seconds` a 15-20 (con cuidado de no hacer ban)
- Verifica que los filtros no sean demasiado restrictivos (min_pay muy alto)

### Token expirado constantemente
- Reduce `poll_interval_seconds` para mantener la sesion activa
- El bot ya maneja refresh automatico, pero si Amazon revoca el refresh token
  se vuelve a hacer login completo

---

## Proxima tarea recomendada en VS Code

Agregar soporte para 2FA/OTP. En `flex_bot/auth.py`, metodo `login()`,
cuando Amazon responde con `{"response": {"error": {"code": "OTP_REQUIRED"}}}`,
pedir el codigo OTP al usuario por terminal e incluirlo en un segundo POST.

Ejemplo de flujo:
```python
# Si la respuesta de login contiene OTP_REQUIRED:
otp = input("Ingresa tu codigo de verificacion de Amazon: ").strip()
# Hacer segundo POST con el OTP incluido en auth_data
```

---

## Notas tecnicas adicionales

- `seen_offers` se limpia cada dia junto al contador diario para evitar
  que crezca indefinidamente en sesiones largas.
- El `device_id` se genera una sola vez y se guarda en `tokens.json`.
  Regenerarlo puede trigger verificacion de dispositivo nuevo en Amazon.
- Los tokens de Amazon Flex tienen vida corta (~1h). El refresh token
  puede durar semanas pero Amazon puede revocarlo si detecta actividad
  inusual.
- La API responde 401 cuando el access token expira y el bot lo maneja
  automaticamente en `FlexAPI._headers()` via `auth.get_valid_token()`.

---

## Advertencia

Este bot va en contra de los Terminos de Servicio de Amazon Flex.
Puede resultar en desactivacion de cuenta. Usar bajo propio riesgo.
