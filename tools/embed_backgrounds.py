"""Bettet die Hintergründe aus assets/ als JPEG-Data-URLs in index.html ein,
damit die Browser-Version ohne den assets-Ordner funktioniert.

    py -m pip install --user pillow
    py tools/embed_backgrounds.py
"""
from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
START, END = "/* BG-DATA-START */", "/* BG-DATA-END */"


def main() -> None:
    urls = []
    for path in sorted((ROOT / "assets").glob("bg_*.png")):
        buf = io.BytesIO()
        Image.open(path).convert("RGB").save(buf, "JPEG", quality=82, optimize=True, progressive=True)
        urls.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii"))
    block = START + "\nconst BG_DATA = [\n" + ",\n".join(f'"{u}"' for u in urls) + "\n];\n" + END
    html = HTML.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(html):
        raise SystemExit("Marker BG-DATA-START/END nicht in index.html gefunden")
    HTML.write_text(pattern.sub(lambda _: block, html), encoding="utf-8")
    print(f"{len(urls)} Hintergründe eingebettet ({sum(map(len, urls)) // 1024} KB)")


if __name__ == "__main__":
    main()
