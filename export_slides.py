#!/usr/bin/env python3
"""Export deck.html slides to individual PNGs and a combined PDF for LinkedIn."""

import os
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

DECK_PATH = Path(__file__).parent / "deck.html"
OUT_DIR = Path(__file__).parent / "slides_export"
CHROME = "google-chrome"
WIDTH = 1920
HEIGHT = 1080

def get_slide_count(html: str) -> int:
    return len(re.findall(r'class="slide[^"]*"', html))

def make_slide_html(html: str, slide_num: int, total: int) -> str:
    """Return HTML with only slide_num active, others hidden."""
    result = html

    # Remove any existing 'active' class from slides
    result = re.sub(
        r'(<div class="slide) active(")',
        r'\1\2',
        result
    )

    # Add 'active' to the target slide (e.g. id="s3")
    result = re.sub(
        rf'(<div class="slide"[^>]*id="s{slide_num}")',
        r'\1',
        result
    )
    # Actually activate it: replace 'class="slide"' for the matching id
    result = re.sub(
        rf'(<div )(class="slide")(.*?id="s{slide_num}")',
        r'\1class="slide active"\3',
        result
    )

    return result

def screenshot(html_path: str, out_png: str):
    subprocess.run([
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--window-size={WIDTH},{HEIGHT}",
        "--hide-scrollbars",
        f"--screenshot={out_png}",
        f"file://{html_path}",
    ], check=True, capture_output=True)

def make_pdf_html(slide_pngs: list[str]) -> str:
    """Create an HTML file that prints each PNG as a separate page."""
    items = ""
    for png in slide_pngs:
        items += f'<div class="page"><img src="file://{png}"></div>\n'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  @page {{ size: {WIDTH}px {HEIGHT}px; margin: 0; }}
  body {{ background: #000; }}
  .page {{
    width: {WIDTH}px;
    height: {HEIGHT}px;
    page-break-after: always;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .page img {{ width: 100%; height: 100%; object-fit: cover; }}
</style>
</head>
<body>
{items}
</body>
</html>"""

def main():
    OUT_DIR.mkdir(exist_ok=True)
    html = DECK_PATH.read_text()

    # Detect total slides
    ids = re.findall(r'id="s(\d+)"', html)
    total = max(int(i) for i in ids) if ids else 0
    print(f"Found {total} slides.")

    tmp_dir = tempfile.mkdtemp()
    slide_pngs = []

    try:
        for i in range(1, total + 1):
            slide_html = make_slide_html(html, i, total)
            tmp_html = os.path.join(tmp_dir, f"slide_{i}.html")
            Path(tmp_html).write_text(slide_html)

            out_png = os.path.join(tmp_dir, f"slide_{i:02d}.png")
            print(f"  Capturing slide {i}...", end=" ", flush=True)
            screenshot(tmp_html, out_png)
            print("done")
            slide_pngs.append(out_png)

        # Build PDF
        pdf_html_path = os.path.join(tmp_dir, "deck_for_pdf.html")
        Path(pdf_html_path).write_text(make_pdf_html(slide_pngs))
        pdf_out = str(OUT_DIR / "aria_deck.pdf")
        print("Building PDF...", end=" ", flush=True)
        subprocess.run([
            CHROME,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_out}",
            f"file://{pdf_html_path}",
        ], check=True, capture_output=True)
        print("done")

        print(f"\nDone! PDF saved to: {OUT_DIR}")
        print(f"  • aria_deck.pdf  ← upload this to LinkedIn as a document post")

    finally:
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()