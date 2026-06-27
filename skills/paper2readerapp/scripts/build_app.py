#!/usr/bin/env python3
"""build_app.py — assemble the final standalone reader app by filling the template.

Placeholders filled:
  <!--BODY-->     the single-column paper body HTML (sections, math, <figure>, <cite>, <mark>)
  /*REFS*/        refs JSON  ->  {key:{full,short,year,url}}
  /*ORDER*/       refs order (alphabetical key list)
  /*FIGS*/        figs JSON  ->  {id:dataURL}
  /*SUMMARIES*/   section summaries {headingId:{t,b:[...]}}  (optional; default {})
  /*FONTVARS*/    CSS overrides --serif/--mono from detect_fonts (optional)
  __TITLE__ __VENUE__ __RUNAUTH__   metadata text
  __NAV_AUTHORS__  top-navbar authors (et-al shortened for >2)
  __ARXIV_HTML__   optional arXiv outbound link for the top navbar
Usage:
  python build_app.py --template assets/template.html --body body.html --refs refs.json \
     --figs figs.json [--summaries summaries.json] [--fonts fonts.json] [--macros macros.json] \
     --title "Paper Title" [--venue "arXiv"] [--authors "A. Author, B. Author"] \
     [--arxiv 2604.05018] --out app.html"""
import argparse, json, html, re
def nav_authors(authors):
    auths=[x.strip() for x in re.split(r',|\band\b|&', authors) if x.strip()]
    if not auths: return ''
    if len(auths)==1: return auths[0]
    if len(auths)==2: return auths[0]+' and '+auths[1]
    return auths[0]+' et al.'       # et-al shortening for >2 authors
def arxiv_link(s):
    if not s: return ''
    m=re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', s)
    aid=m.group(1) if m else s.strip()
    return (f'<a class="nav-arxiv" href="https://arxiv.org/abs/{html.escape(aid)}" '
            f'target="_blank" rel="noopener">arXiv:{html.escape(aid)}</a>')
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--template',required=True); ap.add_argument('--body',required=True)
    ap.add_argument('--refs',required=True); ap.add_argument('--figs',required=True)
    ap.add_argument('--summaries',default=None); ap.add_argument('--fonts',default=None)
    ap.add_argument('--macros',default=None, help='JSON {name:expansion} of paper-specific LaTeX macros for MathJax')
    ap.add_argument('--title',required=True); ap.add_argument('--venue',default='')
    ap.add_argument('--authors',default=''); ap.add_argument('--arxiv',default='',
                    help='arXiv id or URL; renders an outbound link in the top navbar')
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    t=open(a.template).read()
    body=open(a.body).read()
    refs=json.load(open(a.refs)); figs=json.load(open(a.figs))
    summ=json.load(open(a.summaries)) if a.summaries else {}
    fontvars=''
    if a.fonts:
        f=json.load(open(a.fonts))
        fontvars=f"--serif:{f['serif']}; --mono:{f['mono']};"
    macros=''
    if a.macros:
        md=json.load(open(a.macros))
        # MathJax tex.macros entries: "name": "expansion"  (or ["expansion", nargs])
        macros=', '.join(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in md.items())
    t=t.replace('/*MACROS*/', macros)
    t=t.replace('<!--BODY-->', body)
    t=t.replace('/*REFS*/', json.dumps(refs.get('refs',refs), ensure_ascii=False))
    t=t.replace('/*ORDER*/', json.dumps(refs.get('order',[]), ensure_ascii=False))
    t=t.replace('/*FIGS*/', json.dumps(figs, ensure_ascii=False))
    t=t.replace('/*SUMMARIES*/', json.dumps(summ, ensure_ascii=False))
    t=t.replace('/*FONTVARS*/', fontvars)
    t=t.replace('__TITLE__', html.escape(a.title))
    t=t.replace('__VENUE__', html.escape(a.venue or 'Paper'))
    t=t.replace('__RUNAUTH__', html.escape(a.authors))
    t=t.replace('__NAV_AUTHORS__', html.escape(nav_authors(a.authors)))
    t=t.replace('__ARXIV_HTML__', arxiv_link(a.arxiv))
    open(a.out,'w').write(t)
    # sanity: warn on any unfilled placeholder
    leftover=[p for p in ['<!--BODY-->','/*REFS*/','/*ORDER*/','/*FIGS*/','/*SUMMARIES*/','/*FONTVARS*/',
                          '/*MACROS*/','__TITLE__','__VENUE__','__RUNAUTH__','__NAV_AUTHORS__','__ARXIV_HTML__'] if p in t]
    print(json.dumps({'out':a.out,'kb':len(t)//1024,'unfilled':leftover}))
if __name__=='__main__': main()
