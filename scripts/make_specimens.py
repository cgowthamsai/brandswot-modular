#!/usr/bin/env python3
"""Render README / Google Fonts specimen images into documentation/."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TTF = ROOT / "fonts" / "ttf"
OUT = ROOT / "documentation"
INK, ORANGE, PAPER, GREY = "#0B0B0C", "#FF6A1F", "#F4F1EA", "#8A8780"


def f(style, size):
    return ImageFont.truetype(str(TTF / f"BRANDSWOTModular-{style}.ttf"), size)


def hero():
    W, H = 2400, 1200
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    d.text((120, 110), "BRANDSWOT", font=f("Black", 300), fill=PAPER)
    d.text((120, 430), "MODULAR", font=f("Black", 300), fill=ORANGE)
    d.text((126, 800), "We don't just brand. We build.", font=f("Regular", 76), fill=PAPER)
    d.text((126, 1010), "Pixel display type in brickwork  ·  Light 300 – Black 900  ·  Roman + Italic  ·  OFL",
           font=f("Bold", 34), fill=GREY)
    im.save(OUT / "specimen-1.png")


def weights():
    W, H = 2400, 1500
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    styles = ["Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"]
    y = 90
    for s in styles:
        d.text((120, y + 40), s.upper(), font=f("Bold", 30), fill=GREY)
        d.text((560, y), "Hyderabad 500081", font=f(s, 120), fill=INK)
        y += 190
    im.save(OUT / "specimen-2.png")


def italics():
    W, H = 2400, 1000
    im = Image.new("RGB", (W, H), ORANGE)
    d = ImageDraw.Draw(im)
    d.text((120, 120), "Built, not drawn.", font=f("BlackItalic", 170), fill=INK)
    d.text((120, 400), "Brick by brick, the brand", font=f("Italic", 120), fill=INK)
    d.text((120, 600), "stands on its own feet.", font=f("LightItalic", 120), fill=INK)
    d.text((124, 860), "ITALIC  ·  12° SLANT  ·  SAME BRICKWORK", font=f("Bold", 34), fill=INK)
    im.save(OUT / "specimen-3.png")


def charset():
    cmap = TTFont(TTF / "BRANDSWOTModular-Bold.ttf").getBestCmap()
    chars = [chr(c) for c in sorted(cmap) if c > 0x20 and c != 0xA0 and not 0x300 <= c < 0x370]
    W = 2400
    per = 36
    rows = (len(chars) + per - 1) // per
    H = 160 + rows * 110 + 80
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    d.text((120, 60), f"{len(chars)} CHARACTERS  ·  GOOGLE FONTS LATIN CORE", font=f("Bold", 34), fill=ORANGE)
    font = f("Bold", 72)
    for i, ch in enumerate(chars):
        r, c = divmod(i, per)
        d.text((120 + c * 60, 160 + r * 110), ch, font=font, fill=PAPER)
    im.save(OUT / "specimen-4.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    hero(); weights(); italics(); charset()
    print("specimens written")
