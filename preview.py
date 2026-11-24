#!/usr/bin/env python3
"""Render each page of a PDF to a PNG so a sheet can be checked before printing.

Usage:
    python3 preview.py sheet.pdf          # sheet-p1.png, sheet-p2.png, ... (150 dpi)
    python3 preview.py sheet.pdf 300      # higher resolution
"""
import os
import sys

import pymupdf

if len(sys.argv) < 2:
    sys.exit(__doc__)
pdf = sys.argv[1]
dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 150
stem = os.path.splitext(pdf)[0]
doc = pymupdf.open(pdf)
for n, page in enumerate(doc, 1):
    out = f"{stem}-p{n}.png"
    page.get_pixmap(dpi=dpi).save(out)
    print("wrote", out)
print(f"{len(doc)} page(s)")
