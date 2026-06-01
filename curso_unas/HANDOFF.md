# 🎀 HANDOFF — Curso "El Arte de las Uñas" (Maison Lumière)

> **Para el Claude Code local (VS Code):** este archivo te explica TODO lo hecho hasta ahora y
> exactamente cómo terminar el PDF. El usuario ya generó 20 imágenes y las tiene en su PC.
> Tu trabajo es **incrustarlas en el curso y regenerar el PDF final**. Lee todo antes de actuar.

---

## 1. Objetivo del proyecto
Crear un **libro/curso profesional en PDF**, en español, ultra completo e ilustrado, sobre cómo
convertirse en experta en uñas desde cero hasta nivel avanzado en EE.UU. Estética: **academia
femenina premium** (tonos nude/blush + dorado, dark plum en portadas).

Regla del usuario: **no inventar datos**. Precios, salarios, licencias y tendencias están basados
en investigación real con fuentes citadas dentro del propio PDF.

## 2. Estado actual ✅
- `curso.html` → documento completo: portada, índice, **introducción + 14 módulos + precios EE.UU.
  + plan 30 días + FAQ + glosario + certificado**. **67 páginas** (con 7 fotos ya integradas).
- Ya tiene **9 ilustraciones vectoriales (SVG)** propias + **7 FOTOS REALES ya incrustadas**.
- `generate_images.py` → motor que **inserta fotos reales** bajo cada sección y reconstruye el PDF.
- `Maison-Lumiere-El-Arte-de-las-Unas.pdf` → PDF actual (con las 7 primeras fotos).
- `img/` → ya contiene 7 imágenes optimizadas (.jpg). **Faltan 13.**

### ✅ YA INTEGRADAS (7): intro_hero, tools_kit, drill_bits, uv_lamp, realce_products, russian_mani, acrylic_apex
### ⏳ FALTAN (13): polygel_form, gel_polish, art_french, art_chrome, art_cateye, art_aura, art_marble, art_floral, nail_shapes, pedicure_spa, workstation, social_flatlay, brand_identity

### Por qué no se terminó en la nube
La sesión en la nube **no podía recibir archivos de imagen** (las imágenes del chat no se guardan
en disco, y GitHub web rechazó las fotos de iCloud por pesadas). **En local esto se resuelve**
porque tú SÍ puedes leer las carpetas del usuario.

## 3. 🎯 TU TAREA (pasos)

### Paso 0 — Entorno
- Necesitas **Python 3** y **WeasyPrint**: `pip install weasyprint`
- ⚠️ **WeasyPrint en Windows** requiere las librerías **GTK3/Pango/Cairo**. Si `weasyprint` falla al
  importar, instala el runtime de GTK3 para Windows (paquete "gtk3-runtime") o ejecuta dentro de
  **WSL/Linux**. Alternativa: usar Playwright/Chromium para HTML→PDF si GTK da problemas.

### Paso 1 — Conseguir las imágenes del usuario
El usuario tiene las 20 imágenes en una carpeta local, p. ej.:
`C:\Users\lias9\Downloads\Fotos en iCloud\Fotos en iCloud`
(pídele la ruta exacta y confírmala).

### Paso 2 — Renombrar y copiar a `curso_unas/img/`
**Tú puedes VER las imágenes** (ábrelas con tu capacidad de visión) y emparejar cada una con su
**clave** según la tabla de abajo (por contenido visual y/o el orden 1→20 en que las generó).
Copia cada imagen a `curso_unas/img/` renombrada como `<clave>.<ext>` (acepta `png`, `jpg`, `webp`).

Ejemplo: la foto de manos con manicura nude → `curso_unas/img/intro_hero.jpg`

> 💡 Las fotos de iCloud pueden ser muy pesadas/HEIC. Conviértelas a JPG y redúcelas a ~1600 px de
> ancho antes de copiar (en el PDF se ven a tamaño medio; no necesitan más). Pillow sirve:
> `pip install pillow` y reescalar.

### Paso 3 — Integrar y construir el PDF
```bash
cd curso_unas
python generate_images.py --integrate-only
```
Esto inserta cada imagen bajo su encabezado (anclaje único) y regenera
`Maison-Lumiere-El-Arte-de-las-Unas.pdf`. Es **idempotente** (si ya estaba insertada, la salta).

### Paso 4 — Revisar y entregar
Abre el PDF, verifica que las 20 fotos quedaron bajo su sección correcta. Si alguna quedó mal
emparejada, corrige el nombre del archivo en `img/` y vuelve a correr el comando.

### Paso 5 — (Opcional) Guardar en GitHub
```bash
git add -A
git commit -m "Integra 20 imágenes reales al curso"
git push origin claude/etsy-store-audit-of437
```

## 4. 🗺️ Tabla: las 20 imágenes (orden · clave · qué muestra · sección)

| # | clave (nombre de archivo) | Qué muestra | Sección / Módulo |
|---|---|---|---|
| 1 | `intro_hero` | Manos con manicura nude elegante, spa de lujo | Introducción |
| 2 | `tools_kit` | Flat lay de herramientas (limas, buffer, pusher, nipper, pinzas, pinceles) | Mód. 1 |
| 3 | `drill_bits` | Set de puntas (bits) de torno en soporte | Mód. 1 |
| 4 | `uv_lamp` | Lámpara UV/LED moderna | Mód. 1 |
| 5 | `realce_products` | Polvo acrílico, monómero, gel, polygel/crema (productos) | Mód. 1 |
| 6 | `russian_mani` | Manicura rusa, cutícula con torno (guante) | Mód. 4 |
| 7 | `acrylic_apex` | Perfil lateral de uña esculpida (apex/curva) | Mód. 5 |
| 8 | `polygel_form` | Aplicación con dual form y pincel | Mód. 6 |
| 9 | `gel_polish` | Esmaltado en gel con pincel (color nude) | Mód. 7 |
| 10 | `art_french` | Varias manos con diseños elegantes (french/nude/leaf) | Mód. 8 (portada) |
| 11 | `art_chrome` | Uñas chrome espejo plateado | Mód. 8 |
| 12 | `art_cateye` | Cat eye azul profundo magnético | Mód. 8 |
| 13 | `art_aura` | Aura nails malva/rosa con centro luminoso | Mód. 8 |
| 14 | `art_marble` | Mármol blanco con vetas doradas | Mód. 8 |
| 15 | `art_floral` | Flores pintadas a mano sobre nude | Mód. 8 |
| 16 | `nail_shapes` | Comparativa de formas (cuadrada/ovalada/almendra/coffin/stiletto) | Mód. 9 |
| 17 | `pedicure_spa` | Pies en baño spa con flores y sales | Mód. 10 |
| 18 | `workstation` | Estación de trabajo con lámpara de aro (vista superior) | Mód. 2 |
| 19 | `social_flatlay` | Flat lay redes sociales con teléfono "nail.studio" | Mód. 13 |
| 20 | `brand_identity` | Mood board de marca "Luz Nails" | Mód. 11 |

> Nota: el orden 1→20 es el mismo en que el usuario las generó/envió, así que si las tienes
> ordenadas por fecha/nombre, el emparejamiento es directo. Aun así, **verifica visualmente**.

## 5. ⚙️ Cómo funciona `generate_images.py`
- `IMAGES` = dict `clave → (prompt, caption, clase_css)`. La `caption` se muestra bajo la foto.
- `ANCHORS` = dict `clave → encabezado HTML único` tras el cual se inserta la `<figure>`.
- `inject_into_html()` busca `curso_unas/img/<clave>.<ext>` y lo inserta tras su anchor (idempotente).
- `build_pdf()` ejecuta `weasyprint curso.html <pdf>`.
- Flags: `--integrate-only` (no llama a ninguna API, solo inserta y construye) ·
  `--force` (regenera vía OpenAI si tuvieras `OPENAI_API_KEY`; **no lo necesitas** para este flujo).
- Clase `half` (en `art_chrome/cateye/aura/marble/floral` y `drill_bits/uv_lamp`) → imagen a media página.

## 6. 🎨 Sistema de diseño (por si editas el HTML)
- Paleta CSS vars en `<style>`: `--blush`, `--rose`, `--rosegold`, `--gold`, `--plum`, `--mauve`…
- Fuentes Google: Playfair Display (display), Cormorant Garamond (itálicas), Poppins/Montserrat (texto).
- Componentes: `.box.tip/.pro/.warn/.note`, `.data` (dato con fuente), `ol.steps`, `ul.check`,
  `.badge.b-easy/b-mid/b-hard`, `.photo-real` (fotos), `.figbox` (SVG), `.divider` (portadillas de módulo).
- Página A4 con numeración y encabezado por módulo (CSS Paged Media de WeasyPrint).

## 7. 📚 Estructura del curso (índice)
Introducción · M1 Herramientas · M2 Higiene/Seguridad · M3 Anatomía · M4 Preparación (rusa) ·
M5 Acrílico · M6 Gel/Polygel · M7 Esmaltado · M8 Nail Art · M9 Formas · M10 Pedicura ·
M11 Negocio/Dinero · Precios EE.UU. · M12 Clientas difíciles · M13 Redes · M14 Secretos ·
Módulo final (plan 30 días + checklists) · FAQ · Glosario · Certificado.

## 8. ✅ Checklist rápido para terminar
- [ ] `pip install weasyprint pillow` (y GTK en Windows si hace falta)
- [ ] Pedir al usuario la ruta de su carpeta de imágenes
- [ ] Ver cada imagen, emparejar con su clave (tabla §4)
- [ ] Copiar a `curso_unas/img/<clave>.jpg` (convertir/reducir si pesan mucho)
- [ ] `python generate_images.py --integrate-only`
- [ ] Abrir el PDF y verificar las 20 fotos
- [ ] (Opcional) commit + push

---
*Generado como traspaso de la sesión en la nube. El motor y el HTML ya están listos; solo faltan
las imágenes en `curso_unas/img/` con el nombre correcto.*
