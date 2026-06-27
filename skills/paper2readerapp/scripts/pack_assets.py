#!/usr/bin/env python3
"""pack_assets.py — quantise the chosen figure images and base64-embed them so the
final app is a single self-contained HTML file. Reads a mapping of figure-id ->
image path (the manifest's id/image, or your curated choices) and writes figs.json
{ id: dataURL }. Quantisation keeps plots/tables crisp while cutting size ~5x.
Usage: python pack_assets.py --map figmap.json --out figs.json [--maxw 1480] [--colors 128]
  figmap.json: {"fig1":"/path/a.png", "tab1":"/path/b.png", ...}"""
import argparse, base64, json, os
from PIL import Image
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--map',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--maxw',type=int,default=1480); ap.add_argument('--colors',type=int,default=128)
    a=ap.parse_args(); m=json.load(open(a.map)); data={}; total=0
    for fid,path in m.items():
        if not path or not os.path.exists(path): continue
        im=Image.open(path).convert('RGB'); w,h=im.size
        if w>a.maxw: im=im.resize((a.maxw,int(h*a.maxw/w)), Image.LANCZOS)
        q=im.quantize(colors=a.colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        tmp=path+'.q.png'; q.save(tmp, optimize=True)
        b=open(tmp,'rb').read(); os.remove(tmp); total+=len(b)
        data[fid]='data:image/png;base64,'+base64.b64encode(b).decode()
    json.dump(data, open(a.out,'w'))
    print(json.dumps({'figs':len(data),'kb':total//1024,'out':a.out}))
if __name__=='__main__': main()
