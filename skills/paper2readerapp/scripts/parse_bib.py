#!/usr/bin/env python3
"""
parse_bib.py — turn a BibTeX file (or several) into reference records for the
reader app.

Design note on names: the user requirement is to list references with FULL
author names when they are available, and never to abbreviate first names even
if the source paper's bibliography style does. BibTeX `author` fields almost
always carry the full given names even when the rendered PDF prints initials, so
we read the raw field and keep every given name in full. We never reduce a name
to an initial; if the source itself only has an initial, we keep that initial.

Output JSON: { "refs": { key: {full, short, year, url} }, "order": [keys...] }
  full  = formatted reference (HTML, no abstract), full names
  short = inline author-year label, e.g. "Cohen", "Sutton & Barto", "Vaswani et al."

Usage:
  python parse_bib.py --bib paper.bib [paper2.bib ...] --out refs.json
  python parse_bib.py --bib a.bib --cited keys.txt --out refs.json   # restrict to cited keys
"""
import argparse, json, re, html

ACCENTS = {r"\'a":"á",r"\'e":"é",r"\'i":"í",r"\'o":"ó",r"\'u":"ú",r"\'n":"ń",r"\'c":"ć",
           r'\"a':"ä",r'\"o':"ö",r'\"u':"ü",r'\"e':"ë",r"\`e":"è",r"\^o":"ô",r"\^e":"ê",
           r"\~n":"ñ",r"\c c":"ç",r"\v s":"š",r"\v c":"č",r"\o":"ø",r"\aa":"å",r"\ss":"ß"}

def delatex(s):
    if not s: return s
    s = s.replace(r"{\textregistered}","®").replace(r"\textregistered","®")
    s = s.replace(r"{\textquoteright}","’").replace("~"," ")
    for k,v in ACCENTS.items():
        s = s.replace("{"+k+"}",v).replace(k+" ",v).replace(k,v)
    s = re.sub(r"\\(emph|textit|textbf|texttt|textsc|mbox|text)\{([^{}]*)\}", r"\2", s)
    s = s.replace(r"\&","&").replace("\\#","#").replace("\\%","%").replace("\\$","$")
    s = s.replace("{","").replace("}","").replace("--","–")
    return re.sub(r"\s+"," ",s).strip()

def parse_entries(src):
    entries = {}; i = 0; n = len(src)
    while True:
        at = src.find('@', i)
        if at < 0: break
        br = src.find('{', at)
        if br < 0: break
        etype = src[at+1:br].strip().lower()
        if etype in ('comment','preamble','string'):
            i = br + 1; continue
        depth = 1; j = br + 1
        while j < n and depth > 0:
            c = src[j]
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            j += 1
        body = src[br+1:j-1]; comma = body.find(',')
        if comma < 0: i = j; continue
        key = body[:comma].strip()
        entries[key] = (etype, body[comma+1:]); i = j
    return entries

def parse_fields(fs):
    out = {}; i = 0; n = len(fs)
    while i < n:
        m = re.match(r'\s*([A-Za-z0-9_\-]+)\s*=\s*', fs[i:])
        if not m: break
        name = m.group(1).lower(); i += m.end()
        if i >= n: break
        if fs[i] == '{':
            depth = 1; j = i + 1
            while j < n and depth > 0:
                if fs[j] == '{': depth += 1
                elif fs[j] == '}': depth -= 1
                j += 1
            val = fs[i+1:j-1]; i = j
        elif fs[i] == '"':
            j = i + 1
            while j < n and fs[j] != '"': j += 1
            val = fs[i+1:j]; i = j + 1
        else:
            j = i
            while j < n and fs[j] not in ',\n': j += 1
            val = fs[i:j].strip(); i = j
        while i < n and fs[i] in ', \n\t\r': i += 1
        out[name] = ' '.join(val.split())
    return out

def split_authors(a):
    return [x.strip() for x in re.split(r'\s+and\s+', a) if x.strip()] if a else []

def name_parts(a):
    """Return (given_full, family). Keeps given names in full (no initials)."""
    a = a.strip()
    if ',' in a:
        fam, given = a.split(',', 1)
        return delatex(given.strip()), delatex(fam.strip())
    toks = a.split()
    if not toks: return '', ''
    # last token (or 'van der X') is the family name
    return delatex(' '.join(toks[:-1])), delatex(toks[-1])

def family(a):
    return name_parts(a)[1]

def full_author_list(authors):
    formatted = []
    for a in authors:
        given, fam = name_parts(a)
        formatted.append(f"{fam}, {given}".strip().rstrip(',') if given else fam)
    if not formatted: return ''
    if len(formatted) == 1: return formatted[0]
    if len(formatted) == 2: return f"{formatted[0]} & {formatted[1]}"
    return ', '.join(formatted[:-1]) + ', & ' + formatted[-1]

def short_label(authors, title):
    fams = [family(a) for a in authors]
    if not fams:
        return (delatex(title)[:18] or 'Anon')
    if len(fams) == 1: return fams[0]
    if len(fams) == 2: return f"{fams[0]} & {fams[1]}"
    return f"{fams[0]} et al."

def esc(s): return html.escape(s or '')

def format_full(f):
    authors = split_authors(f.get('author', '') or f.get('editor', ''))
    yr = delatex(f.get('year', 'n.d.'))
    title = esc(delatex(f.get('title', '')))
    bits = []
    al = full_author_list(authors)
    if al: bits.append(f"<span class='r-au'>{esc(al)}</span>")
    bits.append(f"({esc(yr)}).")
    if title: bits.append(f"<span class='r-ti'>{title}.</span>")
    venue = ''
    if f.get('journal'):
        v = f"<em>{esc(delatex(f['journal']))}</em>"
        if f.get('volume'): v += f", <em>{esc(delatex(f['volume']))}</em>"
        if f.get('number'): v += f"({esc(delatex(f['number']))})"
        if f.get('pages'):  v += f", {esc(delatex(f['pages']).replace('--','–'))}"
        venue = v + '.'
    elif f.get('booktitle'):
        venue = f"In <em>{esc(delatex(f['booktitle']))}</em>."
    elif f.get('publisher'):
        venue = f"{esc(delatex(f['publisher']))}."
    elif f.get('school') or f.get('institution'):
        venue = f"{esc(delatex(f.get('school') or f.get('institution')))}."
    if venue: bits.append(venue)
    if f.get('eprint'):
        bits.append(f"{esc(f.get('archiveprefix','arXiv'))}:{esc(f['eprint'])}.")
    url = f.get('url', '')
    if not url and f.get('doi'): url = 'https://doi.org/' + f['doi']
    if not url and f.get('eprint'): url = 'https://arxiv.org/abs/' + f['eprint']
    return ' '.join(bits), url, (short_label(authors, f.get('title','')), str(yr))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bib', nargs='+', required=True)
    ap.add_argument('--cited', default=None, help='optional file with one cite key per line')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    src = ''
    for b in args.bib:
        src += open(b, encoding='utf-8', errors='replace').read() + '\n'
    entries = parse_entries(src)
    cited = None
    if args.cited:
        cited = set(x.strip() for x in open(args.cited) if x.strip())
    refs = {}
    for key, (etype, fs) in entries.items():
        if cited is not None and key not in cited:
            continue
        f = parse_fields(fs); f.pop('abstract', None); f['_type'] = etype
        full, url, (short, yr) = format_full(f)
        refs[key] = {'full': full, 'url': url, 'short': short, 'year': yr,
                     '_sort': (family(split_authors(f.get('author',''))[0]).lower()
                               if f.get('author') else delatex(f.get('title','')).lower(), yr)}
    order = sorted(refs, key=lambda k: refs[k]['_sort'])
    for k in refs: refs[k].pop('_sort')
    json.dump({'refs': refs, 'order': order}, open(args.out, 'w'), ensure_ascii=False, indent=0)
    print(json.dumps({'refs': len(refs), 'out': args.out}))

if __name__ == '__main__':
    main()
