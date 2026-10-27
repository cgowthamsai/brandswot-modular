#!/usr/bin/env python3
"""Package the desktop download: OTF + TTF + variable + licence + readme."""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
version = sys.argv[1] if len(sys.argv) > 1 else "dev"
dist = ROOT / "dist"
dist.mkdir(exist_ok=True)
out = dist / f"BRANDSWOT-Modular-v{version}.zip"
top = f"BRANDSWOT-Modular-v{version}"

readme = f"""BRANDSWOT Modular v{version}
Designed by Gowtham Sai · BRANDSWOT Consultancy · https://brandswotconsultancy.com

INSTALL
  Windows : open the otf folder, select all files, right-click > Install for all users
  macOS   : open the otf folder, select all files, double-click > Install Font
  Linux   : copy the otf files to ~/.local/share/fonts and run fc-cache -f

WHICH FILES?
  otf/       Desktop apps (Word, Figma, Photoshop, Illustrator, InDesign, Canva upload)
  ttf/       Older software, video editors, games engines
  variable/  One file with every weight from Light 300 to Black 900 (Figma, web, After Effects)
  web/       .woff2 files for websites

LICENCE
  Free for personal and commercial use under the SIL Open Font License 1.1 (OFL.txt).
  You may use it in logos, products, apps and print. You may not sell the font files on their own.

Source, issues and updates: https://github.com/cgowthamsai/brandswot-modular
"""

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for sub, dest in (("fonts/otf", "otf"), ("fonts/ttf", "ttf"),
                      ("fonts/variable", "variable"), ("fonts/webfonts", "web")):
        for f in sorted((ROOT / sub).glob("*")):
            z.write(f, f"{top}/{dest}/{f.name}")
    for f in ("OFL.txt", "FONTLOG.txt"):
        z.write(ROOT / f, f"{top}/{f}")
    z.writestr(f"{top}/READ-ME.txt", readme)
print(out)
