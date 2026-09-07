# -*- coding: utf-8 -*-
"""
main.py — blog.perusistemas.pro

FastAPI + Jinja2, sin base de datos. Los artículos se cargan al arrancar y
viven en memoria: no se toca disco en cada request.

Única variable de entorno: SITIO_URL. Todas las URLs internas se construyen a
partir de ella, nunca escritas a mano, para que migrar de dominio
(blog.perusistemas.pro -> perusistemas.pro/blog) no obligue a tocar plantillas.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .articulos import SLUG_CATEGORIA, catalogo

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("blog")

BASE_DIR = Path(__file__).resolve().parent

SITIO_URL = os.getenv("SITIO_URL", "http://localhost:8000").strip().rstrip("/")
SITIO_NOMBRE = "Perú Sistemas PRO"
SITIO_TITULO = "Blog · Perú Sistemas PRO"
SITIO_DESCRIPCION = (
    "Análisis de contabilidad, tributación, gestión empresarial, tecnología, "
    "inteligencia artificial y sector público."
)
OG_POR_DEFECTO = "/static/og/por-defecto.png"


def url(ruta: str = "/") -> str:
    """URL absoluta a partir de SITIO_URL. Único lugar donde se arma un enlace."""
    return f"{SITIO_URL}/{ruta.lstrip('/')}" if ruta.strip("/") else f"{SITIO_URL}/"


app = FastAPI(title="Blog — Perú Sistemas PRO", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals.update(url=url, SITIO_NOMBRE=SITIO_NOMBRE, SITIO_URL=SITIO_URL)


@app.on_event("startup")
def cargar_articulos() -> None:
    catalogo.cargar()


def _og_imagen(art) -> str:
    """Open Graph siempre absoluto. Sin imagen propia, la del sitio."""
    img = art.imagen if art and art.imagen else OG_POR_DEFECTO
    return img if img.startswith("http") else url(img)


def _ctx(request: Request, **extra) -> dict:
    base = {
        "request": request,
        "categorias": catalogo.categorias_con_articulos(),
        "og_imagen": url(OG_POR_DEFECTO),
        "og_tipo": "website",
        "og_titulo": SITIO_TITULO,
        "og_descripcion": SITIO_DESCRIPCION,
        "canonica": url("/"),
        "anio": datetime.now().year,
        "aviso": None,
    }
    base.update(extra)
    return base


# --- Rutas ------------------------------------------------------------------
@app.get("/salud")
def salud() -> JSONResponse:
    return JSONResponse({
        "estado": "ok",
        "articulos": len(catalogo.articulos),
        "sitio_url": SITIO_URL,
    })


@app.get("/", response_class=HTMLResponse)
def indice(request: Request):
    return templates.TemplateResponse("indice.html", _ctx(
        request,
        destacados=[a for a in catalogo.articulos if a.destacado],
        resto=[a for a in catalogo.articulos if not a.destacado],
        titulo_pagina=SITIO_TITULO,
    ))


@app.get("/rss.xml")
def rss() -> Response:
    items = []
    for a in catalogo.recientes[:30]:
        enlace = xml_escape(url("/" + a.slug))
        pub = datetime(a.fecha.year, a.fecha.month, a.fecha.day, 12, 0, tzinfo=timezone.utc)
        categoria = f"<category>{xml_escape(a.categoria)}</category>" if a.categoria else ""
        items.append(
            "<item>"
            f"<title>{xml_escape(a.titulo)}</title>"
            f"<link>{enlace}</link>"
            f'<guid isPermaLink="true">{enlace}</guid>'
            f"<description>{xml_escape(a.resumen)}</description>"
            f"<pubDate>{format_datetime(pub)}</pubDate>"
            f"{categoria}"
            "</item>"
        )
    ahora = format_datetime(datetime.now(timezone.utc))
    cabecera = '<?xml version="1.0" encoding="UTF-8"?>'
    xml = (
        f"{cabecera}\n"
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
        f"<title>{xml_escape(SITIO_TITULO)}</title>\n"
        f"<link>{xml_escape(url('/'))}</link>\n"
        f"<description>{xml_escape(SITIO_DESCRIPCION)}</description>\n"
        "<language>es-PE</language>\n"
        f"<lastBuildDate>{ahora}</lastBuildDate>\n"
        f"<atom:link href=\"{xml_escape(url('/rss.xml'))}\" rel=\"self\" "
        'type="application/rss+xml"/>\n'
        + "\n".join(items)
        + "\n</channel>\n</rss>\n"
    )
    return Response(xml, media_type="application/rss+xml; charset=utf-8")


@app.get("/sitemap.xml")
def sitemap() -> Response:
    urls = [
        f"<url><loc>{xml_escape(url('/'))}</loc>"
        f"<lastmod>{catalogo.ultima_modificacion().isoformat()}</lastmod>"
        "<changefreq>daily</changefreq><priority>1.0</priority></url>"
    ]
    for _, slug, _ in catalogo.categorias_con_articulos():
        urls.append(
            f"<url><loc>{xml_escape(url('/categoria/' + slug))}</loc>"
            "<changefreq>weekly</changefreq><priority>0.6</priority></url>"
        )
    for a in catalogo.recientes:
        lastmod = (a.actualizado or a.fecha).isoformat()
        urls.append(
            f"<url><loc>{xml_escape(url('/' + a.slug))}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            "<changefreq>monthly</changefreq><priority>0.8</priority></url>"
        )
    cabecera = '<?xml version="1.0" encoding="UTF-8"?>'
    xml = (f"{cabecera}\n"
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    return Response(xml, media_type="application/xml; charset=utf-8")


@app.get("/robots.txt")
def robots() -> Response:
    txt = f"User-agent: *\nAllow: /\n\nSitemap: {url('/sitemap.xml')}\n"
    return Response(txt, media_type="text/plain; charset=utf-8")


@app.get("/categoria/{categoria_slug}", response_class=HTMLResponse)
def por_categoria(request: Request, categoria_slug: str):
    nombre = SLUG_CATEGORIA.get(categoria_slug.lower())
    if not nombre:
        return _no_encontrado(request)
    titulo = f"{nombre} · {SITIO_NOMBRE}"
    return templates.TemplateResponse("categoria.html", _ctx(
        request,
        categoria_actual=nombre,
        categoria_actual_slug=categoria_slug.lower(),
        articulos=catalogo.de_categoria(nombre),
        titulo_pagina=titulo,
        og_titulo=titulo,
        og_descripcion=f"Artículos de {nombre} en el blog de {SITIO_NOMBRE}.",
        canonica=url(f"/categoria/{categoria_slug.lower()}"),
    ))


# Se declara AL FINAL: si fuera antes, capturaría /rss.xml, /salud, etc.
@app.get("/{slug}", response_class=HTMLResponse)
def articulo(request: Request, slug: str):
    art = catalogo.por_slug.get(slug.lower())
    if art is None:
        return _no_encontrado(request)
    return templates.TemplateResponse("articulo.html", _ctx(
        request,
        art=art,
        titulo_pagina=f"{art.titulo} · {SITIO_NOMBRE}",
        og_titulo=art.titulo,
        og_descripcion=art.resumen or SITIO_DESCRIPCION,
        og_imagen=_og_imagen(art),
        og_tipo="article",
        canonica=url(f"/{art.slug}"),
    ))


def _no_encontrado(request: Request) -> HTMLResponse:
    """404 útil: el índice completo en vez de una pared en blanco."""
    html = templates.get_template("indice.html").render(_ctx(
        request,
        destacados=[a for a in catalogo.articulos if a.destacado],
        resto=[a for a in catalogo.articulos if not a.destacado],
        titulo_pagina=f"No encontrado · {SITIO_NOMBRE}",
        aviso="Esa dirección no existe. Estos son los artículos publicados.",
    ))
    return HTMLResponse(html, status_code=404)
