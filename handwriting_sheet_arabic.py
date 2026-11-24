#!/usr/bin/env python3
"""Arabic handwriting practice sheet generator (US Letter PDF).

Right-to-left adaptation of handwriting_sheet.py. Same page, guide lines,
colors and row pitch; the differences are:
  * rows run right to left: dark model at the right margin, gray tracing
    copies to its left, and the LEFT third of the row kept blank;
  * one Naskh font instead of print/cursive, sized so alif reaches the top
    line; the dashed midline sits at the measured height of the small round
    letters (the head of waw), since Arabic has no x-height;
  * no upper/lower-case "pair" rows; every row is a list of items.

Setup (once per environment):
    npm install                        # fonts, from package.json
    pip install -r requirements.txt

Usage:
    python3 handwriting_sheet_arabic.py                # built-in starter sheet
    python3 handwriting_sheet_arabic.py spec.json out.pdf

SPEC shape:
    {"title": "...",
     "sections": [                         # two per page (top / bottom half)
        {"heading": "Letters on their own",
         "scale": 0.75,                    # optional: lines 75% as tall
         "rows": [                         # up to 7 rows per section (9 at 0.75)
            {"items": ["ب"], "traces": 3}, # each item dark, then gray copies
            {"items": ["بَاب", "نَار"]}      #   ("traces" defaults to 1)
         ]}]}

Text is shaped with HarfBuzz and drawn as glyph outlines, so letters join and
vowel marks sit where the font puts them. Don't replace that with a plain
drawString call: it would give disconnected, left-to-right letters.
"""
import glob
import io
import json
import os
import sys

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------- content ---
SPEC = {
    "title": "Arabic Handwriting Practice",
    "sections": [
        {"heading": "Arabic letters on their own", "rows": [
            {"items": ["ا"], "traces": 3},
            {"items": ["ب"], "traces": 3},
            {"items": ["ت"], "traces": 3},
            {"items": ["ن"], "traces": 3},
            {"items": ["ل"], "traces": 3},
            {"items": ["م"], "traces": 3},
            {"items": ["ر"], "traces": 3},
        ]},
        {"heading": "Joined letters and words", "rows": [
            {"items": ["ببب", "ننن"]},
            {"items": ["للل", "ممم", "لا"]},
            {"items": ["بَاب", "نَار"], "traces": 2},
            {"items": ["مَال", "رَبّ"]},
            {"items": ["لَبَن", "نَمْل"]},
            {"items": ["تَمْر", "تُرَاب"]},
            {"items": ["بِنْت", "اِبْن"]},
        ]},
    ],
}

# ----------------------------------------------------------------- layout ---
PAGE_W, PAGE_H = letter
MARGIN = 40          # left/right margin, pt
CAP = 24             # baseline -> top guide line (alif height), pt
ROW_PITCH = 47       # distance between rows, pt
ROWS_PER_SECTION = 7
BLANK_FRACTION = 1 / 3   # left-hand share of each row kept empty
GAP_MODEL = 24       # space between a dark model and its first gray copy
GAP_TRACE = 18       # space after each gray copy

INK = (0.13, 0.15, 0.20)
TRACE = (0.66, 0.68, 0.73)
BLUE = (0.35, 0.55, 0.80)
RED = (0.85, 0.45, 0.45)
NOTE = ("Start at the right: look at the dark letters, trace the gray ones, "
        "then write your own.")

FONT_FILE = "scheherazade-new/files/scheherazade-new-arabic-400-normal.woff"
TALL = "ا"           # letter that defines the top line
SMALL = "و"          # letter whose head defines the dashed midline


# ------------------------------------------------------------------ fonts ---
def find_fontsource():
    """Locate node_modules/@fontsource near the script, cwd, or home."""
    here = os.path.dirname(os.path.abspath(__file__))
    probe = FONT_FILE.split("/")[0]
    for base in (os.environ.get("FONTSOURCE_DIR"), os.getcwd(), here,
                 os.path.expanduser("~"), os.path.expanduser("~/hw")):
        if not base:
            continue
        for cand in (base, os.path.join(base, "node_modules", "@fontsource")):
            if os.path.isdir(os.path.join(cand, probe)):
                return cand
    for hit in glob.glob(os.path.expanduser("~/**/node_modules/@fontsource"),
                         recursive=True):
        if os.path.isdir(os.path.join(hit, probe)):
            return hit
    sys.exit(f"Font not found. Run: npm i @fontsource/{probe}  "
             "(or set FONTSOURCE_DIR)")


def load_font():
    ft = TTFont(os.path.join(find_fontsource(), FONT_FILE))
    ft.flavor = None                           # woff -> plain ttf, in memory
    ttf = io.BytesIO()
    ft.save(ttf)
    hbfont = hb.Font(hb.Face(ttf.getvalue()))
    font = {"upm": ft["head"].unitsPerEm, "glyphs": ft.getGlyphSet(),
            "order": ft.getGlyphOrder(), "hb": hbfont}
    # measured from the shaped outlines; font metadata is unreliable here
    font["cap"] = ink_bounds(font, TALL)[3] / font["upm"]
    font["mid"] = ink_bounds(font, SMALL)[3] / font["upm"]
    return font


class CanvasPen(BasePen):
    """Draws a glyph outline into a reportlab path at (x, y) with scale k."""

    def __init__(self, glyphs, path, x, y, k):
        super().__init__(glyphs)
        self.p, self.x, self.y, self.k = path, x, y, k

    def _t(self, pt):
        return self.x + pt[0] * self.k, self.y + pt[1] * self.k

    def _moveTo(self, a):
        self.p.moveTo(*self._t(a))

    def _lineTo(self, a):
        self.p.lineTo(*self._t(a))

    def _curveToOne(self, a, b, c):
        self.p.curveTo(*self._t(a), *self._t(b), *self._t(c))

    def _closePath(self):
        self.p.close()


def shape(font, text):
    """Shape right-to-left Arabic; glyphs come back in visual (left-to-right) order."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = "rtl"
    buf.script = "Arab"
    buf.language = "ar"
    hb.shape(font["hb"], buf)
    return [(font["order"][i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def ink_bounds(font, text):
    """(xmin, ymin, xmax, ymax) of the shaped text in font units, pen at 0,0."""
    box, cx = None, 0
    for glyph, adv, xo, yo in shape(font, text):
        pen = BoundsPen(font["glyphs"])
        font["glyphs"][glyph].draw(pen)
        if pen.bounds:
            b = (pen.bounds[0] + cx + xo, pen.bounds[1] + yo,
                 pen.bounds[2] + cx + xo, pen.bounds[3] + yo)
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                         max(box[2], b[2]), max(box[3], b[3]))
        cx += adv
    return box


def text_width(font, text, size):
    return sum(g[1] for g in shape(font, text)) * size / font["upm"]


def draw_text_rtl(c, font, text, right, y, size, color):
    """Draw shaped text ending at x=right; returns the x of its left edge."""
    k = size / font["upm"]
    left = right - text_width(font, text, size)
    path = c.beginPath()
    cx = left
    for glyph, adv, xo, yo in shape(font, text):
        font["glyphs"][glyph].draw(
            CanvasPen(font["glyphs"], path, cx + xo * k, y + yo * k, k))
        cx += adv * k
    c.setFillColorRGB(*color)
    c.drawPath(path, stroke=0, fill=1, fillMode=1)   # non-zero: overlapping joins print solid
    return left


# ---------------------------------------------------------------- drawing ---
def draw_header(c):
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(*INK)
    c.drawString(MARGIN, PAGE_H - 30, "Name: ________________________________")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 30, "Date: ________________")


def draw_section(c, font, section, top):
    """Draw one half-page section starting at y=top; returns y below it."""
    s = section.get("scale", 1)             # 0.75 -> lines 75% as tall
    cap, pitch = CAP * s, ROW_PITCH * s
    max_rows = int(ROWS_PER_SECTION / s)
    size = cap / font["cap"]
    rows = section["rows"]
    if len(rows) > max_rows:
        sys.exit(f"'{section['heading']}' has {len(rows)} rows; max is "
                 f"{max_rows}. Split it into another section.")
    limit = MARGIN + (PAGE_W - 2 * MARGIN) * BLANK_FRACTION

    c.setFillColorRGB(*INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, top - 14, section["heading"])
    c.setFont("Helvetica", 8.5)
    c.setFillColorRGB(0.4, 0.4, 0.45)
    c.drawRightString(PAGE_W - MARGIN, top - 14, NOTE)

    for i, row in enumerate(rows):
        base = top - 26 - i * pitch - cap - 4
        c.setLineWidth(0.7)
        c.setDash()
        c.setStrokeColorRGB(*BLUE)
        c.line(MARGIN, base + cap, PAGE_W - MARGIN, base + cap)
        c.setStrokeColorRGB(*RED)
        c.line(MARGIN, base, PAGE_W - MARGIN, base)
        c.setStrokeColorRGB(*BLUE)
        c.setDash(4, 4)
        mid = base + font["mid"] * size
        c.line(MARGIN, mid, PAGE_W - MARGIN, mid)
        c.setDash()

        x = PAGE_W - MARGIN - 8                 # start at the right margin
        for item in row["items"]:
            x = draw_text_rtl(c, font, item, x, base, size, INK) - GAP_MODEL
            for _ in range(row.get("traces", 1)):
                x = draw_text_rtl(c, font, item, x, base, size, TRACE) - GAP_TRACE
        if x + GAP_TRACE < limit:
            print(f"warning: row {i + 1} of '{section['heading']}' leaves less "
                  f"than a third of the line blank; move an item to another row.")
    return top - 26 - ROWS_PER_SECTION * ROW_PITCH


def build(spec, out):
    font = load_font()
    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(spec.get("title", "Arabic Handwriting Practice"))
    sections = spec["sections"]
    for start in range(0, len(sections), 2):
        draw_header(c)
        y = PAGE_H - 44
        for n, section in enumerate(sections[start:start + 2]):
            if n:
                c.setStrokeColorRGB(0.6, 0.6, 0.65)
                c.setLineWidth(0.5)
                c.setDash(1, 3)
                c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
                c.setDash()
                y -= 12
            y = draw_section(c, font, section, y)
        c.showPage()
    c.save()
    print("wrote", out)


if __name__ == "__main__":
    spec = SPEC
    out = "arabic-handwriting-practice.pdf"
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as fh:
            spec = json.load(fh)
    if len(sys.argv) > 2:
        out = sys.argv[2]
    build(spec, out)
