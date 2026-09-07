# -*- coding: utf-8 -*-
"""
articulos.py — carga y parseo de los artículos Markdown.

No hay base de datos: los artículos son archivos en el repositorio. Se leen y
se convierten a HTML UNA sola vez, al arrancar, y quedan en memoria. Publicar
es escribir un .md y hacer push.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import frontmatter
import markdown

log = logging.getLogger("blog.articulos")

DIR_ARTICULOS = Path(__file__).resolve().parent.parent / "articulos"

# Las seis categorías del blog. Fijas, en el código: no hay panel de admin.
CATEGORIAS: tuple[str, ...] = (
    "Contabilidad",
    "Tributación",
    "Gestión Empresarial",
    "Tecnología",
    "Inteligencia Artificial",
    "Sector Público",
)

PALABRAS_POR_MINUTO = 200

EXTENSIONES_MD = ["tables", "fenced_code", "attr_list", "toc", "footnotes"]


def slugificar(texto: str) -> str:
    """'Inteligencia Artificial' -> 'inteligencia-artificial'. Sin tildes ni ñ."""
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base


# Mapa slug -> nombre canónico, para resolver /categoria/{slug}.
SLUG_CATEGORIA: dict[str, str] = {slugificar(c): c for c in CATEGORIAS}

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "setiembre", "octubre", "noviembre", "diciembre")


def fecha_larga(f: date | None) -> str:
    return f"{f.day} de {MESES[f.month - 1]} de {f.year}" if f else ""


@dataclass(slots=True)
class Articulo:
    slug: str
    titulo: str
    resumen: str
    fecha: date
    actualizado: date | None
    autor: str
    categoria: str | None          # None si el frontmatter trae una fuera de la lista
    tags: list[str]
    imagen: str | None
    destacado: bool
    derivados: list[str]           # solo se parsea y se guarda; no se muestra (aún)
    cuerpo_html: str
    tiempo_lectura: int            # minutos
    palabras: int
    tiene_tablas: bool = False
    _fecha_iso: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self._fecha_iso = self.fecha.isoformat()

    @property
    def categoria_slug(self) -> str:
        return slugificar(self.categoria) if self.categoria else ""

    @property
    def fecha_iso(self) -> str:
        return self._fecha_iso

    @property
    def fecha_texto(self) -> str:
        return fecha_larga(self.fecha)

    @property
    def actualizado_texto(self) -> str:
        return fecha_larga(self.actualizado)

    @property
    def autor_cita(self) -> str:
        """'Duilio Restuccia Eslava' -> 'Restuccia Eslava, D.' (formato de cita)."""
        partes = self.autor.split()
        if len(partes) < 2:
            return self.autor
        return f"{' '.join(partes[1:])}, {partes[0][0]}."


def _a_fecha(valor, defecto: date | None = None) -> date | None:
    """Acepta date, datetime o 'AAAA-MM-DD'. Nunca revienta: cae al defecto."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        try:
            return date.fromisoformat(valor.strip()[:10])
        except ValueError:
            pass
    return defecto


def _a_lista(valor) -> list[str]:
    if isinstance(valor, (list, tuple)):
        return [str(v).strip() for v in valor if str(v).strip()]
    if isinstance(valor, str) and valor.strip():
        return [t.strip() for t in valor.split(",") if t.strip()]
    return []


def _parsear(ruta: Path) -> Articulo | None:
    """Convierte un .md en Articulo. Un archivo malo se registra y se salta:
    un typo en un frontmatter no puede tumbar el sitio."""
    try:
        doc = frontmatter.load(ruta, encoding="utf-8")
    except Exception as e:  # YAML inválido, encoding raro, etc.
        log.error("No se pudo leer %s: %s", ruta.name, e)
        return None

    meta = doc.metadata or {}
    titulo = str(meta.get("titulo", "")).strip()
    if not titulo:
        log.error("%s: sin 'titulo' en el frontmatter. Se omite.", ruta.name)
        return None

    fecha = _a_fecha(meta.get("fecha"))
    if fecha is None:
        log.error("%s: 'fecha' ausente o inválida. Se omite.", ruta.name)
        return None

    categoria = str(meta.get("categoria", "")).strip()
    if categoria and categoria not in CATEGORIAS:
        log.warning("%s: categoría desconocida %r. Se trata como sin categoría.",
                    ruta.name, categoria)
        categoria = ""

    md = markdown.Markdown(extensions=EXTENSIONES_MD, output_format="html")
    cuerpo_html = md.convert(doc.content)

    palabras = len(re.findall(r"\S+", doc.content))
    minutos = max(1, round(palabras / PALABRAS_POR_MINUTO))

    imagen = str(meta.get("imagen", "")).strip() or None

    return Articulo(
        slug=ruta.stem.lower(),
        titulo=titulo,
        resumen=str(meta.get("resumen", "")).strip(),
        fecha=fecha,
        actualizado=_a_fecha(meta.get("actualizado")),
        autor=str(meta.get("autor", "")).strip() or "Perú Sistemas PRO",
        categoria=categoria or None,
        tags=_a_lista(meta.get("tags")),
        imagen=imagen,
        destacado=bool(meta.get("destacado", False)),
        derivados=_a_lista(meta.get("derivados")),
        cuerpo_html=cuerpo_html,
        tiempo_lectura=minutos,
        palabras=palabras,
        tiene_tablas="<table>" in cuerpo_html,
    )


class Catalogo:
    """Todos los artículos en memoria. Se llena una vez, al arrancar."""

    def __init__(self) -> None:
        self.articulos: list[Articulo] = []
        self.por_slug: dict[str, Articulo] = {}

    def cargar(self) -> None:
        encontrados: list[Articulo] = []
        if not DIR_ARTICULOS.is_dir():
            log.warning("No existe la carpeta %s. Blog sin artículos.", DIR_ARTICULOS)
        else:
            for ruta in sorted(DIR_ARTICULOS.glob("*.md")):
                art = _parsear(ruta)
                if art is None:
                    continue
                if art.slug in {a.slug for a in encontrados}:
                    log.error("Slug duplicado %r (%s). Se omite.", art.slug, ruta.name)
                    continue
                encontrados.append(art)

        # Orden de publicación: destacados arriba, luego por fecha descendente.
        encontrados.sort(key=lambda a: (not a.destacado, -a.fecha.toordinal(), a.titulo))
        self.articulos = encontrados
        self.por_slug = {a.slug: a for a in encontrados}
        log.info("Artículos cargados: %d", len(encontrados))

    # --- Consultas ---------------------------------------------------------
    @property
    def recientes(self) -> list[Articulo]:
        """Solo por fecha descendente, ignorando el destacado (para RSS)."""
        return sorted(self.articulos, key=lambda a: (-a.fecha.toordinal(), a.titulo))

    def de_categoria(self, categoria: str) -> list[Articulo]:
        return [a for a in self.articulos if a.categoria == categoria]

    def categorias_con_articulos(self) -> list[tuple[str, str, int]]:
        """(nombre, slug, cuántos) solo de las categorías que tienen artículos."""
        salida = []
        for c in CATEGORIAS:
            n = sum(1 for a in self.articulos if a.categoria == c)
            if n:
                salida.append((c, slugificar(c), n))
        return salida

    def ultima_modificacion(self) -> date:
        fechas = [a.actualizado or a.fecha for a in self.articulos]
        return max(fechas) if fechas else date.today()


catalogo = Catalogo()
