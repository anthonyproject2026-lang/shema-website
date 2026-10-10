"""Geometry and input regression. Run: python tests/carousel_regression.py

Optional --baseline records every failure and before screenshots; --url tests a
reachable deployed site read-only. Touch uses Chromium's real touch input API.
"""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tests/evidence/carousel'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--baseline', action='store_true')
parser.add_argument('--url')
args = parser.parse_args()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
results = []
failures = []
GEOMETRY = """index => {
 const v=document.querySelector('#carouselViewport'), t=document.querySelector('#carouselTrack');
 const cards=[...t.children], card=cards[index], r=card.getBoundingClientRect(), vr=v.getBoundingClientRect();
 const left=vr.left+v.clientLeft, right=vr.right-v.clientLeft;
 const inside=e=>{const b=e.getBoundingClientRect();return b.left>=r.left-.5&&b.right<=r.right+.5&&b.top>=r.top-.5&&b.bottom<=r.bottom+.5&&e.scrollHeight<=e.clientHeight+1&&e.scrollWidth<=e.clientWidth+1};
 const range=document.createRange();range.selectNodeContents(card.querySelector('p'));
 const textFits=[...range.getClientRects()].every(b=>b.left>=r.left&&b.right<=r.right+.5&&b.top>=r.top&&b.bottom<=r.bottom+.5);
 const controls=[...document.querySelectorAll('#keralaCarousel button')];
 return {title:card.querySelector('h3').textContent, viewportWidth:right-left,cardWidth:r.width,
 delta:r.left-left, gap:getComputedStyle(t).columnGap, transform:getComputedStyle(t).transform,
 aligned:Math.abs(r.left-left)<.5&&Math.abs(r.right-right)<.5,
 noStrip:cards.every((e,i)=>i===index||Math.min(e.getBoundingClientRect().right,right)-Math.max(e.getBoundingClientRect().left,left)<=.5),
 captionFits:[...card.querySelectorAll('.kerala-card-tag,h3,p')].every(inside)&&textFits,
 controlsFit:controls.every(e=>{const b=e.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.width>=24&&b.height>=24}),
 controlsClear:controls.every(e=>{const b=e.getBoundingClientRect();return Math.min(b.right,r.right)-Math.max(b.left,r.left)<=.5||Math.min(b.bottom,r.bottom)-Math.max(b.top,r.top)<=.5}),
 counter:document.querySelector('.carousel-counter').textContent,
 widths:cards.map(e=>e.getBoundingClientRect().width)};
}"""
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in (320,390,430,1024,1440):
   for motion in ('reduce','no-preference'):
    page=browser.new_page(viewport={'width':width,'height':900},has_touch=True,reduced_motion=motion)
    page.goto(args.url or f'http://127.0.0.1:{server.server_port}/index.html')
    page.evaluate('document.fonts.ready')
    carousel=page.locator('#keralaCarousel'); carousel.scroll_into_view_if_needed()
    page.locator('#carouselPauseBtn').click()
    # Load all existing images before measurements: intrinsic sizing must not
    # change the track stride when a lazy image becomes available.
    page.locator('.kerala-card img').evaluate_all("imgs=>imgs.forEach(i=>i.loading='eager')")
    page.locator('.kerala-card img').evaluate_all("imgs=>Promise.all(imgs.map(i=>i.decode()))")
    total=page.locator('.kerala-card').count()
    longest=page.locator('.kerala-card p').evaluate_all('(ps)=>ps.map(p=>p.textContent.length).indexOf(Math.max(...ps.map(p=>p.textContent.length)))')
    def check(index, action):
     page.wait_for_timeout(550 if motion=='no-preference' else 20)
     data=page.evaluate(GEOMETRY,index)
     data.update(width=width,motion=motion,action=action,index=index)
     results.append(data)
     bad=[key for key in ('aligned','noStrip','captionFits','controlsFit','controlsClear') if not data[key]]
     if data['counter']!=f'{index+1} / {total}': bad.append('counter')
     if bad: failures.append({**data,'failed':bad})
    check(0,'initial')
    index=0
    for selector,step in (('#carouselNext',1),('#carouselPrev',-1)):
     for _ in range(total*2):
      page.locator(selector).click(); index=(index+step)%total; check(index,selector)
    # Native touch gestures, both directions and wrap, every slide.
    cdp=page.context.new_cdp_session(page)
    for step in (1,-1):
     for _ in range(total+1):
      page.locator('#carouselViewport').scroll_into_view_if_needed()
      box=page.locator('#carouselViewport').bounding_box()
      x=box['x']+box['width']*(.8 if step==1 else .2); y=box['y']+50
      cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
      end=x-step*max(65,box['width']*.6)
      cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':end,'y':y}]})
      cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
      index=(index+step)%total; check(index,'swipe')
    for i in range(total):
     page.locator('.carousel-dot').nth(i).click(); check(i,'dot')
     if width<500 and motion=='reduce' and i in (1,longest):
      label='theyyam' if i==1 else 'longest'
      carousel.screenshot(path=str(OUT/f'{"before" if args.baseline else "after"}-{label}-{width}.png'))
      if i==longest and i==1:
       carousel.screenshot(path=str(OUT/f'{"before" if args.baseline else "after"}-longest-{width}.png'))
    carousel.focus();page.keyboard.press('ArrowRight');check(0,'keyboard wrap')
    page.keyboard.press('ArrowLeft');check(total-1,'keyboard previous wrap')
    # Resize while positioned on the last slide.
    page.set_viewport_size({'width':390 if width>=500 else 320,'height':900});check(total-1,'resize')
    page.close()
    print(f'{width}px {motion}: checked all slides, repeated wraps, touch, dots, keyboard, resize')
  browser.close()
finally:
 server.shutdown()
(OUT/f'{"baseline" if args.baseline else "result"}.json').write_text(json.dumps({'checks':len(results),'failures':failures,'measurements':results},indent=2),encoding='utf-8')
print(f'{len(results)} checks; {len(failures)} failures')
assert not failures, f'{len(failures)} carousel failures; see evidence JSON'
