#!/usr/bin/env python3
"""detect_fonts.py — read the PDF's embedded fonts (pdffonts) and emit CSS font
stacks that MATCH the source where possible, falling back to a clean, readable
serif when the source font is unknown or unavailable on the reader's machine.

The mapping leans on widely-available system/web fonts so the app looks close to
the paper without bundling font files. Output JSON: {serif, mono, sans, detected, note}.
Usage: python detect_fonts.py --pdf paper.pdf --out fonts.json"""
import argparse, json, subprocess, re, collections
SERIF_MAP = [
  (('palladio','palatino','pagella'),    '"Palatino Linotype","Book Antiqua",Palatino,"URW Palladio L","TeX Gyre Pagella",Georgia,serif'),
  (('times','nimbusrom','termes','tinos','serifa','timesnewroman'), '"Times New Roman",Times,"Tinos","Liberation Serif","TeX Gyre Termes",serif'),
  (('cmr','computermodern','lmroman','latinmodern','cmu','nimbusromno','modern'), '"Latin Modern Roman","CMU Serif","Computer Modern",Georgia,"Times New Roman",serif'),
  (('minion','myriadpro-serif'),         '"Minion Pro","Minion",Georgia,serif'),
  (('charter','bitstreamcharter','xcharter'), '"Charter","Bitstream Charter",Georgia,serif'),
  (('georgia',),                          'Georgia,"Times New Roman",serif'),
  (('garamond','ebgaramond'),             '"EB Garamond",Garamond,Georgia,serif'),
  (('libertine','linuxlibertine'),        '"Linux Libertine","Libertinus Serif",Georgia,serif'),
  (('kepler','utopia','fourier','heuristica'), '"Utopia","Heuristica",Georgia,serif'),
]
SANS_MAP = [
  (('helvetica','nimbussan','arial','heros','texgyreheros','liberation sans'), 'Helvetica,Arial,"Liberation Sans",system-ui,sans-serif'),
  (('cmss','computermodernsans','lmsans'), '"Latin Modern Sans","CMU Sans Serif",system-ui,sans-serif'),
  (('myriad','frutiger','calibri','lato','opensans'), '"Myriad Pro",system-ui,"Segoe UI",Roboto,sans-serif'),
]
MONO_MAP = [
  (('inconsolata',),  '"Inconsolata",ui-monospace,Menlo,Consolas,monospace'),
  (('courier','nimbusmono','cmtt','computermoderntypewriter','lmmono','liberation mono','txtt'),
                      '"Inconsolata","Latin Modern Mono","Liberation Mono",Menlo,Consolas,monospace'),
]
DEFAULT_SERIF='"Palatino Linotype","Book Antiqua",Palatino,"TeX Gyre Pagella",Georgia,serif'
DEFAULT_MONO ='"Inconsolata",ui-monospace,Menlo,Consolas,monospace'
DEFAULT_SANS ='system-ui,"Segoe UI",Helvetica,Arial,sans-serif'
MATHY = ('cmsy','cmmi','cmex','msam','msbm','rsfs','eufm','cmbsy','symbol','stmary','wasy','marvosym','dsrom')
def clean(name):
    name = re.sub(r'^[A-Z]{6}\+','',name)   # strip subset tag
    return name.lower().replace(' ','').replace('-','')
def pick(names, table, default):
    for n in names:
        for keys, stack in table:
            if any(k in n for k in keys):
                return stack, n
    return default, None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pdf',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args()
    try:
        out=subprocess.run(['pdffonts',a.pdf],capture_output=True,text=True).stdout
    except FileNotFoundError:
        out=''
    rows=[l.split() for l in out.splitlines()[2:] if l.strip()]
    names=[clean(r[0]) for r in rows if r]
    text_names=[n for n in names if not any(m in n for m in MATHY)]
    serif,sd = pick(text_names, SERIF_MAP, DEFAULT_SERIF)
    mono,md  = pick(names, MONO_MAP, DEFAULT_MONO)
    sans,nd  = pick(text_names, SANS_MAP, DEFAULT_SANS)
    note = f"matched body≈{sd or 'default'}, mono≈{md or 'default'}" if out else "pdffonts unavailable; using clean defaults"
    json.dump({'serif':serif,'mono':mono,'sans':sans,'detected':text_names[:12],'note':note}, open(a.out,'w'), indent=1)
    print(json.dumps({'serif':sd,'mono':md,'note':note}))
if __name__=='__main__': main()
