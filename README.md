# Blog — Perú Sistemas PRO

Blog mínimo en FastAPI + Jinja2. **Sin base de datos**: los artículos son
archivos Markdown en este repositorio. Publicar = escribir un `.md` y hacer
push; Railway despliega.

Producción: `https://blog.perusistemas.pro`

---

## Publicar un artículo nuevo

1. Crear `articulos/<slug>.md`. **El nombre del archivo es la URL**:
   `articulos/pcge-2026.md` se publica en `/pcge-2026`. Solo minúsculas,
   números y guiones.

2. Escribir el frontmatter:

```yaml
---
titulo: "Nuevo Plan Contable General Empresarial: qué cambia realmente"
resumen: "Una o dos frases. Se usa en el índice, en el Open Graph y en el botón de copiar resumen."
fecha: 2026-08-28
actualizado: 2026-08-28
autor: "Duilio Restuccia Eslava"
categoria: "Contabilidad"
tags: ["PCGE", "normativa contable"]
imagen: "/static/og/pcge.jpg"
destacado: true
derivados:
  - "LinkedIn: post del 30/08"
  - "Video corto: 90 segundos"
---
```

| Campo         | Obligatorio | Nota |
|---------------|-------------|------|
| `titulo`      | sí          | Sin él, el artículo no se publica |
| `resumen`     | recomendado | Índice, Open Graph y botón "Copiar resumen" |
| `fecha`       | sí          | `AAAA-MM-DD`. Sin ella, el artículo no se publica |
| `actualizado` | no          | Si difiere de `fecha`, se muestra en el artículo |
| `autor`       | no          | Por defecto: Perú Sistemas PRO |
| `categoria`   | no          | Una de las seis (abajo). Si no coincide, se publica sin categoría y queda un aviso en el log |
| `tags`        | no          | Lista |
| `imagen`      | no          | 1200×630. Sin ella se usa `/static/og/por-defecto.png` |
| `destacado`   | no          | `true` lo pone arriba del índice |
| `derivados`   | no          | Solo registro interno. **No se muestra en el sitio** |

3. Escribir el cuerpo en Markdown puro. Están activas las extensiones
   `tables`, `fenced_code`, `attr_list`, `toc` y `footnotes`.

4. `git add . && git commit && git push`. Railway despliega solo.

El **tiempo de lectura** no se escribe: se calcula del número de palabras
(200 por minuto).

### Las seis categorías

```
Contabilidad · Tributación · Gestión Empresarial ·
Tecnología · Inteligencia Artificial · Sector Público
```

Están fijas en `app/articulos.py` (`CATEGORIAS`). En el índice solo aparecen
las que tienen al menos un artículo.

### Tablas

Cualquier tabla de Markdown se vuelve interactiva sola, sin sintaxis especial:
orden por columna (detecta números, fechas y texto), filtro cuando pasa de 8
filas, scroll horizontal con primera columna fija en móvil y botón para copiar
en TSV (se pega en Excel en celdas separadas).

---

## Desarrollo local

```bash
cd blog
python -m venv .venv
.venv\Scripts\activate          # Windows.  Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

En `http://localhost:8000`. Los artículos se leen **al arrancar**: si editas un
`.md`, reinicia el servidor (`--reload` lo hace solo al tocar código Python).

---

## Despliegue en Railway

1. Servicio nuevo en Railway apuntando a este repositorio (root: `blog/`).
   Railway detecta `Procfile`, `requirements.txt` y `.python-version`.

2. Variable de entorno — **una sola**:

   ```
   SITIO_URL = https://blog.perusistemas.pro
   ```

   Sin barra final. De ella salen todas las URLs absolutas del Open Graph, el
   RSS, el sitemap y los enlaces internos.

3. Dominio: en Railway, *Settings → Networking → Custom Domain* →
   `blog.perusistemas.pro`. Railway entrega un destino `*.up.railway.app`.

4. En Cloudflare, CNAME `blog` → ese destino, **en gris (DNS only)**. Esperar a
   que Railway emita el certificado; recién entonces activar el proxy (naranja).
   Si se activa el proxy antes, el certificado no se emite.

5. Verificar: `https://blog.perusistemas.pro/salud` debe responder
   `{"estado":"ok", ...}`.

### Migrar a `perusistemas.pro/blog` (a futuro)

Ninguna plantilla tiene URLs escritas a mano: todo pasa por `SITIO_URL`. Migrar
es cambiar esa variable y poner redirecciones 301 desde el subdominio —Google
traslada la autoridad—.

---

## Rutas

| Ruta                     | Qué es |
|--------------------------|--------|
| `/`                      | Índice: destacados arriba, luego por fecha descendente |
| `/{slug}`                | El artículo |
| `/categoria/{slug}`      | Filtro por categoría (`/categoria/inteligencia-artificial`) |
| `/rss.xml`               | Feed RSS |
| `/sitemap.xml`           | Sitemap |
| `/robots.txt`            | Robots |
| `/salud`                 | Estado y cuántos artículos hay cargados |

---

## Open Graph

El destino principal es LinkedIn. **LinkedIn cachea la primera lectura**: si la
vista previa sale mal la primera vez, se queda pegada. Antes de compartir un
artículo nuevo, pasarlo por el
[Post Inspector de LinkedIn](https://www.linkedin.com/post-inspector/) para
forzar la primera lectura correcta.

Todas las etiquetas OG salen con URL absoluta a partir de `SITIO_URL`.

Nota: LinkedIn retiró de su API la posibilidad de comentar desde una web
externa. Este blog solo comparte; no hay ni habrá comentarios de LinkedIn.

---

## Estructura

```
blog/
├─ app/
│  ├─ main.py           Rutas, RSS, sitemap, robots, Open Graph
│  ├─ articulos.py      Carga y parseo de los .md al arrancar (en memoria)
│  ├─ static/
│  │  ├─ estilos.css
│  │  ├─ tablas.js      Ordenar / filtrar / copiar TSV
│  │  ├─ compartir.js   Compartir, copiar enlace y resumen, citar
│  │  └─ og/por-defecto.png
│  └─ templates/        base · indice · articulo · categoria
├─ articulos/           ← aquí van los .md
├─ Procfile
├─ requirements.txt
├─ .python-version
└─ README.md
```

## Lo que este blog NO tiene (a propósito)

Valoración con estrellas, captura de opiniones, comentarios, comparativas
descargables, panel de administración y buscador. Entran después, cuando haya
artículos que los justifiquen. La ventana de atención de un tema normativo dura
semanas: publicar hoy vale más que publicar completo.
