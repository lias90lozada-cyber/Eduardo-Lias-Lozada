#!/usr/bin/env python3
"""
Generador e insertador de imágenes para el curso "El Arte de las Uñas".

REQUISITOS (en una sesión con red abierta):
  1. Variable de entorno OPENAI_API_KEY con una key válida de OpenAI.
  2. El host api.openai.com permitido en el allowlist de red del entorno.
  3. pip install nada extra: usa solo la librería estándar de Python.

USO:
  export OPENAI_API_KEY=sk-...        # o configúralo como secret del entorno
  python3 generate_images.py          # genera lo que falte e incrusta en curso.html
  python3 generate_images.py --force  # regenera todo aunque exista

Qué hace:
  - Genera cada imagen con gpt-image-1 (estilo unificado premium) en ./img/<key>.png
  - Es idempotente: si la imagen ya existe, NO la vuelve a generar (no recobra).
  - Reemplaza los marcadores <!--PHOTO:key--> de curso.html por <figure> con la imagen.
  - Regenera el PDF final con WeasyPrint.
"""

import os, sys, json, base64, time, urllib.request, urllib.error, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "img")
HTML = os.path.join(HERE, "curso.html")
PDF = os.path.join(HERE, "Maison-Lumiere-El-Arte-de-las-Unas.pdf")
API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"
SIZE = "1536x1024"      # horizontal, encaja con el ancho de página
QUALITY = "medium"      # low | medium | high  (medium = buen balance costo/calidad)

# Estilo común para coherencia visual de todo el libro
STYLE = ("estilo fotografía editorial de belleza premium, luz natural suave, "
         "tonos nude, blush y dorado, estética femenina elegante de academia de lujo, "
         "fondo limpio y minimalista, altísimo detalle, realista, "
         "sin texto, sin marcas de agua, sin letras")

# key -> (prompt, caption, clase_extra)
IMAGES = {
    "intro_hero":      ("manos femeninas con manicura nude brillante perfecta reposando con elegancia en un spa de lujo", "El mundo profesional de las uñas", ""),
    "tools_kit":       ("flat lay cenital de herramientas profesionales de manicura: limas, buffer, empujador de cutícula, alicate, pinzas y pinceles ordenados", "Herramientas básicas de la nail artist", ""),
    "drill_bits":      ("set de puntas (bits) de torno eléctrico para uñas de distintas formas, ordenadas, foto de producto macro", "Puntas de drill profesionales", "half"),
    "uv_lamp":         ("lámpara UV LED moderna para curar uñas, foto de producto limpia", "Lámpara UV/LED de curado", "half"),
    "realce_products": ("polvo acrílico en frasco, líquido monómero, pote de gel y tubo de polygel agrupados, foto de producto", "Sistemas de realce: acrílico, gel y polygel", ""),
    "russian_mani":    ("primer plano macro de una manicura rusa en proceso, zona de la cutícula limpia y pulcra", "Preparación y manicura rusa", ""),
    "acrylic_apex":    ("perfil lateral en primer plano de una uña esculpida en acrílico mostrando el apex y la estructura", "Estructura de acrílico: apex y curva C", ""),
    "polygel_form":    ("aplicación de polygel con dual form sobre una uña, primer plano detallado", "Construcción con polygel y dual form", ""),
    "gel_polish":      ("aplicación de esmalte en gel con pincel sobre uñas, primer plano pulcro y prolijo", "Esmaltado en gel de nivel salón", ""),
    "art_chrome":      ("manicura efecto chrome espejo plateado metálico, primer plano", "Diseño: Chrome / espejo", "half"),
    "art_cateye":      ("manicura cat eye magnética azul profundo con franja luminosa brillante, primer plano", "Diseño: Cat eye magnético", "half"),
    "art_aura":        ("uñas aura con centro luminoso difuminado en tonos malva y rosa, primer plano", "Diseño: Aura nails", "half"),
    "art_marble":      ("uñas con efecto mármol blanco y vetas doradas, primer plano elegante", "Diseño: Mármol", "half"),
    "art_french":      ("manicura french de color con puntas burdeos, primer plano moderno", "Diseño: French de color", "half"),
    "art_floral":      ("nail art floral pintado a mano sobre uñas nude, delicado, primer plano", "Diseño: Flores a mano", "half"),
    "nail_shapes":     ("varias manos mostrando distintas formas de uñas: cuadrada, ovalada, almendra, coffin y stiletto", "Las formas de uña y a quién favorecen", ""),
    "pedicure_spa":    ("pedicura spa de lujo, pies en un baño con flores y sales, tonos suaves y relajantes", "Pedicura estética y spa", ""),
    "workstation":     ("estación de trabajo de manicurista profesional impecable con lámpara de aro y herramientas, vista superior", "Estación de trabajo profesional", ""),
    "social_flatlay":  ("flat lay estético para redes sociales de un salón de uñas: teléfono mostrando contenido de uñas y accesorios bonitos", "Contenido para redes sociales", ""),
    "brand_identity":  ("mood board de marca de un salón de uñas femenino y elegante: muestras de color nude y dorado, logo abstracto, papelería", "Marca personal que enamora", ""),
}


def log(msg):
    print(f"[generate_images] {msg}", flush=True)


def generate_one(key, prompt, force=False):
    out = os.path.join(IMG_DIR, f"{key}.png")
    if os.path.exists(out) and not force:
        log(f"✓ ya existe, omito: {key}.png")
        return out
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log("ERROR: falta OPENAI_API_KEY en el entorno.")
        sys.exit(1)
    full_prompt = f"{prompt}. {STYLE}"
    body = json.dumps({
        "model": MODEL, "prompt": full_prompt,
        "size": SIZE, "quality": QUALITY, "n": 1,
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
            b64 = data["data"][0]["b64_json"]
            with open(out, "wb") as f:
                f.write(base64.b64decode(b64))
            log(f"★ generada: {key}.png")
            return out
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")
            log(f"HTTP {e.code} en {key} (intento {attempt}): {msg[:200]}")
            if e.code in (400, 401, 403):  # error de key/permiso/contenido: no reintentar
                raise
            time.sleep(2 ** attempt)
        except Exception as e:
            log(f"fallo en {key} (intento {attempt}): {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"No se pudo generar {key} tras varios intentos.")


# Encabezado (único) tras el cual se inserta cada imagen. Verificado: 1 coincidencia c/u.
ANCHORS = {
    "intro_hero":      '<h2 class="sec">El mundo de las uñas como profesión</h2>',
    "tools_kit":       '<h3>Herramientas básicas (con las que empiezas)</h3>',
    "drill_bits":      '<h3>El drill (torno eléctrico) y sus puntas (bits)</h3>',
    "uv_lamp":         '<h3>Lámparas UV vs. LED</h3>',
    "realce_products": '<h3>Sistemas de realce: acrílico, gel, polygel</h3>',
    "russian_mani":    '<h3>Manicura rusa (en seco, con drill): paso a paso</h3>',
    "acrylic_apex":    '<h3>Anatomía de una uña esculpida: apex y curva C</h3>',
    "polygel_form":    '<h3>Construcción con polygel y dual form (paso a paso)</h3>',
    "gel_polish":      '<h2 class="sec">Esmaltado en gel de nivel salón</h2>',
    "art_french":      '<h2 class="sec">Nail art: diseños que venden</h2>',
    "art_chrome":      '<h4>Chrome / espejo <span class="badge b-easy">Fácil</span></h4>',
    "art_cateye":      '<h4>Cat eye (magnético) <span class="badge b-easy">Fácil</span></h4>',
    "art_aura":        '<h4>Aura nails <span class="badge b-mid">Intermedio</span></h4>',
    "art_marble":      '<h4>Mármol <span class="badge b-mid">Intermedio</span></h4>',
    "art_floral":      '<h4>Flores a mano / one-stroke <span class="badge b-hard">Avanzado</span></h4>',
    "nail_shapes":     '<h2 class="sec">Las formas de uña y a quién favorecen</h2>',
    "pedicure_spa":    '<h3>Pedicura spa (paso a paso)</h3>',
    "workstation":     '<h3>Cómo organizar una mesa profesional</h3>',
    "social_flatlay":  '<h3>Ideas de contenido que funcionan</h3>',
    "brand_identity":  '<h3>Marca personal que enamora</h3>',
}


def _ext_for(key):
    """Acepta png/jpg/jpeg/webp; devuelve la ruta relativa existente o png por defecto."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        if os.path.exists(os.path.join(IMG_DIR, f"{key}.{ext}")):
            return f"img/{key}.{ext}"
    return None


def inject_into_html():
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    inserted = skipped = missing = 0
    for key, (_, caption, cls) in IMAGES.items():
        src = _ext_for(key)
        if not src:
            missing += 1
            continue
        if f'alt="{caption}"' in html or f'src="{src}"' in html:
            skipped += 1            # ya insertada (idempotente)
            continue
        anchor = ANCHORS.get(key)
        if not anchor or anchor not in html:
            log(f"  ! sin anclaje para {key}, omito")
            continue
        cls_attr = f"photo-real {cls}".strip()
        fig = (f'\n  <figure class="{cls_attr}">'
               f'<img src="{src}" alt="{caption}">'
               f'<figcaption>{caption}</figcaption></figure>')
        html = html.replace(anchor, anchor + fig, 1)
        inserted += 1
    with open(HTML, encoding="utf-8", mode="w") as f:
        f.write(html)
    log(f"imágenes insertadas: {inserted} | ya estaban: {skipped} | sin archivo: {missing}")


def build_pdf():
    log("generando PDF…")
    subprocess.run(["weasyprint", HTML, PDF], check=True)
    log(f"PDF listo: {PDF}")


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    # --integrate-only: NO llama a la API; solo inserta las imágenes que ya pusiste
    # en ./img/ (png/jpg/jpeg/webp con el nombre clave) y reconstruye el PDF.
    if "--integrate-only" in sys.argv:
        inject_into_html()
        build_pdf()
        log("✔ INTEGRADAS. Revisa el PDF.")
        return
    force = "--force" in sys.argv
    total = len(IMAGES)
    for i, (key, (prompt, _c, _cls)) in enumerate(IMAGES.items(), 1):
        log(f"[{i}/{total}] {key}")
        generate_one(key, prompt, force=force)
    inject_into_html()
    build_pdf()
    log("✔ TERMINADO. Revisa el PDF.")


if __name__ == "__main__":
    main()
