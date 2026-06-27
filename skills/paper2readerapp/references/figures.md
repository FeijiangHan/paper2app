# figures.md — extracting figures & tables that are NEVER cropped

The single most common failure when turning a paper into a reader is a clipped
figure: the crop keeps the colored plot area but loses the axis title, legend, a
second panel, or the bottom row of a table. This file explains how `extract_figures.py`
avoids that and how to repair the rare miss.

## Choosing the image source

- **Figure shipped as an image file** in the LaTeX source (`\includegraphics{plot.pdf}`
  / `.png` / `.jpg`): use that file directly — it is the highest fidelity and is never
  cropped. (A vector `.pdf`/`.eps` figure can be rasterized: `pdftoppm -png -r 300 plot.pdf out`.)
- **Figure that exists only in the PDF** (drawn with TikZ/pgfplots, or any figure when
  the input is a PDF): extract from the PDF with the script below. The non-cropping
  guarantee and Step-9 verification apply to all of these.

When a figure exists both as a source file and in the PDF, prefer the source file.

## Running the extractor

```bash
python scripts/extract_figures.py --pdf work/paper.pdf --out work/ --dpi 300
```
Outputs:
- `work/figures/<id>.png` — one cropped image per caption found;
- `work/pages/page-NN.png` — full-page renders (the verifier compares against these);
- `work/figures_manifest.json` — one record per caption.

Manifest fields you care about:
- `id` (e.g. `fig_figure3`, `tab_table1`, `alg_algorithm1`), `kind`, `label`, `page`,
  `caption`, `size`, `image`;
- `primary` — **use only `primary: true` records**. Body-text references to "Figure N"
  and duplicate captions are kept but marked `primary: false` (`duplicate_of`/`body_ref`);
- `suspicious` — the crop's border had ink (it *might* be clipped or include a neighbour)
  — review these visually;
- `edge_touch`, `direction`, `x_px`, `y_px` — geometry for debugging/overrides.

## How it avoids cropping (so you trust it, and know its limits)

It anchors each crop on the **caption** (located exactly with pdfplumber), then:
1. picks the caption's column (1- vs 2-column auto-detected; full-width `figure*` spans
   the gutter);
2. finds the figure on the correct side (above the caption for figures, below for
   tables/algorithms);
3. sets the far edge at the **largest whitespace gap** between the figure and the
   body/header — never the first small internal gap — so legends, axis titles and extra
   panels stay in;
4. trims the surrounding whitespace and checks all four borders are clear.

Limits: very tight figure-to-text spacing, or a figure split by a gap larger than the
float separation, can still mislead it. That's what verification + overrides are for.

## Repair loop (OODA) for a flagged or wrong crop

After Step 9 the verifier may report a figure as clipped, too tall (grabbed a neighbour),
or wrong page. Fix it without touching code by passing an overrides file and re-running:

```json
// work/fig_overrides.json  — units are PDF POINTS (72/in); omit fields you don't need
{
  "fig_figure6": { "pad": 6 },
  "tab_table1":  { "direction": "below" },
  "fig_figure9": { "y0": 120, "y1": 360 },
  "fig_figure4": { "x0": 54, "x1": 290 }
}
```
```bash
python scripts/extract_figures.py --pdf work/paper.pdf --out work/ --dpi 300 \
  --overrides work/fig_overrides.json
```
Only the listed ids are recomputed with your bounds; everything else is unchanged.
Re-verify. To read coordinates, render the page with a ruler or open
`work/pages/page-NN.png` and estimate (points = pixel ÷ dpi × 72).

Tip: when in doubt, **over-include** — a little extra whitespace around a figure is
harmless; a clipped axis title is not. `trim()` removes the slack.

## Build map

For Step 8, write `work/figmap.json` mapping the figure id used in `body.html`
(`data-fig`) to the chosen image path (a source file, or `work/figures/<id>.png`):

```json
{ "fig_figure1": "work/figures/fig_figure1.png", "fig3": "work/source/figs/plot3.pdf.png" }
```
You may rename ids to friendly ones (`fig3`, `tab1`) as long as `data-fig` in the body,
the key in `figmap.json`, and the packed `figs.json` all agree.
