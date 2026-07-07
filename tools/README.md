# tools/ — animation page harness

Scripts that generate and validate the self-contained SVG animation pages
under `GitHub_Pages/pages/`, so ch07-ch12 can be built at the same
granularity as ch02-ch06 without hand-copying boilerplate (which is how the
ch06-bucket-insert link bug and the ch06 label/marker overlap happened).

## Workflow for one chapter

1. **Inventory the chapter.**
   ```
   python3 tools/list_pseudocode_blocks.py /path/to/Data_Structure_And_Algorithms/src/chapters/ch07.tex
   ```
   Lists every `lstlisting[style=pseudocode]` block with its first line, and
   the animation pages that already exist for that chapter. Decide by hand
   which blocks deserve their own page — skip pure `struct` declarations and
   trivial one-line wrappers that just call a "real" variant (e.g. ch06
   skipped the naive `radix_sort` wrapper in favor of animating
   `radix_sort_with_buckets` directly, matching how ch04/ch05 only animate
   the substantive lstlisting blocks). Aim for one page per algorithm, ~4-10
   frames each, following a worked example already present in the .tex if
   one exists (reuse its exact numbers so the animation matches the text).

2. **Write two small files per page** (anywhere, e.g. `/tmp/`):
   - `<slug>.frames.json` — `{"durationMs": ..., "code": [...], "frames": [...]}`.
     `code` is the pseudocode split into lines (matches the lstlisting).
     Each frame has at least `at` (ms, non-decreasing) and `codeLines`
     (indices into `code` to highlight), plus whatever fields your render
     function needs.
   - `<slug>.render.js` — a single `function render(ms){...}` that reads
     `script.frames[frameIndexAt(ms)]`, clears `svg.innerHTML`, draws SVG
     nodes, and sets `label.textContent` / `note.textContent` / calls
     `highlightCode(f)` / `seek.value=ms`. The template already provides
     `script`, `svg`, `code`, `label`, `note`, `seek`, `el()`, `write()`,
     `marker()`, `arrowDefs()`, `frameIndexAt()`, `highlightCode()` in
     scope — don't redeclare them.

   Two established visual families to reuse (see existing pages):
   - **array/bucket family** (`ch06-bucket-sort.html`,
     `ch06-radix-sort-buckets.html`): a value row of boxes plus stacked
     "bucket" columns below.
   - **chain/pointer family** (`ch05-chained-hash-insert.html`,
     `ch06-bucket-insert.html`): boxes for a header array plus linked nodes
     joined by `.edge` lines, using `arrowDefs()`/`marker` for arrowheads.

   Leave at least ~20px of vertical gap between any text row and the row
   below it (labels at y≈16, per-cell markers at y≈40, cells starting at
   y≈48 is the pattern used in ch06) — this is what the earlier "i= と灰色の
   文字が被る" bug violated.

3. **Generate the page.**
   ```
   python3 tools/new_page.py \
     --title ch07-<slug> \
     --aria-label "<日本語で内容を説明>" \
     --viewbox 720 <height> \
     --frames /tmp/<slug>.frames.json \
     --render /tmp/<slug>.render.js \
     --out GitHub_Pages/pages/ch07-<slug>.html
   ```
   `durationMs`, the seek `max`, and the `aspect-ratio`/`viewBox` are all
   derived from your inputs, so they can't drift out of sync with each other.

4. **Validate.**
   ```
   python3 tools/validate_page.py GitHub_Pages/pages/ch07-*.html
   ```
   Catches JSON errors, non-monotonic/overrunning frame timestamps,
   out-of-range `codeLines`, seek/durationMs mismatches, and JS syntax
   errors. It does **not** check the rendered SVG visually.

5. **Look at it.** Always, no exceptions:
   ```
   cd GitHub_Pages && python3 -m http.server 8791
   open http://localhost:8791/pages/ch07-<slug>.html
   ```
   Play it through at least once. Check for overlapping text and elements
   drifting outside the `viewBox` (SVG clips silently — nothing raises an
   error).

6. **Wire it into the site and the textbook.**
   - Add a `<a class="item ...">` entry to the matching `<section
     class="chapter">` in `GitHub_Pages/index.html`, and bump that
     chapter's `<span class="pill">` count in the header summary.
   - In the textbook repo, insert right after the matching
     `\end{lstlisting}` in `src/chapters/ch07.tex`:
     ```
     \href{https://youbo0129ueno-star.github.io/Data_Structure_MOV/GitHub_Pages/pages/ch07-<slug>.html}
     {\color{blue}ここをクリック}
     \color{black}で映像を確認できます.
     ```

7. **Commit and push `main` directly** (not a feature branch). GitHub Pages
   serves from `main`; ch05/ch06 were briefly 404 in production because
   their commits landed only on a side branch and were never merged.
