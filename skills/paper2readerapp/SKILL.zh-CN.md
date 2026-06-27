---
name: paper2readerapp-zh
description: >-
  Chinese variant of paper2readerapp. Convert any research paper into a single
  self-contained, interactive Chinese HTML reader app with one-column layout,
  Chinese highlights, Chinese sidenotes, Chinese section summaries, citation
  popovers, MathJax, and never-cropped figures/tables. Use when the user asks for
  a Chinese paper reader app or a Chinese version of the generated app.
---


# paper2readerapp 中文版

把论文转换成上文描述的中文交互式单栏阅读 app。 The
mechanical work (download, render, crop, parse, assemble) is done by the scripts
in `scripts/`. The *understanding* work — transcribing a PDF with vision,
authoring the highlight tour and the section summaries, and verifying nothing was
dropped or cropped — is done by **you and subagents**. This skill has no external
OCR dependency: when only a PDF is available you transcribe page images yourself
(a strong vision+OCR model), one page at a time, ideally via subagents.

Read this whole file first, then read the relevant `references/` file before the
step that needs it. Keep a running scratch `work/` directory for one paper.

## Chinese-output policy

This is the Chinese variant. Unless the user explicitly requests otherwise, the
final generated reader app MUST use Chinese for all reader-facing explanatory
content:

- translate or rewrite the paper title, section summaries, highlight notes, tour
  titles, figure/table explanatory captions, UI-facing helper text, and any added
  pedagogical explanations in natural Simplified Chinese;
- preserve mathematical notation, citation keys, author names, equations, figure
  labels, theorem names, and technical terms when translating them would reduce
  precision;
- keep the source paper faithful: do not invent claims, and do not omit important
  caveats during translation or simplification;
- write highlight sidenotes and section bullets in clear Chinese suitable for a
  technical reader who wants to understand the paper quickly;
- if the paper itself is already Chinese, preserve its terminology and only add
  the app annotations in Chinese.

When assembling `work/body.html`, the body content should be a Chinese reading
version of the paper, not merely an English app chrome with a few translated notes.
References may keep original titles and venues when that is the most faithful option,
but citation popovers should use Chinese field labels if labels are added.

## What you produce

ONE standalone Chinese `<paper-slug>.html` file (figures embedded as base64; MathJax and
the body font load from CDN/the system). It must have, like the reference design:

- the **entire paper** in a single reading column, even if the source is 2-column;
- inline **figures and tables** (never cropped), each with its caption as real text;
- a **pink highlighter** over the salient passages; clicking a highlight opens a
  Chinese plain-language sidenote; the bottom navbar walks a curated, non-linear learning
  path through the highlights (Reset / Prev / Next) with a progress scrubber and a
  **Back** button that returns from figure/section jumps;
- **teal section/subsection summaries**: clicking any heading (except Introduction,
  Related Work, and Conclusion) opens a bullet summary;
- **citations in the paper's author–year style**, each name individually clickable,
  opening a non-dimming popover with the full reference (no abstract);
- the **source's fonts** where detectable, else a clean serif.

## Requirements

- **Subagents** (Task tool) for parallel page OCR, authoring, and verification.
  If subagents are unavailable, do the steps inline, one at a time.
- **bash + python** with `pdfplumber pillow numpy` (`pip install --break-system-packages`)
  and **poppler** (`pdftoppm`, `pdffonts`). Node is handy for a load smoke-test.
- Network only for the arXiv path (`scripts/fetch_arxiv.py`). If it's blocked, ask
  the user to supply the PDF and/or source files directly.

## Step 0 — Set up

```bash
mkdir -p work
pip install pdfplumber pillow numpy --break-system-packages -q
```
Decide the input mode from what the user gave you:
- an **arXiv id or URL** → Step 1a
- a **.tex (+ .bib)** (with or without a PDF) → Step 1b
- a **PDF only** → Step 1c

## Step 1a — arXiv

```bash
python scripts/fetch_arxiv.py --id <arxiv-id-or-url> --out work/
```
This downloads the **PDF** and the **LaTeX e-print source**, unpacks it, and prints
JSON with `pdf`, `main_tex`, `bib_files`, and `image_files`. Then continue as the
tex path (Step 1b) using the downloaded `main_tex`/`bib_files`, and keep the `pdf`
for figure extraction (Step 3) and font detection (Step 5). If the download fails,
tell the user and ask for the files.

## Step 1b — LaTeX source (preferred when available)

The `.tex` is the most reliable source of text, structure, math, citation keys and
reading order. Read `main_tex` (and any `\input`/`\include` files). You will author
the body HTML from it in Step 6. Note the figure environments and which figures
have **image files** in the source (`\includegraphics{...}`) versus ones drawn in
LaTeX (TikZ/pgfplots) that exist only in the PDF.

Extract paper-specific macros: scan the preamble for `\newcommand`/`\def` and record
them as `work/macros.json` (`{ "Mgen": "M_{q}", ... }`) so equations render.

## Step 1c — PDF only (vision OCR)

Render every page, then transcribe each page image to detailed Markdown **yourself**
(no external OCR tool). Read `references/ocr.md` for the exact per-page instructions
and reading-order rules (this is where single-column reconstruction of a 2-column
PDF happens).

```bash
python scripts/render_pages.py --pdf work/paper.pdf --out work/pages --dpi 200
```
Then spawn one subagent per page (or per few pages) — each reads its page PNG and
returns Markdown for that page. Merge the pages in order. Capture math as LaTeX,
mark figure/table locations, and keep citation call-outs.

## Step 2 — Decide the figure source

Read `references/figures.md`. Rule of thumb:
- a figure that ships as an **image file** in the LaTeX source → use that file (best
  fidelity);
- a figure that exists **only in the PDF** (TikZ/pgfplots, or PDF-only input) →
  extract it from the PDF in Step 3. **The non-cropping guarantee and verification
  apply to every PDF-extracted figure.**

## Step 3 — Extract figures and tables from the PDF (never cropped)

```bash
python scripts/extract_figures.py --pdf work/paper.pdf --out work/ --dpi 300
```
Writes `work/figures/<id>.png`, full-page renders in `work/pages/`, and
`work/figures_manifest.json`. The script anchors each crop on its caption and grows
it to the **largest whitespace gap** so legends/axis-titles/panels are never clipped;
it auto-detects 1- vs 2-column layout, marks body-text false-positives (`body_ref`)
and `duplicate` captions as non-`primary`, and flags anything to re-check in
`suspicious`. Use only `primary: true` records. For any flagged or wrong crop, follow
the **override + OODA** loop in `references/figures.md` (re-run with `--overrides`).

## Step 4 — References (FULL author names)

```bash
python scripts/parse_bib.py --bib work/source/*.bib --out work/refs.json
```
Important policy: **use the names exactly as the source provides them, and never
abbreviate a first name** — BibTeX `author` fields are usually full even when the
printed PDF shows initials, and `parse_bib.py` keeps them full. Do **not** look names
up online. If the source only has an initial, keep the initial. For a PDF-only paper
with no `.bib`, build the same `refs.json` shape from the references you transcribed,
preserving whatever names the paper printed.

## Step 5 — Fonts (match source, else clean default)

```bash
python scripts/detect_fonts.py --pdf work/paper.pdf --out work/fonts.json
```
Maps the PDF's dominant body/mono fonts to close web/system stacks; falls back to a
clean serif. (No PDF? Skip — the template's clean default is used.)

## Step 6 — Author the body HTML (single column)

Read `references/authoring.md` for the **exact markup the template expects** and write
`work/body.html`: title/authors/abstract, then every section in reading order as
`<h2 id>`/`<h3 id>`/`<p>`, inline `<figure id><img data-fig="..."><figcaption>`, math in
`$...$`/`$$...$$`, citations as `<cite data-k="key1,key2">` (or `data-p="t"` for textual),
internal links as `<a class="xref" data-ref="targetId">`, and a `<div id="ref-list"></div>`
under a `## References` heading. **Always single column**, regardless of the source
layout. For long papers, split the sections across subagents, giving each the
authoring conventions and the figure-id list, then concatenate.

## Step 7 — Author the highlight tour and the section summaries (comprehensive)

Still in `references/authoring.md`. This is the heart of the experience.
- **Highlights**: wrap the salient spans in `<mark class="hl" data-tour="N" data-title="..."
  data-note="...">`. `data-tour` is the *pedagogical* order (floats allowed, e.g. `8.5`),
  which should be the best sequence for understanding and may jump around the paper.
  Notes are Simplified Chinese plain text (unicode symbols, no LaTeX, no double quotes).
- **Summaries**: give every `<h2>`/`<h3>` a stable `id`, then write Chinese bullet summaries in
  `work/summaries.json` mapping that id → `{ "t": "short title", "b": ["bullet", ...] }`
  for **every section and subsection EXCEPT** the Introduction, Related Work, and
  Conclusion. Be comprehensive.

## Step 8 — Assemble

```bash
python scripts/pack_assets.py --map work/figmap.json --out work/figs.json
python scripts/build_app.py --template assets/template.html --body work/body.html \
  --refs work/refs.json --figs work/figs.json --summaries work/summaries.json \
  --fonts work/fonts.json --macros work/macros.json \
  --title "<paper title>" --venue "<venue/arXiv>" --authors "<full author list, comma-separated>" \
  [--arxiv <arxiv-id>] --out work/<slug>.html
```
`work/figmap.json` is `{ figure-id: image-path }` for the `primary` figures you kept
(source images or `work/figures/<id>.png`). Pass the **full comma-separated author list**
to `--authors`; the build derives the top-navbar form itself (et-al shortening for >2).
Pass `--arxiv <id>` **only for arXiv inputs** — it renders the outbound `arXiv:<id>`
link in the scroll-in top navbar (omit it for non-arXiv papers). The top navbar and the
"Built with paper2readerapp" footer are part of the template and need no extra work.
`build_app.py` prints `unfilled: []` when all placeholders are filled — investigate if not.

## Step 9 — Verify and OODA until clean

Read `references/verify.md`. Spawn a **verifier subagent** that compares the built app
against the source and checks: every page/section is present; every figure and table
is extracted **and not cropped** (compare each figure to its full-page render); the
reading order is correct and single-column; citations resolve and names are full; math
renders; highlights and summaries exist and are mutually exclusive. It returns a
defect list. **Observe → Orient → Decide → Act**: fix (re-OCR a page, re-crop a figure
via `--overrides`, edit the body, re-author a note), rebuild, and re-verify. Loop until
the verifier reports no defects. Also run a quick load smoke-test (no JS console errors)
if Node is available.

## Step 10 — Deliver

Present the final Chinese `<slug>.html` to the user (use `present_files` if available). Mention
they can open it in any browser, and offer to tune the highlight density or theme.

## Non-negotiables (these are the whole point)

- **Single column always.** A 2-column PDF still renders as one reading column.
- **Figures are never cropped.** If a crop might be clipped, expand and re-verify.
- **Full author names.** Never abbreviate a first name the source gives in full.
- **Comprehensive annotations.** A reader should be able to understand the paper from
  the highlights + notes + summaries alone.

## Reference files

- `references/pipeline.md` — end-to-end command recipe, data formats, directory layout.
- `references/ocr.md` — per-page vision OCR instructions (PDF-only path, reading order).
- `references/figures.md` — uncropped extraction, the manifest, override/OODA loop,
  source-image vs PDF-crop decision, 2-column handling.
- `references/authoring.md` — the exact template markup; how to choose highlights and
  write notes; how to author section summaries; math, citations, cross-refs.
- `references/verify.md` — verifier subagent checklist and the OODA repair loop.
