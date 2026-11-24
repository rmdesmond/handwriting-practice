#!/usr/bin/env python3
"""Handwriting practice sheet generator (US Letter PDF).

Setup (once per environment):
    npm install                        # fonts, from package.json
    pip install -r requirements.txt

Usage:
    python3 handwriting_sheet.py                 # builds the built-in vowel sheet
    python3 handwriting_sheet.py spec.json out.pdf

To make a different sheet, edit SPEC below (or pass a JSON file of the same
shape). Everything else (layout, guide lines, colors, fonts) stays fixed.

SPEC shape:
    {"title": "...",                       # PDF document title
     "sections": [                         # one or two per page (top / bottom half)
        {"font": "Print" | "Cursive",
         "heading": "Print vowels",
         "scale": 0.75,                    # optional: lines 75% as tall
         "rows": [                         # up to 7 rows per section (9 at 0.75)
            {"pair": "Aa"},                # letter row: dark "A a" + 3 gray copies
            {"items": ["ea", "ou"],        # word row: each item dark, then gray
             "traces": 1}                  #   copies ("traces" defaults to 1)
         ]}]}
More than two sections flow onto additional pages, two per page.

Cursive text is shaped with HarfBuzz and drawn as glyph outlines, so letters
inside a word really join. Don't replace that with a plain drawString call.
"""
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
    "title": "Vowel Handwriting Practice",
    "sections": [
        {"font": "Print", "heading": "Print vowels", "rows": [
            {"pair": "Aa"}, {"pair": "Ee"}, {"pair": "Ii"}, {"pair": "Oo"}, {"pair": "Uu"},
            {"items": ["aeiou", "AEIOU"]},
            {"items": ["ea", "ou", "ie", "oi"]},
        ]},
        {"font": "Cursive", "heading": "Cursive vowels", "rows": [
            {"pair": "Aa"}, {"pair": "Ee"}, {"pair": "Ii"}, {"pair": "Oo"}, {"pair": "Uu"},
            {"items": ["aeiou"], "traces": 2},
            {"items": ["ea", "ou", "ie", "oi"]},
        ]},
    ],
}

# ----------------------------------------------------------------- layout ---
PAGE_W, PAGE_H = letter
MARGIN = 40          # left/right margin, pt
CAP = 24             # baseline -> top guide line, pt
ROW_PITCH = 47       # distance between rows, pt
ROWS_PER_SECTION = 7
BLANK_FRACTION = 1 / 3   # right-hand share of each row kept empty

INK = (0.13, 0.15, 0.20)
TRACE = (0.66, 0.68, 0.73)
BLUE = (0.35, 0.55, 0.80)
RED = (0.85, 0.45, 0.45)
NOTE = "Look at the dark letters, trace the gray ones, then write your own."

FONT_FILES = {
    "Print": "edu-sa-beginner/files/edu-sa-beginner-latin-500-normal.woff",
    "Cursive": "playwrite-us-trad/files/playwrite-us-trad-latin-400-normal.woff",
}


# ------------------------------------------------------------------ fonts ---
def find_fontsource():
    """Locate node_modules/@fontsource: $FONTSOURCE_DIR, the cwd, or the script's folder."""
    here = os.path.dirname(os.path.abspath(__file__))
    probes = {rel.split("/")[0] for rel in FONT_FILES.values()}
    for base in (os.environ.get("FONTSOURCE_DIR"), os.getcwd(), here):
        if not base:
            continue
        for cand in (base, os.path.join(base, "node_modules", "@fontsource")):
            if all(os.path.isdir(os.path.join(cand, p)) for p in probes):
                return cand
    sys.exit("Fonts not found. Run: npm i @fontsource/edu-sa-beginner "
             "@fontsource/playwrite-us-trad  (or set FONTSOURCE_DIR)")


def load_fonts():
    root = find_fontsource()
    fonts = {}
    for name, rel in FONT_FILES.items():
        ft = TTFont(os.path.join(root, rel))
        ft.flavor = None                       # woff -> plain ttf, in memory
        ttf = io.BytesIO()
        ft.save(ttf)
        upm = ft["head"].unitsPerEm
        glyphs, cmap = ft.getGlyphSet(), ft.getBestCmap()

        def top(ch, glyphs=glyphs, cmap=cmap, upm=upm):
            pen = BoundsPen(glyphs)
            glyphs[cmap[ord(ch)]].draw(pen)
            return pen.bounds[3] / upm

        hbfont = hb.Font(hb.Face(ttf.getvalue()))
        fonts[name] = {
            "upm": upm, "glyphs": glyphs, "order": ft.getGlyphOrder(), "hb": hbfont,
            # measured from real outlines; font metadata is unreliable here
            "cap": max(top(c) for c in "EIU"),
            "xh": top("u"),
        }
    return fonts


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
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font["hb"], buf)
    return [(font["order"][i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def text_width(font, text, size):
    return sum(g[1] for g in shape(font, text)) * size / font["upm"]


def draw_text(c, font, text, x, y, size, color):
    """Draw shaped text as filled outlines; returns the x where it ends."""
    k = size / font["upm"]
    path = c.beginPath()
    cx = x
    for glyph, adv, xo, yo in shape(font, text):
        font["glyphs"][glyph].draw(CanvasPen(font["glyphs"], path, cx + xo * k, y + yo * k, k))
        cx += adv * k
    c.setFillColorRGB(*color)
    c.drawPath(path, stroke=0, fill=1, fillMode=1)   # non-zero: overlapping joins print solid
    return cx


# ---------------------------------------------------------------- drawing ---
def draw_header(c):
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(*INK)
    c.drawString(MARGIN, PAGE_H - 30, "Name: ________________________________")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 30, "Date: ________________")


def draw_section(c, fonts, section, top):
    """Draw one half-page section starting at y=top; returns y below it."""
    font = fonts[section["font"]]
    s = section.get("scale", 1)          # 0.75 -> lines 75% as tall
    cap, pitch = CAP * s, ROW_PITCH * s
    max_rows = int(ROWS_PER_SECTION / s)
    size = cap / font["cap"]
    rows = section["rows"]
    if len(rows) > max_rows:
        sys.exit(f"'{section['heading']}' has {len(rows)} rows; max is "
                 f"{max_rows}. Split it into another section.")
    limit = PAGE_W - MARGIN - (PAGE_W - 2 * MARGIN) * BLANK_FRACTION

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
        mid = base + font["xh"] * size
        c.line(MARGIN, mid, PAGE_W - MARGIN, mid)
        c.setDash()

        x, gap = MARGIN + 8, 0           # gap: blank space added after the last copy
        if "pair" in row:
            upper, lower = row["pair"][0], row["pair"][1:]
            slot = 54
            for k in range(1 + row.get("traces", 3)):
                color = INK if k == 0 else TRACE
                for ch, frac in ((upper, 0.27), (lower, 0.77)):
                    draw_text(c, font, ch, x + slot * frac - text_width(font, ch, size) / 2,
                              base, size, color)
                gap = 12 if k == 0 else 4
                x += slot + gap
        else:
            for item in row["items"]:
                x = draw_text(c, font, item, x, base, size, INK)
                gap = 22
                x += gap
                for _ in range(row.get("traces", 1)):
                    x = draw_text(c, font, item, x, base, size, TRACE)
                    gap = 16
                    x += gap
        if x - gap > limit:
            print(f"warning: row {i + 1} of '{section['heading']}' leaves less than "
                  f"a third of the line blank; move an item to another row.")
    return top - 26 - ROWS_PER_SECTION * ROW_PITCH


def build(spec, out):
    fonts = load_fonts()
    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(spec.get("title", "Handwriting Practice"))
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
            y = draw_section(c, fonts, section, y)
        c.showPage()
    c.save()
    print("wrote", out)


if __name__ == "__main__":
    spec = SPEC
    out = "handwriting-practice.pdf"
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as fh:
            spec = json.load(fh)
    if len(sys.argv) > 2:
        out = sys.argv[2]
    build(spec, out)
