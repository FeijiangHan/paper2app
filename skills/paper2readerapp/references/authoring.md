# authoring.md — the body HTML contract + how to write highlights & summaries

The template (`assets/template.html`) is a fixed shell with placeholders. Your job
in Steps 6–7 is to produce `work/body.html` (the reading content) and
`work/summaries.json` (the section summaries) using EXACTLY the markup below. The
template's CSS and JS already implement all behavior; if you follow the markup, it
just works.

## 1. Body structure (single column, reading order)

Emit a flat sequence of block elements (the template wraps them in one column):

```html
<h1 class="title">Paper Title</h1>
<p class="byline">First Last, Second Author</p>
<p class="affil">Affiliation · email · short running title</p>

<div class="abstract"><h4>Abstract</h4><p>…abstract text…</p></div>

<h2 id="sec-intro">1 &nbsp; Introduction</h2>
<p>Paragraph text … </p>

<h3 id="sub-method">2.1 &nbsp; A subsection</h3>
<p>…</p>
```

Rules:
- **Always one column.** If the source is 2-column, merge into a single reading flow
  in correct order (left column top-to-bottom, then right column). The OCR step
  (`references/ocr.md`) already returns single-column reading order.
- Justified prose is fine; keep paragraphs as `<p>`. Use `<ol class="contrib">` for
  contribution lists and `<ul class="tight">` for tight bullet lists.
- Footnotes: `<p class="footnote"><b>Label.</b> text…</p>`.
- Verbatim/code/prompts: `<pre class="no-math">…</pre>` (the `no-math` class stops
  MathJax from touching it). **Escape `<`, `>`, `&`** inside `<pre>` as `&lt; &gt; &amp;`.
- Give **every** `<h2>`/`<h3>` a stable, unique `id` (used by summaries and cross-refs).

## 2. Math

Inline `$ … $`, display `$$ … $$` (or `\[ \]`). Keep the source LaTeX. Put any
paper-specific `\newcommand` macros in `work/macros.json` so `build_app.py --macros`
injects them into MathJax (otherwise `\Mgen`-style commands won't render). For
PDF-only papers, the OCR transcribes math as standard LaTeX (expand exotic macros).

## 3. Figures, tables, algorithms

```html
<figure id="fig3" class="wide">
  <img data-fig="fig_figure3" alt="short description">
  <figcaption><span class="lab">Figure 3.</span> Caption text, which MAY contain
  $math$, <code>code</code>, and <cite data-k="key"></cite> citations.</figcaption>
</figure>
```
- `data-fig` must equal the figure id you packed into `work/figs.json` (Step 8). The
  JS sets the `src` to the embedded data URL.
- The caption is **real text** (so it can be searched, styled, and highlighted) — do
  not bake the caption into the image.
- Tables: same `<figure>` pattern with the table image, OR, if the table is simple,
  hand-write an HTML `<table>`. Images are the safe default for complex tables.
- Algorithms: either the `<figure>` image, or typeset with the `.algo` block
  (`<div class="algo"><div class="alab">Algorithm 1 …</div><ol><li>…</li></ol></div>`).

## 4. Citations (author–year, individually clickable)

Write a `<cite>` with comma-separated keys; the JS renders the label and makes EACH
name a separate clickable link that opens a popover with the full reference.

```html
… as shown by <cite data-k="vaswani2017attention,devlin2019bert"></cite>.   (parenthetical)
<cite data-k="vaswani2017attention" data-p="t"></cite> showed that …          (textual)
```
Do not write the visible "(Author, Year)" text yourself — leave `<cite>` empty; it is
filled from `refs.json`. Keys must exist in `refs.json` (Step 4). Add a
`<h2 id="references">References</h2><div id="ref-list"></div>` near the end; the JS
fills the list (alphabetical, full names).

## 5. Internal cross-references (with Back support)

```html
see Figure <a class="xref" data-ref="fig3">3</a> … in Section <a class="xref" data-ref="sec-method">2.1</a>
```
`data-ref` is the target element's `id`. Clicking scrolls there and records the origin
so the navbar **Back** button returns the reader.

## 6. Highlights — the guided tour

Wrap each salient span:

```html
<mark class="hl" data-tour="5" data-title="Test 1 — the quality ladder"
      data-note="Generate k responses at rising quality, grade each, correlate rank with score. Positive is healthy.">
  the actual sentence/phrase from the paper
</mark>
```

- `data-tour` = position in the **best pedagogical order** for understanding the paper.
  It does NOT have to follow document order — a good tour often introduces the core
  idea, then jumps to the precise definition, then to the headline result, etc. Floats
  are allowed to insert a stop between two others (e.g. `data-tour="8.5"`). The JS sorts
  by this number; Reset/Prev/Next walk it; the progress bar shows where each stop sits
  in the paper.
- `data-title` = a short title for the sidenote. `data-note` = 1–3 sentence plain-text
  explanation. **No LaTeX and no double-quotes inside `data-note`/`data-title`** — use
  unicode (ρ, κ, →, −1, ≤, ×, ≈) and single quotes. Optional `data-sec="§2 Methods"`.
- Coverage: be **comprehensive** — enough highlights+notes that a reader could grasp the
  paper from them alone. Typical: ~25–50 stops depending on length. Prefer wrapping
  pure prose; it's fine if a `<cite>` falls inside a `<mark>` (clicks are disambiguated).
- Selection heuristic: the thesis/reframe, each key definition, the method's moving
  parts, the headline results and their caveats, the surprising findings, the practical
  takeaways, and the honest limitations.

## 7. Section summaries — the teal notes

After every `<h2>`/`<h3>` has an `id`, write `work/summaries.json`:

```json
{
  "sec-method": { "t": "§2 · Method", "b": ["First key point.", "Second key point.", "Third."] },
  "sub-foo":    { "t": "2.1 · Foo",    "b": ["…", "…"] }
}
```
- Include **every section and subsection EXCEPT** the Introduction, the Related-Work
  section (and its subsections), and the Conclusion. (The reader already reads those
  in full; summaries add the most value on the substantive middle.)
- `t` is a short heading label; `b` is 2–4 tight bullets in plain text (unicode ok, no
  LaTeX). The JS shows these in a teal sidenote when the heading is clicked; the
  "summary" affordance and the heading→note wiring are automatic for any id present in
  this file.
- Do not summarize purely structural headings (References, Acknowledgements, the
  AI-disclosure) — just omit their ids.

## 8. Title/runhead metadata

`build_app.py` fills `__TITLE__`, `__VENUE__`, `__RUNAUTH__` from its `--title/--venue/
--authors` flags — pass the real paper title, the venue (or "arXiv"), and a short
author list. You don't put these in `body.html` except the visible `<h1 class="title">`
and `<p class="byline">` at the top.

## 9. Quick self-check before building

- every `data-fig` has a matching key in `figs.json`; every `<cite>` key is in `refs.json`;
- every `data-ref` points to an existing `id`; every `data-tour` is unique; `data-note`
  has no `"`; headings that should be summarizable have ids and appear in `summaries.json`.
