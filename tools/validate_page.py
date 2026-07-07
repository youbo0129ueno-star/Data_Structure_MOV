#!/usr/bin/env python3
"""Validate one or more Data_Structure_MOV animation pages before pushing.

Checks (all of these have been real bugs during ch06 authoring):
  - the embedded framescript <script type="application/json"> block parses
    and has durationMs / code / frames
  - frame.at values are non-decreasing and the last one is < durationMs
  - every frame.codeLines index is within range of the code[] array
  - the seek <input max="..."> matches durationMs (they must never drift)
  - the player <script> block (boilerplate + custom render) passes
    `node --check`, i.e. has no JS syntax errors

This does NOT check the rendered SVG visually (overlapping text,
out-of-viewBox coordinates). Always open the page in a browser and play it
through once before pushing -- see tools/README.md.

Usage:
  python3 tools/validate_page.py GitHub_Pages/pages/ch06-*.html
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

FRAMESCRIPT_RE = re.compile(
    r'<script id="framescript" type="application/json">\n(.*?)\n  </script>', re.S
)
PLAYER_SCRIPT_RE = re.compile(r"<script>\n(.*?)\n  </script>\n</body>", re.S)
SEEK_MAX_RE = re.compile(r'id="seek"[^>]*max="(\d+)"')


def check(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    html = path.read_text(encoding="utf-8")

    m = FRAMESCRIPT_RE.search(html)
    if not m:
        return ["no <script id=\"framescript\"> block found"]
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return [f"framescript JSON invalid: {e}"]

    duration = data.get("durationMs")
    code = data.get("code", [])
    frames = data.get("frames", [])
    if duration is None:
        errors.append("framescript is missing durationMs")
    if not frames:
        errors.append("framescript has zero frames")

    prev_at = -1
    for i, f in enumerate(frames):
        at = f.get("at")
        if at is None or at < prev_at:
            errors.append(f"frame {i}: 'at' missing or not non-decreasing (at={at}, prev={prev_at})")
        else:
            prev_at = at
        for cl in f.get("codeLines", []):
            if cl < 0 or cl >= len(code):
                errors.append(f"frame {i}: codeLines index {cl} out of range (code has {len(code)} lines)")

    if frames and duration is not None and frames[-1].get("at", 0) >= duration:
        errors.append(f"last frame at={frames[-1]['at']} must be < durationMs={duration}")

    seek_m = SEEK_MAX_RE.search(html)
    if not seek_m:
        errors.append("no #seek input with max=... found")
    elif duration is not None and int(seek_m.group(1)) != duration:
        errors.append(f"seek max={seek_m.group(1)} does not match durationMs={duration}")

    script_m = PLAYER_SCRIPT_RE.search(html)
    if not script_m:
        errors.append("player <script> block not found")
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
            tf.write(script_m.group(1))
            tf_path = tf.name
        result = subprocess.run(["node", "--check", tf_path], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"node --check failed:\n{result.stderr.strip()}")

    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="+", type=pathlib.Path)
    args = ap.parse_args()

    failed = False
    for p in args.pages:
        errors = check(p)
        if errors:
            failed = True
            for e in errors:
                print(f"FAIL: {p}: {e}")
        else:
            print(f"OK:   {p}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
