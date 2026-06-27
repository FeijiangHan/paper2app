# pipeline.md — command recipe, data formats, directory layout

A compact end-to-end reference. See `SKILL.md` for the narrative and the other
`references/*.md` for the judgement-heavy steps.

## Working directory layout (one paper)

```
work/
├── paper.pdf                  # the PDF (downloaded or provided)
├── source/                    # unpacked LaTeX source (arXiv/tex path): *.tex, *.bib, figure files
├── pages/                     # page-NN.png full-page renders (OCR + verification)
├── figures/                   # <id>.png cropped figures/tables
├── figures_manifest.json      # one record per caption (see figures.md)
├── paper.md                   # merged OCR transcript (PDF-only path)
├── refs.json                  # {refs:{key:{full,short,year,url}}, order:[...]}
├── fonts.json                 # {serif, mono, sans, detected, note}
├── macros.json                # {name: expansion}  (paper-specific LaTeX macros)
├── body.html                  # the single-column body you author
├── summaries.json             # {headingId:{t, b:[...]}}
├── figmap.json                # {figureId: imagePath}
├── figs.json                  # {figureId: dataURL}   (from pack_assets.py)
└── <slug>.html                # FINAL app
```

## Command recipe

```bash
# 0. deps
pip install pdfplumber pillow numpy --break-system-packages -q

# 1a. arXiv  ->  pdf + source
python scripts/fetch_arxiv.py --id <id-or-url> --out work/

# 1c. PDF-only  ->  page images, then transcribe with vision subagents (references/ocr.md)
python scripts/render_pages.py --pdf work/paper.pdf --out work/pages --dpi 200

# 3. figures/tables (uncropped); re-run with --overrides during the OODA loop
python scripts/extract_figures.py --pdf work/paper.pdf --out work/ --dpi 300

# 4. references with FULL names
python scripts/parse_bib.py --bib work/source/*.bib --out work/refs.json
#    (restrict to cited keys if you like: --cited work/cited_keys.txt)

# 5. fonts (match source, else clean default)
python scripts/detect_fonts.py --pdf work/paper.pdf --out work/fonts.json

# 8. pack images + assemble
python scripts/pack_assets.py --map work/figmap.json --out work/figs.json
python scripts/build_app.py --template assets/template.html --body work/body.html \
  --refs work/refs.json --figs work/figs.json --summaries work/summaries.json \
  --fonts work/fonts.json --macros work/macros.json \
  --title "<title>" --venue "<venue>" --authors "<authors>" --out work/<slug>.html
```

`build_app.py` prints `{"unfilled": []}` on success. Any placeholder left in
`unfilled` means a missing input — fix and rebuild.

## Template placeholders (filled by build_app.py)

| placeholder      | source                              |
|------------------|-------------------------------------|
| `<!--BODY-->`    | `work/body.html`                    |
| `/*REFS*/`       | `refs.json` → `refs`                |
| `/*ORDER*/`      | `refs.json` → `order`               |
| `/*FIGS*/`       | `figs.json`                         |
| `/*SUMMARIES*/`  | `summaries.json` (default `{}`)     |
| `/*FONTVARS*/`   | `fonts.json` → `--serif/--mono`     |
| `/*MACROS*/`     | `macros.json` → MathJax tex.macros  |
| `__TITLE__` `__VENUE__` `__RUNAUTH__` | CLI flags      |
| `__NAV_AUTHORS__` | derived from `--authors` (et-al for >2) — top navbar |
| `__ARXIV_HTML__`  | `--arxiv` → outbound `arXiv:<id>` link (empty if omitted) |

## JSON shapes

```jsonc
// refs.json
{ "refs": { "cohen1960kappa": {
    "full": "<span class='r-au'>Cohen, Jacob</span> (1960). <span class='r-ti'>…</span> …",
    "short": "Cohen", "year": "1960", "url": "https://doi.org/…" } },
  "order": ["arora2025healthbench", "cohen1960kappa", …] }

// summaries.json
{ "sec-method": { "t": "§2 · Method", "b": ["point one", "point two"] } }

// figmap.json   (figure id used in body's data-fig  ->  image path)
{ "fig_figure1": "work/figures/fig_figure1.png" }
```

## Optional: jsdom load smoke-test

```bash
npm i jsdom -y >/dev/null 2>&1
node -e '
const fs=require("fs"),{JSDOM,VirtualConsole}=require("jsdom");
const h=fs.readFileSync(process.argv[1],"utf8");const e=[];const vc=new VirtualConsole();
vc.on("jsdomError",x=>e.push(x.detail&&x.detail.message||x.message));
const d=new JSDOM(h,{runScripts:"dangerously",pretendToBeVisual:true,virtualConsole:vc,url:"file:///x"});
const w=d.window;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
setTimeout(()=>{w.dispatchEvent(new w.Event("load"));setTimeout(()=>{const D=w.document;
console.log(JSON.stringify({marks:D.querySelectorAll("mark.hl").length,
figs:D.querySelectorAll("img[data-fig][src^=\"data:\"]").length,
refs:D.querySelectorAll("#ref-list li").length,errors:e.length}));process.exit(0);},250);},250);
' work/<slug>.html
```
Expect `errors:0` and non-zero marks/figs/refs.

## Notes & fallbacks

- **No poppler**: install it (`apt-get install poppler-utils`) or use `pdf2image`.
  pdffonts is part of poppler too; without it `detect_fonts.py` returns clean defaults.
- **arXiv blocked**: `fetch_arxiv.py` prints an error — ask the user for the PDF/source.
- **Old-style arXiv ids** (`cs/0309040`) are handled by `fetch_arxiv.py`.
- Keep `--dpi 300` for crisp embedded figures; `pack_assets.py` quantises them (~5×
  smaller) while staying sharp.
