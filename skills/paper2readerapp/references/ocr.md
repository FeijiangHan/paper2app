# ocr.md — vision transcription of a PDF-only paper (no external OCR)

When there is no LaTeX source, you reconstruct the paper by **reading the rendered
page images yourself** — you are a strong vision + OCR model, so do not call any
external OCR tool or library. Transcribe one page image at a time, ideally by
spawning one subagent per page (or per 2–3 pages) so it goes fast and each transcript
is focused.

## Setup

```bash
python scripts/render_pages.py --pdf work/paper.pdf --out work/pages --dpi 200
```
This writes `work/pages/page-01.png`, `page-02.png`, … Use `--dpi 250` if the text is
small or dense.

## Per-page subagent instructions (give this to each subagent)

> Read the image at `work/pages/page-NN.png` and transcribe it to faithful Markdown.
> Requirements:
> - **Reading order, single column.** If the page is two-column, output the LEFT
>   column top-to-bottom, then the RIGHT column — as one linear flow. Never interleave
>   columns. Respect content that spans both columns (full-width titles, figures,
>   tables) at its proper place.
> - **Headings**: mark section/subsection headings with `#`/`##`/`###` and keep their
>   numbers ("3.1 Method").
> - **Math**: transcribe every equation and inline symbol as LaTeX (`$...$`, `$$...$$`).
>   Expand unusual notation faithfully; don't paraphrase math.
> - **Figures/tables**: where a figure or table appears, emit a placeholder line
>   `[[FIGURE: Figure N — caption text verbatim]]` or `[[TABLE: Table N — caption]]`,
>   and transcribe the full caption. Do NOT try to redraw the figure.
> - **Citations**: keep in-text citation call-outs as written, e.g. `(Smith et al., 2021)`
>   or `[12]`. List the reference entries verbatim when you reach the References section —
>   **preserve author names exactly as printed; do not abbreviate or expand them.**
> - **Footnotes**: transcribe and attach as `> footnote: …` near their marker.
> - Preserve emphasis, lists, and inline code. Ignore running headers/footers and page
>   numbers. Output only the Markdown transcript for this page.

## Merging

Concatenate page transcripts in order into `work/paper.md`. Then:
- stitch paragraphs/sentences split across a page or column break (a sentence that ends
  mid-line at the bottom of one page continues at the top of the next);
- de-duplicate repeated running headers/footers if any slipped through;
- resolve the figure/table placeholders to the images from `extract_figures.py`
  (match by "Figure N"/"Table N");
- build `refs.json` from the verbatim reference list (same shape as `parse_bib.py`
  output: `{refs:{key:{full,short,year,url}}, order:[...]}`), keeping names as printed.

From `work/paper.md` you then author `work/body.html` per `references/authoring.md`
(single column, `<cite>`, `<figure data-fig>`, math, headings with ids).

## Quality bar

The verification step (Step 9) will compare your transcript against the page images.
Missing paragraphs, dropped equations, scrambled column order, or truncated reference
names are the usual defects — fix by re-transcribing the offending page (a fresh
subagent, told what was wrong) and re-merging.
