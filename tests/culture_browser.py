"""Check actual culture media geometry and capture complete previews at five widths."""
import json
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests/evidence/culture-expansion'
OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
records=json.loads((ROOT/'images/culture/manifest.json').read_text(encoding='utf-8'))
results=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (320,390,430,1024,1440):
            page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            for image in page.locator('#culture img').all():
                image.scroll_into_view_if_needed()
                image.evaluate('(i)=>i.decode()')
            page.evaluate('document.fonts.ready')
            data=page.locator('#culture').evaluate('''section=>{
              const bounded=e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+.5&&e.scrollWidth<=e.clientWidth+1};
              return {images:[...section.querySelectorAll('img')].map(i=>({src:i.currentSrc,width:i.naturalWidth,height:i.naturalHeight,displayHeight:i.getBoundingClientRect().height,fit:getComputedStyle(i).objectFit})), bounded:[...section.querySelectorAll('.culture-item,.culture-video-card,figcaption,a')].every(bounded), overflow:document.documentElement.scrollWidth>innerWidth};
            }''')
            assert len(data['images'])==8 and data['bounded'] and not data['overflow'],data
            assert all(i['width']>0 and i['height']>0 and i['displayHeight']>=145 and i['fit']=='contain' for i in data['images']),data
            from PIL import Image
            for item in data['images']:
                with Image.open(ROOT/item['src'].split(f':{server.server_port}/')[1]) as asset:
                    assert asset.width in (480,800,1024)
            assert not errors,errors
            assert page.locator('.culture-video-card').count()==8
            for link,record in zip(page.locator('.culture-video-card a').all(),records):
                assert link.get_attribute('href')==record['video_url']
                assert 'Watch on Kerala Tourism' in link.inner_text()
            style='#navbar, #backToTop { visibility:hidden !important; } .reveal {opacity:1 !important;transform:none !important;}'
            page.locator('#culture').screenshot(path=str(OUT/f'culture-complete-{width}.png'),style=style)
            page.locator('.culture-video-grid').screenshot(path=str(OUT/f'video-cards-{width}.png'),style=style)
            page.goto(f'http://127.0.0.1:{server.server_port}/media-credits.html')
            assert page.locator('.media-credit').count()==8
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(OUT/f'credits-{width}.png'),full_page=True)
            results.append(dict(viewport=width,**data))
            page.close()
        browser.close()
    (OUT/'layout.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Culture: all 8 photographs and 8 video cards passed at 320, 390, 430, 1024, 1440px; 15 complete previews captured.')
finally:
    server.shutdown()
