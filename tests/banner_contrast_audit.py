import json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path.cwd();out=ROOT/'tests/evidence/full-mobile';results=[]
def lum(c):
 vs=[v/255 for v in c];return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*k for v,k in zip(vs,(.2126,.7152,.0722)))
with sync_playwright() as p:
 b=p.chromium.launch()
 for width in (320,390,768,1440):
  page=b.new_page(viewport={'width':width,'height':900},reduced_motion='reduce');page.goto((ROOT/'index.html').as_uri());banner=page.locator('.community-banner');banner.scroll_into_view_if_needed();banner.locator('img').evaluate('(i)=>i.decode()')
  data=banner.evaluate("e=>{const b=e.getBoundingClientRect();return [...e.querySelectorAll('h2,p')].map(e=>{const r=document.createRange();r.selectNodeContents(e);return {tag:e.tagName,color:getComputedStyle(e).color,rects:[...r.getClientRects()].map(r=>({x:r.left-b.left,y:r.top-b.top,w:r.width,h:r.height}))}})}")
  path=out/f'contrast-background-{width}.png';banner.screenshot(path=str(path),style='.community-banner-content {visibility:hidden !important}');im=Image.open(path).convert('RGB')
  for item in data:
   alpha=float(item['color'].split(',')[-1].rstrip(')')) if item['color'].startswith('rgba') else 1;ratios=[]
   for r in item['rects']:
    for y in range(max(0,int(r['y'])),min(im.height,int(r['y']+r['h'])+1)):
     for x in range(max(0,int(r['x'])),min(im.width,int(r['x']+r['w'])+1)):
      bg=im.getpixel((x,y));fg=tuple(255*alpha+v*(1-alpha) for v in bg);ratios.append((lum(fg)+.05)/(lum(bg)+.05))
   results.append({'width':width,'tag':item['tag'],'minimumContrast':min(ratios),'color':item['color']})
  page.close()
 b.close()
(out/'contrast.json').write_text(json.dumps(results,indent=2));print(results)

assert all(r["minimumContrast"]>=4.5 for r in results),results
