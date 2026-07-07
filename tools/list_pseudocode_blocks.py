#!/usr/bin/env python3
"""List pseudocode blocks in a chNN.tex chapter file, next to the animation
pages that already exist for that chapter, to help decide what still needs
an animation at the same granularity as ch02-ch06.

This does not decide anything automatically -- struct/declaration-only
blocks (e.g. "struct cell {...}") and trivial one-line wrapper functions
should usually be skipped, the same way ch06 skipped the naive radix_sort
wrapper in favor of animating radix_sort_with_buckets directly. Use
judgement; this is just the inventory step.

Usage:
  python3 tools/list_pseudocode_blocks.py \
    /path/to/Data_Structure_And_Algorithms/src/chapters/ch07.tex
"""
import pathlib
import re
import sys

BLOCK_RE = re.compile(r"\\begin\{lstlisting\}\[style=pseudocode\}?\](.*?)\\end\{lstlisting\}", re.S)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tex_path = pathlib.Path(sys.argv[1])
    if not tex_path.exists():
        sys.exit(f"error: {tex_path} not found")

    chapter_m = re.search(r"(ch\d\d)", tex_path.stem)
    chapter = chapter_m.group(1) if chapter_m else "ch??"
    text = tex_path.read_text(encoding="utf-8")

    print(f"=== pseudocode blocks in {tex_path.name} ===")
    count = 0
    for m in re.finditer(r"\\begin\{lstlisting\}\[style=pseudocode\](.*?)\\end\{lstlisting\}", text, re.S):
        count += 1
        block = m.group(1).strip("\n")
        lines = [ln for ln in block.splitlines() if ln.strip()]
        first_line = lines[0].strip() if lines else ""
        line_no = text[: m.start()].count("\n") + 1
        looks_like_decl = first_line.startswith("struct ") or (
            "(" not in first_line and first_line.endswith(";")
        )
        tag = "  [struct/decl only? check by hand]" if looks_like_decl else ""
        print(f"  L{line_no}: {first_line}{tag}")
    if count == 0:
        print("  (no pseudocode blocks found)")

    pages_dir = pathlib.Path(__file__).parent.parent / "GitHub_Pages" / "pages"
    existing = sorted(p.name for p in pages_dir.glob(f"{chapter}-*.html"))
    print(f"\n=== existing animation pages for {chapter} ===")
    if existing:
        for name in existing:
            print(" ", name)
    else:
        print("  (none yet)")


if __name__ == "__main__":
    main()
