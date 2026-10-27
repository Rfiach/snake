"""Bettet die Hintergründe aus assets/ (bg_*.png, xmas_*.png) als JPEG-Data-URLs in index.html ein,
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


def data_urls(pattern: str) -> list[str]:
    urls = []
    for path in sorted((ROOT / "assets").glob(pattern)):
        buf = io.BytesIO()
        Image.open(path).convert("RGB").save(buf, "JPEG", quality=82, optimize=True, progressive=True)
        urls.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii"))
    return urls


def js_array(name: str, urls: list[str]) -> str:
    return f"const {name} = [\n" + ",\n".join(f'"{u}"' for u in urls) + "\n];\n"


def main() -> None:
    normal, xmas = data_urls("bg_*.png"), data_urls("xmas_*.png")
    block = START + "\n" + js_array("BG_DATA", normal) + js_array("BG_XMAS_DATA", xmas) + END
    html = HTML.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(html):
        raise SystemExit("Marker BG-DATA-START/END nicht in index.html gefunden")
    HTML.write_text(pattern.sub(lambda _: block, html), encoding="utf-8", newline="")
    total = sum(map(len, normal + xmas)) // 1024
    print(f"{len(normal)} normale + {len(xmas)} Weihnachts-Hintergründe eingebettet ({total} KB)")


if __name__ == "__main__":
    main()
