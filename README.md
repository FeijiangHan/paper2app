# paper2readerapp

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">中文说明</a>
</p>

<p align="center">
  <a href="skills/paper2readerapp/SKILL.md">English skill spec</a> ·
  <a href="skills/paper2readerapp/SKILL.zh-CN.md">中文 skill 规范</a>
</p>

**paper2readerapp** is an open-source Claude skill/plugin that converts research
papers into polished, standalone HTML reading experiences. It is designed for people
who want more than a PDF viewer: a paper becomes a guided, annotated, single-page
reader that can be saved, shared, and hosted like any other static web page.

Give it a **PDF**, a **LaTeX source + `.bib`**, or just an **arXiv id/URL**, and it
produces one self-contained `.html` file with:

- the **whole paper in one reading column** (even if the source is two-column);
- **inline figures and tables**, extracted from the PDF *without ever being cropped*
  (no clipped axis titles, legends, panels, or table rows);
- a **pink-highlighter guided tour** — click a highlight for a plain-language margin
  note; an audio-player-style bottom bar (**Reset / Prev / Next**, a progress scrubber,
  and a **Back** button) walks a curated, non-linear learning path;
- **teal section/subsection summaries** — click a heading for bullet points (every
  section except Introduction, Related Work, and Conclusion);
- **author–year citations** where each name is individually clickable and opens a
  popover with the **full reference** (full author names, no abstract);
- **MathJax** equations and the **source paper's fonts** where detectable.

There's no external OCR dependency: for a PDF-only paper the assistant transcribes the
page images itself, one page at a time, and a verifier pass checks that every page and
figure was captured faithfully — looping until it is.

## Project highlights

- **Official-skill workflow** — the repository is packaged as a Claude plugin with an
  installable skill, deterministic helper scripts, reusable assets, and development
  documentation for maintainers.
- **Agentic where it matters** — mechanical work is delegated to scripts, while paper
  understanding, guided-tour writing, section summarization, and verification remain
  model-driven.
- **Static-web friendly output** — the result is a single HTML artifact that can be
  committed to a website, served from GitHub Pages, attached to a note, or opened
  locally without a backend.
- **Research-reader UX** — highlights, sidenotes, section summaries, citation popovers,
  MathJax equations, source-aware fonts, and a bottom tour controller are integrated
  into one consistent app shell.
- **Verification loop** — the skill explicitly asks the assistant to compare the
  generated reader against the source paper and repair missing text, broken math, bad
  citations, or cropped figures before delivery.

## How it works

1. **Ingest** a PDF, LaTeX project, `.bib`, or arXiv id/URL.
2. **Extract** pages, figures, tables, references, fonts, and paper metadata with the
   scripts under `skills/paper2readerapp/scripts/`.
3. **Author** a single-column body, a pedagogical highlight tour, and clickable section
   summaries using the conventions in the skill references.
4. **Assemble** everything into `assets/template.html` so all images and app data are
   embedded in one HTML file.
5. **Verify and repair** through an OODA loop until the reader is faithful to the source.


## Requirements

- **Claude Code** or **Claude Cowork** (the skill uses subagents and image reading).
- **Python 3** with `pdfplumber pillow numpy`
  (`pip install pdfplumber pillow numpy --break-system-packages`).
- **poppler** (`pdftoppm`, `pdffonts`): `brew install poppler` /
  `apt-get install poppler-utils`.
- Network access only for the arXiv input. (Node is optional, for a load self-test.)

## Install

**Claude Code — via the plugin marketplace (recommended)**
```
/plugin marketplace add delip/paper2readerapp
/plugin install paper2readerapp@paper2readerapp
```

**Claude Code — as a skill you copy in**
```bash
git clone https://github.com/delip/paper2readerapp.git
# available everywhere:
cp -r paper2readerapp/skills/paper2readerapp ~/.claude/skills/paper2readerapp
# …or only inside one project:
cp -r paper2readerapp/skills/paper2readerapp <your-project>/.claude/skills/paper2readerapp
```

**Claude Cowork (desktop)** — open **Settings → Capabilities**, add a skill, and point
it at `paper2readerapp/skills/paper2readerapp`.

## Usage

Once installed, just ask in natural language — you don't need to name the skill:

- "Turn this PDF into an interactive reader." *(attach `paper.pdf`)*
- "Make an app out of arXiv 2310.06825."
- "Convert this LaTeX source + .bib into a single-column reader with highlights."
- "paper2readerapp https://arxiv.org/abs/1706.03762"

It downloads/reads the inputs, extracts the figures, parses the references, writes the
single-column body, authors the highlight tour and section summaries, builds the app,
**verifies** it (pages present, figures uncropped, citations and maths intact), fixes
anything it flags, and hands you the finished `.html`. Open it in any browser.

## Customizing

You can steer the result with a sentence, or by editing one file:

- **Tour length / summary depth** — ask for what you want: *"keep the highlight tour
  concise"* or *"summarize every subsection in depth."* The default is comprehensive.
- **Colors** — the look is controlled by CSS variables near the top of
  `skills/paper2readerapp/assets/template.html`: `--pink` (highlights), `--teal`
  (section summaries), `--link` (citations). Change them to retheme every app this
  skill builds.
- **Fonts** — by default the app matches the source paper's fonts and falls back to a
  clean serif. To force one theme for every paper, ask for it (*"use the same clean
  serif for all papers"*).
- **Which sections get summaries** — Introduction, Related Work, and Conclusion are left
  un-summarized by design; ask if you want that changed for a particular paper.

## What makes it different

- **Always single column** — papers are easier to read and annotate as one linear flow.
- **Figures are never cropped** — the most common failure of naive paper→reader tools.
  Every figure extracted from a PDF is grown to surrounding whitespace and then verified,
  so legends, axis titles, panels, and full tables stay intact.
- **Full author names** — references use the names exactly as the source provides them
  and never abbreviate a given name (LaTeX `.bib` files usually carry full names even
  when the printed PDF shows initials). Nothing is looked up online.

## Personal workflow example

One practical workflow is to use this skill with a personal GitHub Pages site. My
personal website is hosted on GitHub, so I can ask Codex/Claude Code to take an arXiv
paper link, run this skill, generate a standalone HTML reader, and save it under a
chosen path in my homepage repository. After committing and pushing that file, I can
open my website and read the interactive paper app directly from the browser. This
works especially well because the generated app is static and self-contained.

## Skill specifications

- [English skill spec](skills/paper2readerapp/SKILL.md) — default skill for generating
  English reader apps.
- [中文 skill 规范](skills/paper2readerapp/SKILL.zh-CN.md) — Chinese skill variant for
  generating Chinese reader apps.

## Extending this skill

Want to change how the skill works under the hood — the figure extraction, the app
template's HTML/CSS/JS, the reference parsing, the orchestration, or packaging a new
release? See **[SKILL_DEV_README.md](SKILL_DEV_README.md)** for the repository layout,
architecture, the template placeholder contract, testing, and publishing details.
