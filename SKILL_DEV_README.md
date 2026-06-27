# Developing paper2readerapp

This document is for people who want to **modify or extend** the skill. End-user
install, usage, and theming live in `README.md`. For day-to-day "how does the agent
run this" detail, the authoritative spec is the skill itself
(`skills/paper2readerapp/SKILL.md`) and its `references/`.

## Repository layout

```
paper2readerapp/                         # GitHub repo root = a single-plugin marketplace
├── .claude-plugin/
│   ├── marketplace.json                 # what `/plugin marketplace add delip/paper2readerapp` reads
│   └── plugin.json                      # the plugin manifest (plugin == repo root)
├── skills/
│   └── paper2readerapp/                 # the skill (auto-discovered by the plugin loader)
│       ├── SKILL.md                     # orchestration the agent follows
│       ├── assets/template.html         # the reusable app shell (CSS + JS) with placeholders
│       ├── scripts/                     # deterministic helpers (Python)
│       └── references/                  # detail docs the agent loads as needed
├── README.md                            # for users / installers
├── SKILL_DEV_README.md                  # this file
└── .gitignore
```

`source: "./"` in `marketplace.json` means the plugin is the repo itself; the loader
discovers the skill at `skills/paper2readerapp/SKILL.md`.

## Architecture: deterministic scripts + agentic judgement

The split is deliberate. **Scripts** do the mechanical, reproducible work; **the agent
(and subagents)** do everything that needs understanding. Keep that boundary when you
extend it — push repeatable logic into a script, leave judgement to the SKILL.md prose.

Scripts (`skills/paper2readerapp/scripts/`):

| script | role | key flags |
|---|---|---|
| `fetch_arxiv.py` | arXiv id/URL → PDF + unpacked LaTeX source; finds `main.tex`, `.bib`, image files | `--id --out` |
| `render_pages.py` | PDF → page PNGs (vision OCR + verification) | `--pdf --out --dpi` |
| `extract_figures.py` | caption-anchored, **never-cropped** figure/table/algorithm crops + manifest; full-page renders | `--pdf --out --dpi --overrides --list-only` |
| `parse_bib.py` | `.bib` → references with **full** author names | `--bib --out --cited` |
| `detect_fonts.py` | `pdffonts` → CSS font stacks (match source, else clean default) | `--pdf --out` |
| `pack_assets.py` | quantise + base64-embed chosen figures | `--map --out --maxw --colors` |
| `build_app.py` | fill the template → final standalone HTML | `--template --body --refs --figs --summaries --fonts --macros --title --venue --authors --out` |

Agentic steps (in `SKILL.md`): transcribe a PDF with vision (`references/ocr.md`), merge
two columns into one reading flow, author the body HTML and the highlight tour + section
summaries (`references/authoring.md`), and run a verifier subagent in an OODA loop
(`references/verify.md`) until figures, text, citations, and maths are all faithful.

## The template contract

`assets/template.html` is the proven app shell. `build_app.py` fills these placeholders:

| placeholder | filled from |
|---|---|
| `<!--BODY-->` | the authored body HTML |
| `/*REFS*/` `/*ORDER*/` | `parse_bib.py` output (`refs`, `order`) |
| `/*FIGS*/` | `pack_assets.py` output (`{id: dataURL}`) |
| `/*SUMMARIES*/` | `{headingId: {t, b:[...]}}` |
| `/*FONTVARS*/` | `detect_fonts.py` → `--serif/--mono` overrides |
| `/*MACROS*/` | paper-specific LaTeX macros for MathJax |
| `__TITLE__` `__VENUE__` `__RUNAUTH__` | CLI metadata |

The body markup the template expects (marks, cites, figures, cross-refs, headings) is
specified in `skills/paper2readerapp/references/authoring.md` — read it before changing
the template's CSS/JS so you don't break the contract. The interactive behavior
(highlight tour, summaries, citation popovers, Back button) is all in the template's
inline `<script>`; the colors are CSS variables at the top of `:root`.

## Common modifications

- **Change the look** for every generated app → edit CSS variables / styles in
  `assets/template.html`.
- **Add interactive behavior** → edit the inline `<script>` in the template, then
  re-validate with the jsdom smoke test (below). Keep the existing IDs/classes that the
  body markup and `build_app.py` depend on.
- **Add a font mapping** → extend the `SERIF_MAP`/`MONO_MAP`/`SANS_MAP` tables in
  `scripts/detect_fonts.py` (match on a lowercased, de-subsetted font-name substring).
- **Improve figure extraction** → `scripts/extract_figures.py`. The core idea is
  caption-anchoring + "grow to the largest whitespace gap" so nothing clips; preserve the
  `--list-only` fast path (no rendering), the `body_ref`/`primary`/`suspicious` flags, and
  the `--overrides` repair hook used by the OODA loop.
- **Change orchestration** → `SKILL.md` and `references/*.md`. Keep `SKILL.md` under
  ~500 lines and push detail into `references/`.

## Testing & validation

There is no heavyweight harness; validate by running the scripts on real papers and
loading the result.

Per-script smoke (any paper):
```bash
cd skills/paper2readerapp
python scripts/parse_bib.py   --bib /path/main.bib --out /tmp/refs.json
python scripts/detect_fonts.py --pdf /path/paper.pdf --out /tmp/fonts.json
python scripts/extract_figures.py --pdf /path/paper.pdf --out /tmp/w --list-only   # fast: caption counts
```
A good cross-check: the figure/table count `extract_figures.py` derives from the **PDF**
should match `\begin{figure}`/`\begin{table}` counts in the LaTeX source. (On
arXiv:2604.05018 both gave 16 figures + 8 tables; on the monotonicity paper all 13
figures came out uncropped — see git history for the validation that also caught a
truncated-PNG bug in the list-only path.)

Final-app load test (no JS console errors), the snippet is in
`skills/paper2readerapp/references/pipeline.md`:
```bash
npm i jsdom -y && node -e '…'   # expect errors:0 and non-zero marks/figs/refs
```

## Packaging & publishing

- **Publish to the marketplace**: push this repo to `github.com/delip/paper2readerapp`.
  Users then run `/plugin marketplace add delip/paper2readerapp` and
  `/plugin install paper2readerapp@paper2readerapp`. Bump `version` in **both**
  `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` on each release.
- **Single-file skill bundle** (for sharing outside a repo): zip the skill folder with a
  `.skill` extension —
  `cd skills && zip -r ../paper2readerapp.skill paper2readerapp` — which installs in
  Cowork via Settings → Capabilities.
- Keep `work/` out of git (it's the per-paper scratch dir; already in `.gitignore`).

## Design rationale (so changes stay aligned)

- **Single column always** — uniform, linear reading and annotation, independent of the
  source's column count.
- **Never-cropped figures** — the dominant failure mode of naive converters; the
  extractor over-includes then trims, and a verifier subagent re-checks every figure
  against its full-page render, looping until clean.
- **Source-only full names** — references reflect what the paper provides, never
  abbreviating a given name and never fetching from the network.
- **Scripts vs. agent** — anything reproducible is a script (cheap, testable, reusable);
  anything that needs reading/judgement stays in the prose so the model can do it well.
