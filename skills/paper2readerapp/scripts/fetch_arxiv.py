#!/usr/bin/env python3
"""fetch_arxiv.py — given an arXiv id or URL, download BOTH the PDF and the LaTeX
e-print source, unpack the source, and locate the main .tex, the .bib file(s),
and any figure image files shipped in the source.

Prefer the source for text/structure; use the PDF for figure extraction and font
detection. If the network is unavailable, this prints an error and the skill
should ask the user to provide the files directly.

Usage: python fetch_arxiv.py --id 2505.08775 --out work/
       python fetch_arxiv.py --id https://arxiv.org/abs/2505.08775 --out work/
Prints JSON {id, pdf, source_dir, main_tex, bib_files, image_files}."""
import argparse, json, os, re, tarfile, gzip, urllib.request, glob, shutil
UA={'User-Agent':'paper2readerapp/1.0 (research reader; contact: user)'}
def norm_id(s):
    s=s.strip()
    m=re.search(r'arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(v[0-9]+)?)', s)
    if m: return m.group(1)
    m=re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', s)
    if m: return m.group(1)
    return s  # old-style id like cs/0309040
def get(url, dest):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(dest,'wb') as f:
        shutil.copyfileobj(r,f)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--id',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    aid=norm_id(a.id); src=os.path.join(a.out,'source'); os.makedirs(src,exist_ok=True)
    pdf=os.path.join(a.out,'paper.pdf')
    res={'id':aid,'pdf':None,'source_dir':src,'main_tex':None,'bib_files':[],'image_files':[]}
    try:
        get(f'https://arxiv.org/pdf/{aid}.pdf', pdf); res['pdf']=pdf
    except Exception as e:
        res['pdf_error']=str(e)
    eprint=os.path.join(a.out,'eprint.tar')
    try:
        get(f'https://arxiv.org/e-print/{aid}', eprint)
        # could be a tar, a gzip'd tar, or a single gzip'd tex
        try:
            with tarfile.open(eprint) as tf: tf.extractall(src)
        except tarfile.ReadError:
            with gzip.open(eprint,'rb') as g: data=g.read()
            open(os.path.join(src,'main.tex'),'wb').write(data)
    except Exception as e:
        res['source_error']=str(e)
    texs=glob.glob(os.path.join(src,'**','*.tex'), recursive=True)
    def is_main(p):
        try: t=open(p,encoding='utf-8',errors='replace').read()
        except: return False
        return '\\documentclass' in t and '\\begin{document}' in t
    mains=[p for p in texs if is_main(p)]
    res['main_tex']= (mains[0] if mains else (texs[0] if texs else None))
    res['bib_files']=glob.glob(os.path.join(src,'**','*.bib'), recursive=True)
    res['image_files']=[p for ext in ('pdf','png','jpg','jpeg','eps','svg')
                        for p in glob.glob(os.path.join(src,'**',f'*.{ext}'), recursive=True)
                        if os.path.basename(p)!='paper.pdf']
    print(json.dumps(res, indent=1))
if __name__=='__main__': main()
