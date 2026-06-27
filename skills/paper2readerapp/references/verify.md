# verify.md — verification subagent + the OODA repair loop

A reader app is only useful if it is faithful and complete. After building (Step 8),
run a verification pass and **loop until there are no defects**. Prefer a dedicated
verifier subagent (a fresh set of eyes that did not author the body), because the
author tends to be blind to its own omissions.

## What the verifier checks

Give the verifier: the source (PDF page images in `work/pages/`, and the `.tex`/`.bib`
if present), the built `work/<slug>.html`, the `work/figures_manifest.json`, and this
checklist. It should return a concrete defect list (id/section + what's wrong), not a
vibe.

1. **Completeness of text.** Every section and subsection in the source appears in the
   app, in the right order, with no dropped paragraphs, equations, or footnotes. Spot-check
   3–5 pages word-for-word against `work/pages/`.
2. **Single column.** The whole paper reads as one column; a 2-column source was merged
   in correct reading order (no interleaved or out-of-order text).
3. **Figures & tables present and NOT cropped.** For every `primary` figure/table:
   open `work/figures/<id>.png` (or the source image) and the corresponding
   `work/pages/page-NN.png`; confirm the cropped image contains the WHOLE figure —
   all panels, axis labels, axis titles, legends, colorbars, and (for tables) every
   row and both rules. Confirm nothing from a neighbouring figure or body text leaked
   in. List any clipped/over-included/wrong-page/missing figures.
4. **Captions** are present as real text under each figure and match the source.
5. **Citations.** In-text `<cite>` keys resolve; the reference list is complete and in
   the paper's style; **author names are full** (no first name abbreviated that the
   source gives in full).
6. **Math** renders (no raw `$...$` leaking as text, no MathJax "undefined control
   sequence"); paper-specific macros were registered.
7. **Annotations.** A pink highlight tour exists and is comprehensive; clicking a
   highlight shows a sidenote; section/subsection summaries exist for everything except
   Introduction/Related-Work/Conclusion; the two note types don't overlap.
8. **Interaction smoke** (if Node available): the page loads with no JS console errors;
   Next/Prev/Reset/Back, citation popovers, and heading summaries all fire. A jsdom
   load harness is enough (see `references/pipeline.md`).

## The loop (Observe → Orient → Decide → Act)

For each defect:
- **Figure clipped / wrong** → add an entry to `work/fig_overrides.json` and re-run
  `extract_figures.py --overrides …` (see `references/figures.md`), re-pack, rebuild.
- **Missing/garbled text** → re-transcribe that page (PDF path) or fix the body HTML
  from the `.tex`; rebuild.
- **Bad/short reference name** → fix in `refs.json` using the source's printed name
  (never invent or fetch); rebuild.
- **Math not rendering** → add the macro to `work/macros.json` or fix the LaTeX; rebuild.
- **Thin annotations** → add highlights/summaries; rebuild.

Rebuild, then **re-verify the items you changed** (and a quick global pass). Stop when
the verifier returns an empty defect list. Don't declare done while any figure is still
flagged `suspicious` and unreviewed.

## Why a subagent and a loop (not one pass)

Papers are long and the failure modes are easy to miss in a single read. A subagent
verifier with an explicit checklist catches the systematic problems (a whole subsection
dropped, every table off by one row, a 2-column page interleaved), and the OODA loop is
cheap because each fix is local (one figure, one page, one note) and rebuilding is fast.
