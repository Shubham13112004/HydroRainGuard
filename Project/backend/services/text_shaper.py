"""
Correct multi-script text rendering for ReportLab PDFs.

WHY THIS MODULE EXISTS
----------------------
ReportLab's built-in fonts (Helvetica, and even a plain embedded TTF)
do no complex-script shaping. Given the Marathi string "पाणी", a naive
renderer emits codepoints in logical order and lets the font's cmap
pick glyphs. Devanagari does not work that way:

  * the 'I' matra (U+093F ि) is stored *after* its consonant in
    logical order but must be *drawn to the left* of it (reordering);
  * clusters such as क्ष, ज्ञ, त्र require GSUB ligature substitution
    into a single conjunct glyph;
  * half-forms (हिन्दी), the reph (पुनर्भरण), and nukta forms all need
    context-sensitive substitution.

Without a shaping engine you get boxes, wrong matra placement and
missing conjuncts.

THE FIX
-------
Shape every string with HarfBuzz -- the same engine Chrome, Firefox,
Android and Inkscape use -- then draw the resulting glyph IDs as vector
outlines through fontTools' pen protocol onto the ReportLab canvas.
Output stays true vector: it scales, prints at any DPI, and is smaller
than rasterising the page.

Latin runs that need no shaping still go through drawString, so
ordinary text remains copyable and searchable in the PDF.

FONTS
-----
Noto Sans and Noto Sans Devanagari (SIL OFL 1.1) are bundled in
data/fonts/, so the server needs nothing installed. Characters that no
bundled font covers (arrows, maths symbols) are substituted -- see
_SUBSTITUTIONS -- rather than silently rendered as blanks.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from reportlab.pdfgen.pathobject import PDFPathObject
from reportlab.platypus import Flowable
from reportlab.lib.colors import Color

# Explicit export list: `import *` must not shadow reportlab's own
# TTFont with the identically named fontTools class.
__all__ = [
    "FONT_DIR", "LATIN_REGULAR", "LATIN_BOLD", "DEVA_REGULAR", "DEVA_BOLD",
    "LATIN_FONT", "LATIN_FONT_BOLD", "HAS_FONTS",
    "needs_shaping", "has_devanagari", "font_for", "shaping_font_path",
    "shape", "string_width", "draw_shaped", "draw_aligned", "draw_wrapped",
    "wrap_height", "register_fonts", "ascent_descent",
    "ShapedParagraph", "P",
]

FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "fonts"
)

LATIN_REGULAR = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")
LATIN_BOLD = os.path.join(FONT_DIR, "NotoSans-Bold.ttf")
DEVA_REGULAR = os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")
DEVA_BOLD = os.path.join(FONT_DIR, "NotoSansDevanagari-Bold.ttf")

# ReportLab font names registered by this module.
LATIN_FONT = "HRG-Sans"
LATIN_FONT_BOLD = "HRG-Sans-Bold"

# Script ranges that need HarfBuzz rather than plain drawString.
_COMPLEX_RANGES = (
    (0x0900, 0x097F),   # Devanagari
    (0x0980, 0x09FF),   # Bengali
    (0x0A00, 0x0A7F),   # Gurmukhi
    (0x0A80, 0x0AFF),   # Gujarati
    (0x0B00, 0x0B7F),   # Oriya
    (0x0B80, 0x0BFF),   # Tamil
    (0x0C00, 0x0C7F),   # Telugu
    (0x0C80, 0x0CFF),   # Kannada
    (0x0D00, 0x0D7F),   # Malayalam
    (0x0D80, 0x0DFF),   # Sinhala
    (0x0600, 0x06FF),   # Arabic
    (0x0750, 0x077F),   # Arabic Supplement
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
)

# Characters no bundled font covers. Noto Sans deliberately omits most
# arrows and maths operators; rather than emit a blank notdef box we
# swap in an ASCII equivalent. Keep entries single-ASCII-ish.
_SUBSTITUTIONS = {
    "\u2192": "->",     # → rightwards arrow
    "\u2190": "<-",     # ←
    "\u2194": "<->",    # ↔
    "\u21d2": "=>",     # ⇒
    "\u21d0": "<=",     # ⇐
    "\u21d4": "<=>",    # ⇔
    "\u2191": "^",      # ↑
    "\u2193": "v",      # ↓
    "\u2264": "<=",     # ≤
    "\u2265": ">=",     # ≥
    "\u2260": "!=",     # ≠
    "\u2248": "~",      # ≈
    "\u221a": "sqrt",   # √
    "\u2211": "sum",    # ∑
    "\u221e": "inf",    # ∞
    "\u03b1": "alpha",  # α
    "\u03b2": "beta",   # β
    "\u03b3": "gamma",  # γ
    "\u03b4": "delta",  # δ
    "\u03bc": "u",      # µ
    "\u03c0": "pi",     # π
    "\u03c3": "sigma",  # σ
    "\u2206": "d",      # ∆
    "\u25cf": "*",      # ●
    "\u25cb": "o",      # ○
    "\u2713": "ok",     # ✓
    "\u2717": "x",      # ✗
    "\u26a0": "!",      # ⚠
}


# ---------------------------------------------------------------- font loading

@dataclass
class _Face:
    tt: TTFont
    glyph_order: list
    upem: int
    glyph_set: object
    cmap: frozenset


@lru_cache(maxsize=8)
def _load_face(path: str) -> _Face:
    tt = TTFont(path, fontNumber=0, lazy=False)
    cps: set[int] = set()
    for table in tt["cmap"].tables:
        cps |= set(table.cmap.keys())
    return _Face(
        tt=tt,
        glyph_order=tt.getGlyphOrder(),
        upem=tt["head"].unitsPerEm,
        glyph_set=tt.getGlyphSet(),
        cmap=frozenset(cps),
    )


@lru_cache(maxsize=8)
def _hb_font(path: str):
    with open(path, "rb") as fh:
        blob = hb.Blob(fh.read())
    font = hb.Font(hb.Face(blob))
    font.scale = (_load_face(path).upem, _load_face(path).upem)
    return font


def register_fonts() -> bool:
    """
    Register the bundled Noto Sans faces with ReportLab so ordinary
    Latin text uses them (and stays copyable/selectable). Returns
    False if the font files are missing, in which case callers fall
    back to Helvetica.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as RLTTFont

    ok = True
    for name, path in ((LATIN_FONT, LATIN_REGULAR), (LATIN_FONT_BOLD, LATIN_BOLD)):
        if name in pdfmetrics.getRegisteredFontNames():
            continue
        if os.path.exists(path):
            pdfmetrics.registerFont(RLTTFont(name, path))
        else:  # pragma: no cover - fonts ship with the repo
            ok = False
    if ok:
        from reportlab.lib.fonts import addMapping
        addMapping(LATIN_FONT, 0, 0, LATIN_FONT)
        addMapping(LATIN_FONT, 1, 0, LATIN_FONT_BOLD)
    return ok


HAS_FONTS = register_fonts()


def font_for(bold: bool) -> str:
    if not HAS_FONTS:
        return "Helvetica-Bold" if bold else "Helvetica"
    return LATIN_FONT_BOLD if bold else LATIN_FONT


def _font_chain(bold: bool) -> tuple[str, ...]:
    """Fonts tried in order for each character."""
    if not HAS_FONTS:
        return ()
    return (LATIN_BOLD, DEVA_BOLD) if bold else (LATIN_REGULAR, DEVA_REGULAR)


# ------------------------------------------------------------- script detection

def needs_shaping(text: str) -> bool:
    """True when the string contains characters HarfBuzz must lay out."""
    for ch in text:
        cp = ord(ch)
        if unicodedata.combining(ch):
            return True
        for lo, hi in _COMPLEX_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def has_devanagari(text: str) -> bool:
    return any(0x0900 <= ord(ch) <= 0x097F for ch in text)


def shaping_font_path(text: str, bold: bool) -> str:
    """Pick the font a whole string would be set in."""
    chain = _font_chain(bold)
    if not chain:
        return ""
    if has_devanagari(text):
        return chain[1]
    return chain[0]


def _prepare(text: str, bold: bool) -> str:
    """Swap characters no bundled font can draw for ASCII equivalents."""
    chain = _font_chain(bold)
    if not chain:
        return text
    covered = _load_face(chain[0]).cmap | _load_face(chain[1]).cmap
    if all(ord(ch) in covered for ch in text):
        return text
    return "".join(
        ch if ord(ch) in covered else _SUBSTITUTIONS.get(ch, "") for ch in text
    )


def _split_runs(text: str, bold: bool) -> list[tuple[str, str]]:
    """
    Split `text` into (segment, font_path) pairs so each character is
    set in the first bundled font that actually has it. This is what
    makes "पुणे (Pune) 20°C" work: Devanagari from the Devanagari face,
    the degree sign from the Latin face.
    """
    chain = _font_chain(bold)
    if not chain:
        return [(text, "")]
    if not text:
        return []

    runs: list[tuple[str, str]] = []
    cur: list[str] = []
    cur_font: str | None = None

    for ch in text:
        picked = chain[0]
        for path in chain:
            if ord(ch) in _load_face(path).cmap:
                picked = path
                break
        if picked != cur_font and cur:
            runs.append(("".join(cur), cur_font))
            cur = []
        cur.append(ch)
        cur_font = picked

    if cur:
        runs.append(("".join(cur), cur_font))
    return runs


# ------------------------------------------------------------------ shaping

@dataclass
class ShapedRun:
    text: str
    glyphs: list      # glyph names
    positions: list   # (x, y, advance) in font units; x is absolute
    font_path: str


@lru_cache(maxsize=8192)
def shape(text: str, font_path: str) -> ShapedRun:
    """Shape `text` with HarfBuzz. Cached; positions are in font units."""
    if not font_path:
        return ShapedRun(text, [], [], "")
    font = _hb_font(font_path)
    face = _load_face(font_path)

    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()

    # OpenType features HarfBuzz should apply. The Indic ones
    # (nukt/akhn/rphf/blwf/half/pstf/vatu/cjct/pres/abvs/blws/psts)
    # are what produce conjuncts, half-forms and the reph.
    features = {
        "kern": True, "liga": True, "clig": True, "rlig": True,
        "calt": True, "ccmp": True, "locl": True,
        "nukt": True, "akhn": True, "rphf": True, "blwf": True,
        "half": True, "pstf": True, "vatu": True, "cjct": True,
        "pres": True, "abvs": True, "blws": True, "psts": True,
        "haln": True, "init": True, "medi": True, "fina": True,
        "isol": True,
    }
    hb.shape(font, buf, features)

    glyphs, positions = [], []
    x = y = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gid = info.codepoint
        name = face.glyph_order[gid] if gid < len(face.glyph_order) else ".notdef"
        glyphs.append(name)
        positions.append((x + pos.x_offset, y + pos.y_offset, pos.x_advance))
        x += pos.x_advance
        y += pos.y_advance

    return ShapedRun(text=text, glyphs=glyphs, positions=positions,
                     font_path=font_path)


# ------------------------------------------------------------------ measuring

@lru_cache(maxsize=8)
def _metrics(font_path: str):
    face = _load_face(font_path)
    hhea = face.tt["hhea"]
    return hhea.ascent / face.upem, -hhea.descent / face.upem


def ascent_descent(text: str, size: float, bold: bool = False):
    """(ascent, descent) in points, both positive."""
    path = shaping_font_path(text or "x", bold)
    if not path:
        return size * 0.8, size * 0.2
    a, d = _metrics(path)
    return a * size, d * size


def string_width(text: str, size: float, bold: bool = False) -> float:
    """Advance width of `text` rendered at `size` points."""
    if not text:
        return 0.0
    text = _prepare(text, bold)

    if not _font_chain(bold):  # no bundled fonts: Helvetica fallback
        from reportlab.pdfbase import pdfmetrics
        return pdfmetrics.stringWidth(text, font_for(bold), size)

    total = 0.0
    for seg, path in _split_runs(text, bold):
        if not seg:
            continue
        if needs_shaping(seg):
            run = shape(seg, path)
            total += sum(p[2] for p in run.positions) * size / _load_face(path).upem
        else:
            from reportlab.pdfbase import pdfmetrics
            name = LATIN_FONT_BOLD if (bold and path == LATIN_BOLD) else LATIN_FONT
            total += pdfmetrics.stringWidth(seg, name, size)
    return total


# -------------------------------------------------------------------- drawing

class _PDFPathPen(BasePen):
    """
    fontTools pen that writes into a reportlab PDFPathObject.

    ReportLab's own ReportLabPen targets reportlab.graphics.shapes.Path,
    which canvas.drawPath() cannot consume; PDFPathObject can, and it
    is the object the canvas path operators build, so glyph outlines
    land in the content stream exactly like native text.
    """

    def __init__(self, glyph_set, path: PDFPathObject):
        super().__init__(glyph_set)
        self.path = path

    def _moveTo(self, p):
        self.path.moveTo(*p)

    def _lineTo(self, p):
        self.path.lineTo(*p)

    def _curveToOne(self, p1, p2, p3):
        self.path.curveTo(*p1, *p2, *p3)

    def _closePath(self):
        self.path.close()


def draw_shaped(
    canvas,
    x: float,
    y: float,
    text: str,
    size: float,
    bold: bool = False,
    color: Color | None = None,
) -> float:
    """
    Draw `text` with its baseline starting at (x, y).

    Latin runs go through drawString (copyable, searchable). Runs
    needing shaping are laid out by HarfBuzz and drawn as vector
    outlines. Returns the advance width in points.
    """
    if not text:
        return 0.0
    if color is not None:
        canvas.setFillColor(color)

    text = _prepare(text, bold)

    if not _font_chain(bold):
        canvas.setFont(font_for(bold), size)
        canvas.drawString(x, y, text)
        from reportlab.pdfbase import pdfmetrics
        return pdfmetrics.stringWidth(text, font_for(bold), size)

    cursor = x
    for seg, path in _split_runs(text, bold):
        if not seg:
            continue

        if not needs_shaping(seg):
            from reportlab.pdfbase import pdfmetrics
            name = LATIN_FONT_BOLD if (bold and path == LATIN_BOLD) else LATIN_FONT
            canvas.setFont(name, size)
            canvas.drawString(cursor, y, seg)
            cursor += pdfmetrics.stringWidth(seg, name, size)
            continue

        run = shape(seg, path)
        face = _load_face(path)
        scale = size / face.upem

        # One path for the whole run, each glyph placed by a transform,
        # then a single drawPath -- cheaper and tighter than per-glyph
        # fills.
        path_obj = PDFPathObject()
        base_pen = _PDFPathPen(face.glyph_set, path_obj)
        for gname, (gx, gy, adv) in zip(run.glyphs, run.positions):
            if gname != ".notdef":
                t = Transform(scale, 0, 0, scale,
                              cursor + gx * scale, y + gy * scale)
                face.glyph_set[gname].draw(TransformPen(base_pen, t))
        canvas.drawPath(path_obj, stroke=0, fill=1)

        cursor += sum(p[2] for p in run.positions) * scale

    return cursor - x


def draw_aligned(
    canvas,
    x: float,
    y: float,
    text: str,
    size: float,
    bold: bool = False,
    align: str = "left",     # left | center | right
    max_width: float | None = None,
    color: Color | None = None,
) -> float:
    """Draw one line with alignment. Returns the width used."""
    w = string_width(text, size, bold)
    if max_width:
        dx = (max_width - w) / 2.0 if align == "center" else (
            max_width - w if align == "right" else 0.0)
    else:
        dx = 0.0
    draw_shaped(canvas, x + dx, y, text, size, bold, color)
    return w


# ------------------------------------------------------------------- wrapping

def _wrap_point(text: str, size: float, bold: bool, max_width: float) -> list[str]:
    """
    Greedy word wrap that is safe for complex scripts: break on spaces
    only, never inside a combining sequence. Words longer than the line
    are hard-split at codepoint boundaries as a last resort.
    """
    if not text:
        return []
    out: list[str] = []
    for para in text.split("\n"):
        out.extend(_wrap_paragraph(para, size, bold, max_width))
    return out


def _wrap_paragraph(text: str, size: float, bold: bool,
                    max_width: float) -> list[str]:
    if not text:
        return [""]
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if string_width(trial, size, bold) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
        # hard-split a single word that still overflows
        while string_width(cur, size, bold) > max_width and len(cur) > 1:
            cut = len(cur)
            while cut > 1 and string_width(cur[:cut], size, bold) > max_width:
                cut -= 1
            while cut > 1 and unicodedata.combining(cur[cut]):
                cut -= 1
            lines.append(cur[:cut])
            cur = cur[cut:]
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(
    canvas,
    x: float,
    y: float,
    text: str,
    size: float,
    bold: bool = False,
    max_width: float = 200.0,
    leading: float | None = None,
    align: str = "left",
    color: Color | None = None,
) -> float:
    """Draw wrapped text with `y` as the TOP of the first line."""
    leading = leading or size * 1.35
    cy = y - size
    for line in _wrap_point(text, size, bold, max_width):
        draw_aligned(canvas, x, cy, line, size, bold, align, max_width, color)
        cy -= leading
    return cy + leading


def wrap_height(text: str, size: float, bold: bool, max_width: float,
                leading: float | None = None) -> float:
    leading = leading or size * 1.35
    return len(_wrap_point(text, size, bold, max_width)) * leading


# ------------------------------------------------------------------ flowable

class ShapedParagraph(Flowable):
    """
    A platypus Flowable that renders text through HarfBuzz.

    Drop-in replacement for reportlab.platypus.Paragraph wherever the
    string may contain Devanagari or another complex script. Keeps the
    same wrap/draw contract, so it also works as a table cell.
    """

    def __init__(
        self,
        text,
        size: float = 9,
        bold: bool = False,
        color: Color | None = None,
        align: str = "left",          # left | center | right
        leading: float | None = None,
        space_before: float = 0,
        space_after: float = 0,
        left_indent: float = 0,
    ):
        Flowable.__init__(self)
        self.text = "" if text is None else str(text)
        self.size = size
        self.bold = bold
        self.color = color or Color(0, 0, 0)
        self.align = align
        self.leading = leading if leading is not None else size * 1.35
        self.space_before = space_before
        self.space_after = space_after
        self.left_indent = left_indent
        self._lines: list[str] = []
        self.width = 0.0
        self.height = 0.0

    # -- measurement ---------------------------------------------------

    def _layout(self, avail_width: float) -> list[str]:
        return _wrap_point(self.text, self.size, self.bold,
                           max(avail_width - self.left_indent, 1.0))

    def _block_height(self, n: int) -> float:
        if n == 0:
            return self.space_before + self.space_after
        asc, desc = ascent_descent(self.text, self.size, self.bold)
        return (self.space_before + (n - 1) * self.leading
                + asc + desc + self.space_after)

    def wrap(self, availWidth, availHeight):
        self._lines = self._layout(availWidth)
        self.width = availWidth
        self.height = self._block_height(len(self._lines))
        return self.width, self.height

    def split(self, availWidth, availHeight):
        lines = self._layout(availWidth)
        if not lines:
            return []
        if self._block_height(len(lines)) <= availHeight:
            return [self]

        asc, desc = ascent_descent(self.text, self.size, self.bold)
        room = availHeight - self.space_before - asc - desc
        n = int(room // self.leading) + 1 if room >= 0 else 0
        n = max(0, min(n, len(lines) - 1))
        if n <= 0:
            return []

        def clone(txt, first):
            return ShapedParagraph(
                txt, size=self.size, bold=self.bold, color=self.color,
                align=self.align, leading=self.leading,
                space_before=self.space_before if first else 0,
                space_after=self.space_after if not first else 0,
                left_indent=self.left_indent,
            )
        return [clone("\n".join(lines[:n]), True),
                clone("\n".join(lines[n:]), False)]

    # -- drawing -------------------------------------------------------

    def draw(self):
        canv = self.canv
        if not self._lines:
            self._lines = self._layout(self.width or 100)
        asc, desc = ascent_descent(self.text, self.size, self.bold)
        extra = (self.leading - (asc + desc)) / 2.0
        y = self.height - self.space_before - extra - asc
        for line in self._lines:
            draw_aligned(
                canv, self.left_indent, y, line, self.size, self.bold,
                self.align, max(self.width - self.left_indent, 1.0), self.color,
            )
            y -= self.leading


def P(text, size=9, bold=False, color=None, align="left", leading=None,
      space_before=0, space_after=0, left_indent=0) -> ShapedParagraph:
    """Shorthand constructor used throughout the PDF report."""
    return ShapedParagraph(
        text, size=size, bold=bold, color=color, align=align, leading=leading,
        space_before=space_before, space_after=space_after,
        left_indent=left_indent,
    )
