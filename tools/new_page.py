#!/usr/bin/env python3
"""Generate a Data_Structure_MOV animation page from the shared template.

Stitches page_template.html together with a frames JSON file (durationMs /
code / frames) and a hand-written render.js file (must define
`function render(ms){...}`), so the boilerplate (CSS, player controls,
seek-range max, viewBox/aspect-ratio) can never drift out of sync with the
content -- that's the class of bug that slipped into ch06-bucket-insert and
ch06-bucket-sort by hand.

Usage:
  python3 tools/new_page.py \
    --title ch07-counting-sort \
    --aria-label "分布数え上げソートのアニメーション" \
    --viewbox 720 440 \
    --frames /tmp/ch07-counting-sort.frames.json \
    --render /tmp/ch07-counting-sort.render.js \
    --out GitHub_Pages/pages/ch07-counting-sort.html
"""
import argparse
import json
import pathlib
import sys

TOOLS_DIR = pathlib.Path(__file__).parent
TEMPLATE_PATH = TOOLS_DIR / "page_template.html"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", required=True, help="<title> and <h1> text, e.g. ch07-counting-sort")
    ap.add_argument("--aria-label", required=True, help="SVG role=img aria-label")
    ap.add_argument("--viewbox", nargs=2, type=int, metavar=("W", "H"), required=True)
    ap.add_argument("--frames", required=True, type=pathlib.Path, help="JSON file: {durationMs, code, frames}")
    ap.add_argument("--render", required=True, type=pathlib.Path, help="JS file defining function render(ms){...}")
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    frames_data = json.loads(args.frames.read_text(encoding="utf-8"))
    for key in ("durationMs", "code", "frames"):
        if key not in frames_data:
            sys.exit(f"error: {args.frames} is missing required key '{key}'")
    if not frames_data["frames"]:
        sys.exit(f"error: {args.frames} has zero frames")
    last_at = frames_data["frames"][-1]["at"]
    if last_at >= frames_data["durationMs"]:
        sys.exit(f"error: last frame at={last_at} must be < durationMs={frames_data['durationMs']}")

    render_body = args.render.read_text(encoding="utf-8").rstrip("\n")
    if "function render(ms)" not in render_body:
        sys.exit(f"error: {args.render} must define function render(ms){{...}}")

    w, h = args.viewbox
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("__TITLE__", args.title)
    html = html.replace("__ARIA_LABEL__", args.aria_label)
    html = html.replace("__ASPECT__", f"{w}/{h}")
    html = html.replace("__VIEWBOX_W__", str(w))
    html = html.replace("__VIEWBOX_H__", str(h))
    html = html.replace("__DURATION_MS__", str(frames_data["durationMs"]))
    html = html.replace("__FRAMESCRIPT_JSON__", json.dumps(frames_data, ensure_ascii=False, indent=2))
    html = html.replace("__RENDER_BODY__", render_body)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
