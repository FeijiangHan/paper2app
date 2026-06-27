#!/usr/bin/env python3
"""
extract_figures.py — extract figures, tables and algorithms from a PDF as
tightly-cropped-but-NEVER-CUT images.

Why this exists: the naive "crop the colored region" approach silently clips
axis titles, legends and panels that sit outside the plotting area. This script
anchors every crop on its CAPTION (located precisely with pdfplumber), grows the
crop until it hits real whitespace on every side, and refuses to stop at a small
internal gap. It also understands 1- and 2-column layouts so a single-column
figure is not widened into its neighbour, and a full-width (figure*) figure is
captured across the gutter.

It writes:
  <out>/figures/<id>.png        cropped figure images (high-DPI)
  <out>/pages/page-NN.png       full-page renders (for the verifier subagent)
  <out>/figures_manifest.json   one record per figure/table/algorithm

OODA: when the verifier flags a crop as cut or wrong, pass an overrides file
(--overrides) mapping the figure id to explicit bounds/padding/direction and
re-run; only the listed figures are recomputed.

Usage:
  python extract_figures.py --pdf paper.pdf --out work/ [--dpi 300]
  python extract_figures.py --pdf paper.pdf --out work/ --overrides fixes.json
Dependencies: pdfplumber, pillow, numpy, poppler (pdftoppm).
"""
import argparse, json, os, re, subprocess, glob, sys
import numpy as np
from PIL import Image, ImageChops, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True  # some PDFs rasterise to slightly-truncated PNGs

CAP_RE = re.compile(r'^(figure|fig|table|algorithm|alg|scheme|listing)\s*\.?\s*([0-9]+|[A-Z]\.?[0-9]+|[IVXLC]+)',
                    re.IGNORECASE)

def render_page(pdf, pg, dpi, out):
    base = os.path.join(out, f'_pg{pg}')
    existing = glob.glob(base + '-*.png')
    if not existing:
        subprocess.run(['pdftoppm', '-png', '-r', str(dpi), '-f', str(pg), '-l', str(pg), pdf, base],
                       check=True)
        existing = glob.glob(base + '-*.png')
    return existing[0]

def trim(im, pad=16, thresh=22):
    bg = Image.new('RGB', im.size, (255, 255, 255))
    d = ImageChops.difference(im, bg)
    d = ImageChops.add(d, d, 2.0, -thresh)
    bb = d.getbbox()
    if not bb:
        return im
    l, t, r, b = bb
    return im.crop((max(0, l - pad), max(0, t - pad),
                    min(im.size[0], r + pad), min(im.size[1], b + pad)))

def detect_columns(page):
    """Return (split_x_or_None). split_x is the gutter centre in PDF points."""
    W = page.width
    words = page.extract_words()
    if not words:
        return None
    # coverage of each x bin by word spans
    bins = 200
    cov = np.zeros(bins)
    for w in words:
        a = int(w['x0'] / W * bins); b = int(w['x1'] / W * bins)
        cov[max(0, a):min(bins, b + 1)] += 1
    # look for a near-empty vertical band in the central third
    lo, hi = int(0.34 * bins), int(0.66 * bins)
    band = cov[lo:hi]
    if band.size == 0:
        return None
    j = int(np.argmin(band)) + lo
    # require the gutter to be clearly empty relative to the columns' density
    side = np.median(cov[cov > 0]) if (cov > 0).any() else 0
    if cov[j] <= max(1, 0.06 * side) and side > 4:
        return j / bins * W
    return None

def find_captions(page, pgnum):
    words = page.extract_words()
    lines = {}
    for w in words:
        key = round(w['top'] / 1.5)
        lines.setdefault(key, []).append(w)
    caps = []
    for k, ws in sorted(lines.items()):
        ws_sorted = sorted(ws, key=lambda w: w['x0'])
        joined = ''.join(w['text'] for w in ws_sorted)         # spaces are often stripped
        spaced = ' '.join(w['text'] for w in ws_sorted)
        m = CAP_RE.match(joined) or CAP_RE.match(spaced)
        if not m:
            continue
        x0 = min(w['x0'] for w in ws); x1 = max(w['x1'] for w in ws)
        top = min(w['top'] for w in ws); bot = max(w['bottom'] for w in ws)
        kind = 'table' if joined.lower().startswith('table') else \
               ('algorithm' if joined.lower().startswith(('algorithm', 'alg')) else 'figure')
        label = re.match(r'^[A-Za-z]+\.?\s*[0-9A-Z.]+', spaced)
        labraw = label.group(0) if label else spaced[:12]
        # Distinguish a real caption from an in-text reference ("Figure 3 shows ...").
        # A caption's number is followed by a separator, a digit, or a Capitalised word;
        # a body reference continues the sentence with a lowercase word.
        rest = spaced[len(labraw):]
        mrest = re.match(r'^\s*([A-Za-z])', rest)  # \s* — pdfplumber may strip the space
        body_ref = bool(mrest and mrest.group(1).islower())
        caps.append({'page': pgnum, 'kind': kind, 'x0': x0, 'x1': x1, 'top': top, 'bottom': bot,
                     'label': labraw.strip(), 'text': spaced[:260], 'body_ref': body_ref})
    return caps

def column_xrange(page, cap, split):
    words = page.extract_words()
    bx0 = min(w['x0'] for w in words); bx1 = max(w['x1'] for w in words)
    if split is None:
        return bx0, bx1
    spans_gutter = cap['x0'] < split - 10 and cap['x1'] > split + 10
    if spans_gutter:
        return bx0, bx1
    if (cap['x0'] + cap['x1']) / 2 < split:
        return bx0, min(bx1, split - 6)
    return max(bx0, split + 6), bx1

def ink_rows(arr, x0px, x1px):
    sub = arr[:, x0px:x1px]
    ink = (sub.max(2) < 170)
    return ink.sum(1), (x1px - x0px)

def crop_one(pageimg, page, cap, split, dpi, ov=None):
    sc = dpi / 72.0
    im = Image.open(pageimg).convert('RGB')
    Wpx, Hpx = im.size
    arr = np.asarray(im).astype(int)
    # x range (points -> px)
    cx0, cx1 = column_xrange(page, cap, split)
    x0px = max(0, int(cx0 * sc) - int(8 * sc / 72 * 72)); x1px = min(Wpx, int(cx1 * sc) + 4)
    x0px = max(0, int(cx0 * sc) - 6); x1px = min(Wpx, int(cx1 * sc) + 6)
    if ov and 'x0' in ov: x0px = int(ov['x0'] * sc)
    if ov and 'x1' in ov: x1px = int(ov['x1'] * sc)
    rowink, w = ink_rows(arr, x0px, x1px)
    empty = rowink < (w * 0.004)
    cap_top = int(cap['top'] * sc)
    cap_bot = int(cap['bottom'] * sc)
    direction = (ov.get('direction') if ov else None) or \
                ('below' if cap['kind'] in ('table', 'algorithm') else 'above')
    minfig = int(0.05 * Hpx)
    def empty_runs(lo, hi):
        gaps = []; y = lo
        while y < hi:
            if empty[y]:
                s = y
                while y < hi and empty[y]:
                    y += 1
                gaps.append((s, y))
            else:
                y += 1
        return gaps
    def grow(direction):
        # The figure is bounded from the body/header by the LARGEST whitespace gap on
        # its side of the caption — never by the first small internal gap (which would
        # clip legends, axis titles or a second panel). This is the key to "never cut".
        if direction == 'above':
            lo = int(0.035 * Hpx); hi = max(lo + 1, cap_top - 2)
            gaps = [g for g in empty_runs(lo, hi) if g[1] < hi - minfig and (g[1] - g[0]) >= 3]
            if gaps:
                g = max(gaps, key=lambda t: t[1] - t[0]); return g[1] - 2, hi
            return int(0.06 * Hpx), hi
        else:
            lo = min(Hpx - 2, cap_bot + 2); hi = int(0.965 * Hpx)
            gaps = [g for g in empty_runs(lo, hi) if g[0] > lo + minfig and (g[1] - g[0]) >= 3]
            if gaps:
                g = max(gaps, key=lambda t: t[1] - t[0]); return lo, g[0] + 2
            return lo, int(0.94 * Hpx)
    y0, y1 = grow(direction)
    # If the chosen side is basically empty, the caption sits on the other side.
    if (y1 - y0) < 0.05 * Hpx:
        y0b, y1b = grow('below' if direction == 'above' else 'above')
        if (y1b - y0b) > (y1 - y0):
            y0, y1 = y0b, y1b
    if ov and 'y0' in ov: y0 = int(ov['y0'] * sc)
    if ov and 'y1' in ov: y1 = int(ov['y1'] * sc)
    pad = int((ov.get('pad', 0) if ov else 0) * sc)
    y0 = max(0, y0 - pad); y1 = min(Hpx, y1 + pad)
    crop = im.crop((x0px, y0, x1px, y1))
    # uncropped self-check: are the four borders whitespace? (content must not touch edges)
    a2 = np.asarray(crop.convert('L'))
    def border_ink(line): return (line < 170).mean()
    touch = {'top': border_ink(a2[0]) > 0.02, 'bottom': border_ink(a2[-1]) > 0.02,
             'left': border_ink(a2[:, 0]) > 0.02, 'right': border_ink(a2[:, -1]) > 0.02}
    crop = trim(crop)
    touch = {k: bool(v) for k, v in touch.items()}
    return crop, {'x_px': [int(x0px), int(x1px)], 'y_px': [int(y0), int(y1)], 'direction': direction,
                  'edge_touch': touch, 'suspicious': bool(any(touch.values()))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dpi', type=int, default=300)
    ap.add_argument('--overrides', default=None)
    ap.add_argument('--list-only', action='store_true')
    args = ap.parse_args()
    import pdfplumber
    os.makedirs(os.path.join(args.out, 'figures'), exist_ok=True)
    os.makedirs(os.path.join(args.out, 'pages'), exist_ok=True)
    overrides = json.load(open(args.overrides)) if args.overrides else {}

    pl = pdfplumber.open(args.pdf)
    manifest = []
    counters = {}
    tmp = os.path.join(args.out, '_pgtmp'); os.makedirs(tmp, exist_ok=True)
    for i, page in enumerate(pl.pages):
        caps = find_captions(page, i + 1)
        if not caps:
            continue
        split = None; pageimg = None
        if not args.list_only:                          # list-only needs no rendering
            split = detect_columns(page)
            pageimg = render_page(args.pdf, i + 1, args.dpi, tmp)
        for cap in caps:
            counters[cap['kind']] = counters.get(cap['kind'], 0) + 1
            base = re.sub(r'[^a-z0-9]+', '', cap['label'].lower()) or f"{cap['kind']}{counters[cap['kind']]}"
            fid = f"{cap['kind'][:3]}_{base}"
            rec = {'id': fid, 'kind': cap['kind'], 'label': cap['label'], 'page': i + 1,
                   'caption': cap['text'], 'body_ref': cap.get('body_ref', False)}
            if args.list_only:
                manifest.append(rec); continue
            crop, meta = crop_one(pageimg, page, cap, split, args.dpi, overrides.get(fid))
            outp = os.path.join(args.out, 'figures', fid + '.png')
            crop.save(outp)
            rec.update(meta); rec['image'] = outp; rec['size'] = list(crop.size)
            manifest.append(rec)
    # full-page renders for the verifier (lower DPI is fine; skip in list-only mode)
    if not args.list_only:
        for i in range(len(pl.pages)):
            dst = os.path.join(args.out, 'pages', f'page-{i+1:02d}.png')
            if not os.path.exists(dst):
                src = render_page(args.pdf, i + 1, 150, tmp)
                Image.open(src).convert('RGB').save(dst)
    pl.close()
    # de-duplicate ids: body-text references to "Figure N" can also match the caption
    # regex. Keep the best crop per id (prefer not-suspicious, then largest), and mark
    # the rest as duplicates so the builder/verifier can ignore them.
    from collections import defaultdict
    groups = defaultdict(list)
    for m in manifest:
        groups[m['id']].append(m)
    for gid, items in groups.items():
        if len(items) < 2:
            items[0].setdefault('primary', True); continue
        items.sort(key=lambda m: (not m.get('body_ref', False), not m.get('suspicious', False),
                                   (m.get('size') or [0, 0])[0] * (m.get('size') or [0, 0])[1]),
                   reverse=True)
        for k, m in enumerate(items):
            m['primary'] = (k == 0)
            if k:
                m['duplicate_of'] = gid
    json.dump(manifest, open(os.path.join(args.out, 'figures_manifest.json'), 'w'), indent=1)
    susp = [m['id'] for m in manifest
            if m.get('primary', True) and (m.get('suspicious') or m.get('body_ref'))]
    print(json.dumps({'figures': len(manifest), 'suspicious': susp,
                      'manifest': os.path.join(args.out, 'figures_manifest.json')}, indent=1))

if __name__ == '__main__':
    main()
