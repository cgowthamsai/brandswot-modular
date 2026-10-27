#!/usr/bin/env python3
"""
BRANDSWOT Modular — source generator.

Reads BRANDSWOTModular.pixels and writes six UFO masters
(Light / Bold / Black × Roman / Italic) plus two designspace files
that `gftools builder config.yaml` (or fontmake) compiles into the
final variable and static fonts.

    python3 build_ufos.py

Designed by Gowtham Sai · BRANDSWOT Consultancy
SIL Open Font License 1.1
"""
import math
import re
import shutil
import unicodedata
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import (AxisDescriptor, DesignSpaceDocument,
                                      InstanceDescriptor, SourceDescriptor)
from glyphsLib import glyphdata

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- project ---
FAMILY = "BRANDSWOT Modular"
PS_FAMILY = "BRANDSWOTModular"
VERSION_MAJOR, VERSION_MINOR = 2, 100
REPO_URL = "https://github.com/cgowthamsai/brandswot-modular"
VENDOR_URL = "https://brandswotconsultancy.com"
DESIGNER = "Gowtham Sai"
MANUFACTURER = "BRANDSWOT Consultancy"
VENDOR_ID = "BSWT"
COPYRIGHT = f"Copyright 2026 The BRANDSWOT Modular Project Authors ({REPO_URL})"
TRADEMARK = "BRANDSWOT is a trademark of BRANDSWOT Consultancy."
DESCRIPTION = ("BRANDSWOT Modular is a pixel display typeface built from "
               "running-bond brickwork, designed by Gowtham Sai for "
               "BRANDSWOT Consultancy in Hyderabad, India.")
LICENSE = ("This Font Software is licensed under the SIL Open Font License, "
           "Version 1.1. This license is available with a FAQ at: "
           "https://openfontlicense.org")
LICENSE_URL = "https://openfontlicense.org"

# --------------------------------------------------------------- geometry ---
UPM = 1000
PX_W = 100            # pixel width
BRICK_ROW = 33        # 23 brick + 10 mortar
BRICK_H = 23
BASE_Y = 12           # bottom of brick row 0
BRICK_W, PERIOD = 40, 50
SB = 65               # side bearing each side
SPACE_W = 400
ITALIC_ANGLE = 12.0   # degrees

# weight masters: (wght, horizontal joint inset d, vertical inset e)
MASTERS = [("Light", 300, 6, 6), ("Bold", 700, 0, 0), ("Black", 900, -4, -4)]
INSTANCES = [(300, "Light"), (400, "Regular"), (500, "Medium"),
             (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
             (900, "Black")]

# accent zones (brick-row index of the mark's bottom course)
LC_TOP, CAP_TOP, CAP_RING = 18, 22, 21

CEDILLA_AS_COMMA = set("GKLNRgklnr")
CARON_PRECOMPOSED = {"d": "dcaron", "l": "lcaron", "L": "Lcaron", "t": "tcaron"}
MARK_FOR_COMBINING = {
    0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde",
    0x304: "macron", 0x306: "breve", 0x307: "dotaccent", 0x308: "dieresis",
    0x30A: "ring", 0x30B: "hungarumlaut", 0x30C: "caron",
    0x326: "commaaccent", 0x327: "cedilla", 0x328: "ogonek",
}
SPACING_ACCENTS = {  # codepoint: mark
    0x00B4: "acute", 0x00A8: "dieresis", 0x00AF: "macron", 0x00B8: "cedilla",
    0x02C6: "circumflex", 0x02C7: "caron", 0x02D8: "breve",
    0x02D9: "dotaccent", 0x02DA: "ring", 0x02DB: "ogonek", 0x02DC: "tilde",
    0x02DD: "hungarumlaut",
}

glyphdata.get_glyph("A")  # load the database
GDATA = glyphdata.GLYPHDATA


def info_for(cp):
    return GDATA.unicodes.get("%04X" % cp) or {}


def nice_name(cp):
    return info_for(cp).get("name") or "uni%04X" % cp


# ----------------------------------------------------------------- parsing ---
def parse(path):
    glyphs, marks = {}, {}
    cur = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s:
            cur = None
            continue
        if cur is not None and set(s) <= set("#."):
            cur["rows"].append(s)
            continue
        if s.startswith("#"):
            continue
        if s.startswith("glyph "):
            parts = s.split()
            name = parts[1]
            cp = None
            y = 0
            wmin = None
            for p in parts[2:]:
                if p.startswith("w="):
                    wmin = int(p[2:])
                if p.startswith("U+"):
                    cp = int(p[2:], 16)
                elif p.startswith("y="):
                    y = int(p[2:])
            cur = {"name": name, "cp": cp, "y": y, "rows": [], "w": wmin}
            glyphs[name] = cur
        elif s.startswith("mark "):
            parts = s.split()
            kv = dict(p.split("=") for p in parts[2:])
            cur = {"name": parts[1], "cc": int(kv["cc"]), "pos": kv["pos"], "rows": []}
            marks[parts[1]] = cur
    for g in glyphs.values():
        if g["cp"] is None:
            g["cp"] = next((int(u, 16) for u, a in GDATA.unicodes.items()
                            if a.get("name") == g["name"]), None)
    return glyphs, marks


# --------------------------------------------------------------- bitmaps ----
# A bitmap is {brick_row: set(cols)}

def pixel_bitmap(rows, y, col_off=0):
    bm = {}
    n = len(rows)
    for i, r in enumerate(rows):
        prow = y + (n - 1 - i)
        cols = {c + col_off for c, ch in enumerate(r) if ch == "#"}
        if cols:
            for k in range(3):
                bm.setdefault(prow * 3 + k, set()).update(cols)
    return bm


def mark_bitmap(mark, bottom_brick, col_off):
    bm = {}
    n = len(mark["rows"])
    for i, r in enumerate(mark["rows"]):
        row_from_bottom = n - 1 - i
        cols = {c + col_off for c, ch in enumerate(r) if ch == "#"}
        if cols:
            for k in range(3):
                bm.setdefault(bottom_brick + row_from_bottom * 3 + k, set()).update(cols)
    return bm


def merge(*bms):
    out = {}
    for bm in bms:
        for r, cols in bm.items():
            out.setdefault(r, set()).update(cols)
    return out


def extent(bm):
    cols = [c for cs in bm.values() for c in cs]
    return (min(cols), max(cols)) if cols else (0, -1)


def normalise(bm):
    lo, _ = extent(bm)
    if lo == 0:
        return bm
    return {r: {c - lo for c in cs} for r, cs in bm.items()}


def width_cols(bm):
    lo, hi = extent(bm)
    return hi - lo + 1


def top_pixel_row(bm):
    return max(bm) // 3


def bottom_row_cols(bm):
    return sorted(bm[min(bm)])


# ----------------------------------------------------------- composition ----
def center_col(base_name, bm, pos):
    if pos == "bottom" and base_name == "l":
        return 1
    w = width_cols(bm)
    return (w - 1) // 2


def place_mark(base_name, base_bm, mark, override_zone=None):
    pos = mark["pos"]
    if pos == "top":
        if override_zone is not None:
            bottom = override_zone
        elif top_pixel_row(base_bm) >= 6:
            bottom = CAP_RING if mark["name"] == "ring" else CAP_TOP
        else:
            bottom = LC_TOP
        off = center_col(base_name, base_bm, pos) - mark["cc"]
    elif pos == "bottom":
        bottom = -6 if mark["name"] == "cedilla" else -7
        off = center_col(base_name, base_bm, pos) - mark["cc"]
    else:  # ogonek: hangs from the right-most foot
        bottom = -6
        off = bottom_row_cols(base_bm)[-1]
    return mark_bitmap(mark, bottom, off)


# ------------------------------------------------------------- outlines -----
def bricks(bm):
    """Return list of (x0, x1, y0, y1, left_is_run_edge, right_is_run_edge)."""
    out = []
    for r in sorted(bm):
        cols = sorted(bm[r])
        runs, start, prev = [], None, None
        for c in cols:
            if start is None:
                start = prev = c
            elif c == prev + 1:
                prev = c
            else:
                runs.append((start, prev))
                start = prev = c
        if start is not None:
            runs.append((start, prev))
        y0 = BASE_Y + BRICK_ROW * r
        phase = 0 if r % 2 == 0 else -25
        for a, b in runs:
            R0, R1 = a * PX_W, b * PX_W + 90
            k = math.floor((R0 - phase) / PERIOD) - 1
            while True:
                bx0 = phase + k * PERIOD
                bx1 = bx0 + BRICK_W
                k += 1
                if bx0 >= R1:
                    break
                x0, x1 = max(bx0, R0), min(bx1, R1)
                if x1 - x0 <= 0:
                    continue
                out.append((x0, x1, y0, y0 + BRICK_H, x0 == R0, x1 == R1))
    return out


def draw(glyph, bm, d, e, shear, x_shift):
    pen = glyph.getPen()
    for x0, x1, y0, y1, le, re_ in bricks(bm):
        if not le:
            x0 += d
        if not re_:
            x1 -= d
        y0 += e
        y1 -= e
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]  # counter-clockwise
        pts = [(round(x + x_shift + y * shear), y) for x, y in pts]
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()


# ---------------------------------------------------------------- build -----
def build_glyph_table():
    glyphs, marks = parse(HERE / "BRANDSWOTModular.pixels")
    table = {}   # name -> dict(cp, bm, kind, anchors)

    for name, g in glyphs.items():
        table[name] = {"cp": g["cp"], "bm": pixel_bitmap(g["rows"], g["y"]),
                       "kind": "base", "w": g["w"]}

    # coverage target: GF Latin Core
    nam = HERE / "GF_Latin_Core.nam"
    targets = []
    for line in nam.read_text().splitlines():
        if line.startswith("0x"):
            targets.append(int(line.split()[0], 16))
    have = {v["cp"] for v in table.values() if v["cp"] is not None}

    # combining marks
    for cp, mname in MARK_FOR_COMBINING.items():
        mk = marks[mname]
        name = nice_name(cp)
        if mk["pos"] == "top":
            bm = mark_bitmap(mk, LC_TOP, 0)
        elif mk["pos"] == "bottom":
            bm = mark_bitmap(mk, -6 if mname == "cedilla" else -7, 0)
        else:
            bm = mark_bitmap(mk, -6, 0)
        table[name] = {"cp": cp, "bm": bm, "kind": "mark", "mark": mk}
        have.add(cp)

    # spacing accents
    for cp, mname in SPACING_ACCENTS.items():
        mk = marks[mname]
        name = nice_name(cp)
        if mk["pos"] == "top":
            bm = mark_bitmap(mk, LC_TOP, 0)
        else:
            bm = mark_bitmap(mk, -6 if mname != "commaaccent" else -7, 0)
        table[name] = {"cp": cp, "bm": bm, "kind": "spacing"}
        have.add(cp)

    # spaces
    table["space"] = {"cp": 0x20, "bm": {}, "kind": "space"}
    table["nbspace"] = {"cp": 0xA0, "bm": {}, "kind": "space"}
    have |= {0x20, 0xA0}

    by_cp = {v["cp"]: k for k, v in table.items() if v["cp"] is not None}

    # precomposed letters
    missing = []
    for cp in targets:
        if cp in have:
            continue
        dec = unicodedata.decomposition(chr(cp)).split()
        if len(dec) != 2 or dec[0].startswith("<"):
            missing.append(cp)
            continue
        base_cp, mark_cp = int(dec[0], 16), int(dec[1], 16)
        base_ch = chr(base_cp)
        mname = MARK_FOR_COMBINING.get(mark_cp)
        if mname is None or base_cp not in by_cp:
            missing.append(cp)
            continue
        if mname == "caron" and base_ch in CARON_PRECOMPOSED:
            continue  # drawn by hand
        if mname == "cedilla" and base_ch in CEDILLA_AS_COMMA:
            mname = "commaturned" if base_ch == "g" else "commaaccent"
        base_name = by_cp[base_cp]
        if base_ch in "ij" and marks[mname]["pos"] == "top":
            base_name = "idotless" if base_ch == "i" else "jdotless"
        base_bm = table[base_name]["bm"]
        mbm = place_mark(base_name, base_bm, marks[mname])
        bm = normalise(merge(base_bm, mbm))
        table[nice_name(cp)] = {"cp": cp, "bm": bm, "kind": "composite"}
        have.add(cp)
    # soft-dotted helper: i-ogonek without its dot (for i-ogonek + top accent)
    bm = normalise(merge(table["idotless"]["bm"],
                         place_mark("idotless", table["idotless"]["bm"], marks["ogonek"])))
    table["iogonek.dotless"] = {"cp": None, "bm": bm, "kind": "composite"}

    for cp in targets:
        if cp not in have and cp not in [v["cp"] for v in table.values()]:
            missing.append(cp)
    return table, marks, sorted(set(missing))


def base_anchors(name, entry):
    """Anchors for GPOS mark attachment (combining marks)."""
    bm = entry["bm"]
    if not bm:
        return []
    w = width_cols(bm)
    cc = (w - 1) // 2
    x = SB + cc * PX_W + 45
    top_zone = CAP_TOP if top_pixel_row(bm) >= 6 else LC_TOP
    anchors = [("top", x, BASE_Y + BRICK_ROW * top_zone),
               ("bottom", SB + (1 if name == "l" else cc) * PX_W + 45, BASE_Y)]
    anchors.append(("ogonek", SB + bottom_row_cols(bm)[-1] * PX_W + 45, BASE_Y))
    return anchors


def make_ufo(table, marks, style, wght, d, e, italic):
    ufo = ufoLib2.Font()
    shear = math.tan(math.radians(ITALIC_ANGLE)) if italic else 0.0
    i = ufo.info
    i.familyName = FAMILY
    i.styleName = f"{style} Italic" if italic else style
    i.versionMajor, i.versionMinor = VERSION_MAJOR, VERSION_MINOR
    i.unitsPerEm = UPM
    i.copyright = COPYRIGHT
    i.trademark = TRADEMARK
    i.openTypeNameDesigner = DESIGNER
    i.openTypeNameDesignerURL = VENDOR_URL
    i.openTypeNameManufacturer = MANUFACTURER
    i.openTypeNameManufacturerURL = VENDOR_URL
    i.openTypeNameLicense = LICENSE
    i.openTypeNameLicenseURL = LICENSE_URL
    i.openTypeNameDescription = DESCRIPTION
    i.openTypeOS2VendorID = VENDOR_ID
    i.openTypeOS2Type = []
    i.openTypeOS2WeightClass = wght
    i.openTypeOS2WidthClass = 5
    i.capHeight = 695
    i.xHeight = 497
    i.ascender = 695
    i.descender = -186
    i.italicAngle = -ITALIC_ANGLE if italic else 0
    i.openTypeHheaAscender = 1000
    i.openTypeHheaDescender = -250
    i.openTypeHheaLineGap = 0
    i.openTypeOS2TypoAscender = 1000
    i.openTypeOS2TypoDescender = -250
    i.openTypeOS2TypoLineGap = 0
    i.openTypeOS2WinAscent = 1050
    i.openTypeOS2WinDescent = 260
    i.openTypeOS2Selection = [7]  # USE_TYPO_METRICS
    i.postscriptUnderlinePosition = -100
    i.postscriptUnderlineThickness = 50
    i.postscriptIsFixedPitch = False

    order = [".notdef", "space", "nbspace"]
    letters = sorted((k for k in table if k not in order),
                     key=lambda k: (table[k]["cp"] is None, table[k]["cp"] or 0, k))
    order += letters
    ps_names, categories = {}, {}

    # .notdef — an empty brick frame
    g = ufo.newGlyph(".notdef")
    frame = {}
    for r in range(0, 21):
        frame[r] = {0, 4} if 3 <= r <= 17 else {0, 1, 2, 3, 4}
    draw(g, frame, d, e, shear, SB)
    g.width = 5 * PX_W + 120

    for name in order[1:]:
        ent = table[name]
        g = ufo.newGlyph(name)
        if ent["cp"] is not None:
            g.unicodes = [ent["cp"]]
        kind = ent["kind"]
        bm = ent["bm"]
        if kind == "space":
            g.width = SPACE_W
        elif kind == "mark":
            mk = ent["mark"]
            # draw so that the mark's centre pixel is centred on x = 0
            x_shift = -(mk["cc"] * PX_W + 45)
            draw(g, bm, d, e, shear, x_shift)
            g.width = 0
            anchor_y = {"top": BASE_Y + BRICK_ROW * LC_TOP,
                        "bottom": BASE_Y, "ogonek": BASE_Y}[mk["pos"]]
            g.appendAnchor({"name": "_" + mk["pos"], "x": 0, "y": anchor_y})
            categories[name] = "mark"
        else:
            cols = width_cols(bm) if bm else 0
            pad = 0
            if ent.get("w") and ent["w"] > cols:
                pad = (ent["w"] - cols) // 2
                cols = ent["w"]
            draw(g, bm, d, e, shear, SB + pad * PX_W)
            g.width = cols * PX_W + 120 if bm else SPACE_W
            if kind in ("base", "composite") and ent["cp"] is not None and \
                    (unicodedata.category(chr(ent["cp"])).startswith("L") or name == "dottedCircle") and kind == "base":
                for an, ax, ay in base_anchors(name, ent):
                    g.appendAnchor({"name": an, "x": round(ax + ay * shear), "y": ay})
                categories[name] = "base"
        info = info_for(ent["cp"]) if ent["cp"] is not None else {}
        if info.get("production"):
            ps_names[name] = info["production"]

    ufo.glyphOrder = order
    ufo.lib["public.postscriptNames"] = ps_names
    ufo.lib["public.openTypeCategories"] = categories
    ufo.features.text = FEATURES
    return ufo


FEATURES = """\
languagesystem DFLT dflt;
languagesystem latn dflt;

@TopMarks = [gravecomb acutecomb circumflexcomb tildecomb macroncomb
             brevecomb dotaccentcomb dieresiscomb ringcomb
             hungarumlautcomb caroncomb];

@BottomMarks = [commaaccentcomb cedillacomb ogonekcomb];

lookup dotless {
    sub i by idotless;
    sub j by jdotless;
    sub iogonek by iogonek.dotless;
} dotless;

feature ccmp {
    sub [i j iogonek]' lookup dotless @TopMarks;
    sub [i j iogonek]' lookup dotless @BottomMarks @TopMarks;
} ccmp;
"""


def main():
    table, marks, missing = build_glyph_table()
    if missing:
        print("WARNING: not yet drawn:", " ".join(chr(c) for c in missing))
    for f in HERE.glob("*.ufo"):
        shutil.rmtree(f)

    for italic in (False, True):
        ds = DesignSpaceDocument()
        ax = AxisDescriptor()
        ax.tag, ax.name = "wght", "Weight"
        ax.minimum, ax.default, ax.maximum = 300, 700, 900
        ds.addAxis(ax)
        suffix = "Italic" if italic else ""
        for style, wght, d, e in MASTERS:
            ufo = make_ufo(table, marks, style, wght, d, e, italic)
            fname = f"{PS_FAMILY}-{style}{suffix}.ufo"
            ufo.save(HERE / fname, overwrite=True)
            src = SourceDescriptor()
            src.filename = fname
            src.familyName = FAMILY
            src.styleName = f"{style} Italic" if italic else style
            src.location = {"Weight": wght}
            ds.addSource(src)
        for wght, style in INSTANCES:
            ins = InstanceDescriptor()
            ins.familyName = FAMILY
            ins.styleName = (f"{style} Italic" if style != "Regular" else "Italic") if italic else style
            ins.location = {"Weight": wght}
            ins.postScriptFontName = f"{PS_FAMILY}-{ins.styleName.replace(' ', '')}"
            ins.filename = f"instances/{ins.postScriptFontName}.ufo"
            ds.addInstance(ins)
        name = f"{PS_FAMILY}-Italic.designspace" if italic else f"{PS_FAMILY}.designspace"
        ds.write(HERE / name)
    n = len(table) + 1
    print(f"Wrote 6 masters, {n} glyphs each.")


if __name__ == "__main__":
    main()
