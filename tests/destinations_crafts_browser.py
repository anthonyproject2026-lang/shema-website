"""Assert complete sections at all requested widths and capture them."""
import json
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'tests/evidence/destinations-crafts'
OUT.mkdir(parents=True, exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
records = json.loads((ROOT/'images/destinations-crafts/manifest.json').read_text(encoding='utf-8'))
results = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in (320,390,430,1024,1440):
            page = browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            for section in ('landmarks','products'):
                locator = page.locator('#'+section)
                assert locator.locator('[data-media-id]').count()==4
                for image in locator.locator('img').all():
                    image.scroll_into_view_if_needed(); image.evaluate('(i)=>i.decode()')
                page.evaluate('document.fonts.ready')
                data = locator.evaluate('''s=>{
                  const bounded=e=>{const r=e.getBoundingClientRect(); return r.left>=-.5 && r.right<=innerWidth+.5 && e.scrollWidth<=e.clientWidth+1};
                  const complete=[...s.querySelectorAll('[data-media-id]')].every(c=>{
                    const outer=c.getBoundingClientRect();
                    return [...c.querySelectorAll('img,figcaption,h3,p,a')].every(e=>{
                      const r=e.getBoundingClientRect();
                      if(r.top<outer.top-.5 || r.bottom>outer.bottom+.5 || e.scrollHeight>e.clientHeight+1) return false;
                      const range=document.createRange();range.selectNodeContents(e);
                      return [...range.getClientRects()].every(t=>t.left>=outer.left-.5&&t.right<=outer.right+.5&&t.top>=outer.top-.5&&t.bottom<=outer.bottom+.5);
                    });
                  });
                  return {complete,bounded:[...s.querySelectorAll('[data-media-id],figure,figcaption,h3,p,a')].every(bounded),cards:[...s.querySelectorAll('[data-media-id]')].map(c=>({id:c.dataset.mediaId, text:c.innerText, image:c.querySelector('img').naturalWidth, fit:getComputedStyle(c.querySelector('img')).objectFit})), overflow:document.documentElement.scrollWidth>innerWidth};
                }''')
                assert data['complete'] and data['bounded'] and not data['overflow'],data
                expected=records[:4] if section=='landmarks' else records[4:]
                for card,r in zip(data['cards'],expected):
                    assert card['id']==r['id'] and r['caption'] in card['text'] and card['image']>0 and card['fit']=='contain'
                    for link in r['external_links']:
                        anchor=locator.locator(f'a[href="{link["url"]}"]')
                        assert anchor.get_attribute('target')=='_blank'
                        assert anchor.get_attribute('rel')=='noopener noreferrer'
                        assert 'opens in a new tab' in anchor.inner_text()
                locator.screenshot(path=str(OUT/f'{section}-complete-{width}.png'),style='#navbar,#backToTop{visibility:hidden!important}.reveal{opacity:1!important;transform:none!important}')
                results.append(dict(width=width,section=section,**data))
            assert not errors,errors
            page.close()
        browser.close()
    (OUT/'layout.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('PASS: all eight cards, complete captions/images/links and bounded sections at 320/390/430/1024/1440; 10 screenshots.')
finally: server.shutdown()
