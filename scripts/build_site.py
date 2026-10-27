#!/usr/bin/env python3
"""Fill the glyph list into the specimen and write docs/index.html (GitHub Pages)."""
import json
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
cmap = TTFont(ROOT / "fonts/ttf/BRANDSWOTModular-Bold.ttf").getBestCmap()
chars = "".join(chr(c) for c in sorted(cmap)
                if c > 0x20 and c != 0xA0 and not 0x300 <= c < 0x370 and c != 0x25CC)
body = (ROOT / "docs/specimen.body.html").read_text(encoding="utf-8")
body = body.replace('"__CHARS__"', json.dumps(chars))
(ROOT / "docs/specimen.html").write_text(body, encoding="utf-8")
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + body.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
        + "\n</body>\n</html>\n")
(ROOT / "docs/index.html").write_text(page, encoding="utf-8")
print("docs/index.html written,", len(chars), "glyphs")
