#!/usr/bin/env python3
"""render_pages.py — render every PDF page to a PNG (for VLM OCR and verification).
Usage: python render_pages.py --pdf paper.pdf --out work/pages [--dpi 200]
Needs poppler (pdftoppm). Prints JSON {pages:[paths], count}."""
import argparse, glob, os, subprocess, json
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--dpi', type=int, default=200)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    subprocess.run(['pdftoppm','-png','-r',str(a.dpi),a.pdf,os.path.join(a.out,'page')], check=True)
    pages = sorted(glob.glob(os.path.join(a.out,'page-*.png')))
    print(json.dumps({'count':len(pages),'pages':pages}, indent=1))
if __name__ == '__main__': main()
