"""Supplemental readable screenshots, touch geometry and font-network evidence."""
import json
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tests/evidence/full-mobile';server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();results=[]
try:
 with sync_playwright() as p:
  for engine in ('chromium','webkit'):
   b=getattr(p,engine).launch()
   for w,h,scale in ((390,900,1),(1440,900,1),(667,375,1),(320,900,2),(1440,900,2)):
    page=b.new_page(viewport={'width':w,'height':h},reduced_motion='reduce',has_touch=True);failed=[]
    page.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure}))
    page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.evaluate('document.fonts.ready')
    if scale==2:page.add_style_tag(content='html{font-size:200% !important}')
    for section in page.locator('main>section,footer').all():
     section.scroll_into_view_if_needed()
     section.locator('img').evaluate_all("es=>{es.forEach(i=>i.loading='eager');return Promise.all(es.map(i=>i.decode().catch(()=>{})))}")
    controls=page.locator('button,.hero-buttons a,.cta-buttons a,.event-video-link,.footer-socials a').evaluate_all("es=>es.filter(e=>e.checkVisibility()).map(e=>{const r=e.getBoundingClientRect();return {label:e.getAttribute('aria-label')||e.textContent.trim(),width:r.width,height:r.height,pass:r.width>= (e.classList.contains('carousel-dot')?24:44)&&r.height>= (e.classList.contains('carousel-dot')?24:44)}})")
    page.evaluate('scrollTo(0,0)');page.wait_for_timeout(200)
    if engine=='chromium':page.screenshot(path=str(OUT/f'whole-page-{w}x{h}-text{scale}.png'),full_page=True)
    if scale==2 and engine=='chromium':
     for selector in ('#hero','#video','#highlights','#community','#contact','.footer'):
      loc=page.locator(selector);loc.scroll_into_view_if_needed();loc.screenshot(path=str(OUT/f'enlarged-{selector.strip("#.")}.png'))
    menu=[]
    if page.locator('#navToggle').is_visible():
     page.locator('#navToggle').click();panel=page.locator('#navLinks').bounding_box()
     for link in page.locator('#navLinks>a').all():
      link.scroll_into_view_if_needed();box=link.bounding_box();menu.append({'text':link.inner_text(),'bounded':box['x']>=panel['x']-1 and box['x']+box['width']<=panel['x']+panel['width']+1,'scrollWidth':link.evaluate('(e)=>e.scrollWidth'),'clientWidth':link.evaluate('(e)=>e.clientWidth')})
     if engine=='chromium':page.screenshot(path=str(OUT/f'menu-{w}x{h}-text{scale}.png'))
     page.keyboard.press('Escape')
     toggle=page.locator('#navToggle')
     toggle.focus();page.keyboard.press('Enter')
     assert toggle.get_attribute('aria-expanded')=='true'
     assert page.locator('#navLinks>a').first.evaluate('(e)=>e===document.activeElement')
     page.locator('#main').focus()
     assert toggle.get_attribute('aria-expanded')=='false'
     toggle.click();page.keyboard.press('Escape')
     assert toggle.get_attribute('aria-expanded')=='false'
     assert toggle.evaluate('(e)=>e===document.activeElement')
     if w>320:
      toggle.click();page.mouse.click(1,h-2)
      assert toggle.get_attribute('aria-expanded')=='false'
    results.append({'engine':engine,'width':w,'height':h,'scale':scale,'controls':controls,'menu':menu,'fonts':page.evaluate("({status:document.fonts.status,faces:[...document.fonts].map(f=>({family:f.family,status:f.status}))})"),'networkFailures':failed})
    page.close()
   b.close()
finally:server.shutdown()
(OUT/'supplemental.json').write_text(json.dumps(results,indent=2));print('Supplemental cases',len(results));print('Bad controls',[(r['engine'],r['width'],c) for r in results for c in r['controls'] if not c['pass']]);print('Bad menu',[(r['engine'],r['width'],c) for r in results for c in r['menu'] if not c['bounded'] or c['scrollWidth']>c['clientWidth']+1]);print('Font evidence',results[0]['fonts'],results[0]['networkFailures'])
assert all(c['pass'] for r in results for c in r['controls'])
assert all(c['bounded'] and c['scrollWidth']<=c['clientWidth']+1 for r in results for c in r['menu'])
