"""Local browser regression: python tests/browser_review.py"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright, TimeoutError
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests'/'evidence'; OUT.mkdir(exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def copyfile(self, source, outputfile):
        try: super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError): pass
def assert_nav_layout(page):
    collapsed=page.locator('#navToggle').is_visible()
    if collapsed: page.locator('#navToggle').click()
    result=page.evaluate("""()=>{
      const rect=e=>e.getBoundingClientRect();
      const links=[...document.querySelectorAll('#navLinks a')];
      const elements=collapsedPlaceholder;
      const bounded=elements.every(e=>{const r=rect(e);return r.left>=-1 && r.right<=innerWidth+1 && r.top>=-1 && r.bottom<=innerHeight+1});
      const overlap=elements.some((e,i)=>elements.slice(i+1).some(f=>{const a=rect(e),b=rect(f);return Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1}));
      const singleLine=e=>[...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE && n.textContent.trim()).every(n=>{const range=document.createRange();range.selectNodeContents(n);return new Set([...range.getClientRects()].filter(r=>r.width>0).map(r=>Math.round(r.top))).size===1});
      const ctas=[...document.querySelectorAll('.hero-buttons a,.cta-buttons a')];
      const color=getComputedStyle(document.querySelector('.hero-buttons .btn-outline'));
      const rgb=s=>s.match(/[\d.]+/g).map(Number);
      const lum=s=>rgb(s).slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
      const a=lum(color.color), b=lum(color.backgroundColor);
      return {bounded,overlap,singleLine:links.concat(ctas).every(singleLine),ctaBounded:ctas.every(e=>{const r=rect(e);return r.left>=0&&r.right<=innerWidth+1}),opaque:rgb(color.backgroundColor).length===3||rgb(color.backgroundColor)[3]===1,contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
    }""".replace('collapsedPlaceholder', "links.concat(document.querySelector('#navToggle'))" if collapsed else "links.concat(document.querySelector('#navbar .nav-logo'))"))
    assert result['bounded'] and not result['overlap'] and result['singleLine'] and result['ctaBounded'], result
    assert result['opaque'] and result['contrast']>=4.5, result
    if collapsed: page.keyboard.press('Escape')
    return collapsed

server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for motion, width in ((m,w) for m in ('reduce','no-preference') for w in (1024,1280,1440,320,390)):
            page=browser.new_page(viewport={'width':width,'height':900},reduced_motion=motion)
            errors=[]; missing=[]; videos=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:missing.append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
            page.on('request',lambda r:videos.append(r.url) if '.mp4' in r.url else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            page.evaluate('document.fonts.ready'); page.wait_for_timeout(300)
            collapsed=assert_nav_layout(page)
            page.reload()
            page.evaluate('document.fonts.ready')
            page.keyboard.press('Tab')
            assert page.locator('.skip-link').evaluate('(e)=>e===document.activeElement')
            page.keyboard.press('Enter')
            assert page.evaluate('location.hash')=='#main'
            assert page.locator('#main').evaluate('(e)=>e===document.activeElement')
            if collapsed:
                toggle=page.locator('#navToggle'); toggle.focus(); page.keyboard.press('Enter')
                assert toggle.get_attribute('aria-expanded')=='true'
                assert page.locator('#navLinks a').first.evaluate('(e)=>e===document.activeElement')
                page.keyboard.press('Escape'); assert toggle.get_attribute('aria-expanded')=='false'
                assert toggle.evaluate('(e)=>e===document.activeElement')
                page.keyboard.press('Enter')
                page.keyboard.press('Enter')
                assert page.evaluate('location.hash')=='#about'
                assert page.locator('#about').evaluate('(e)=>e===document.activeElement')
                assert toggle.get_attribute('aria-expanded')=='false' 
            trigger=page.locator('.event-gallery-trigger'); trigger.click()
            assert page.locator('#eventGalleryEmpty').is_visible()
            assert page.locator('main').evaluate('(e)=>e.inert')
            page.keyboard.press('Tab'); assert page.locator('#eventGalleryClose').evaluate('(e)=>e===document.activeElement')
            page.keyboard.press('Escape'); assert trigger.evaluate('(e)=>e===document.activeElement')
            assert not page.locator('main').evaluate('(e)=>e.inert')
            page.evaluate('window.scrollTo(0,0)')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
            # Scroll each image into view so all lazy local resources are exercised.
            for img in page.locator('img').all(): img.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            assert page.locator('img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)')
            assert not errors,errors
            assert not missing,missing
            assert not videos,videos
            culture=page.locator('#culture')
            culture.scroll_into_view_if_needed()
            assert culture.locator('.culture-item').count()==8
            assert culture.locator('.culture-item img').count()==1
            assert culture.locator('.culture-item').evaluate_all("items=>items.every(e=>{const r=e.getBoundingClientRect();return r.width>0 && r.left>=0 && r.right<=innerWidth+1 && e.scrollWidth<=e.clientWidth})")
            discovery=culture.locator('.culture-discovery a')
            assert discovery.is_visible()
            assert discovery.get_attribute('rel')=='noopener noreferrer'
            assert discovery.get_attribute('href')=='https://www.keralatourism.org/video-gallery/'
            assert discovery.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
            if motion=='reduce':
                culture.screenshot(path=str(OUT/f'culture-{width}.png'), style='#navbar, #backToTop { visibility: hidden !important; }')
            carousel=page.locator('#keralaCarousel')
            carousel.scroll_into_view_if_needed()
            page.mouse.move(0,0)
            page.locator('#main').focus()
            page.wait_for_timeout(600)
            counter=page.locator('.carousel-counter')
            before=counter.inner_text()
            page.wait_for_timeout(5200)
            if motion=='no-preference': assert counter.inner_text()!=before, 'Normal-motion autoplay did not advance'
            else: assert counter.inner_text()==before, 'Reduced-motion autoplay advanced'
            page.locator('#carouselNext').focus()
            page.keyboard.press('Enter')
            focused=counter.inner_text()
            page.wait_for_timeout(5200)
            assert counter.inner_text()==focused, 'Carousel advanced while focused'
            # Real user click; no play() mocking or programmatic playback.
            page.locator('#videoPlayBtn').click()
            try:
                page.wait_for_function("()=>{const v=document.querySelector('#keralaVideo'); return !v.paused && v.currentTime>0.1}", timeout=15000)
                assert page.locator('#keralaVideo').evaluate('(v)=>v.controls')
                page.wait_for_function("getComputedStyle(document.querySelector('#videoOverlay')).visibility==='hidden'")
                print(f'PASS playback {motion} {width}px: time advanced after user click')
                page.locator('#keralaVideo').evaluate('(v)=>v.pause()')
            except TimeoutError:
                state=page.locator('#keralaVideo').evaluate('(v)=>({error:v.error && {code:v.error.code,message:v.error.message},network:v.networkState,ready:v.readyState,currentTime:v.currentTime})')
                assert state['error'] and state['error']['code'] in (3,4), state
                assert page.locator('#videoOverlay').evaluate('(e)=>getComputedStyle(e).visibility')=='visible'
                assert page.locator('#videoPlayBtn').get_attribute('aria-label')=='Video unavailable. Try playing again'
                print(f'CODEC BLOCKER {motion} {width}px: {state}')
            assert videos, 'User playback did not request MP4'
            assert not errors,errors
            assert not missing,missing
            page.evaluate('window.scrollTo(0,0)'); page.wait_for_timeout(800); page.screenshot(path=str(OUT/(f'home-{width}.png' if motion=='reduce' else f'home-normal-{width}.png')),full_page=True)
            if motion=='reduce' and width in (1440,390):
                page.screenshot(path=str(OUT/('desktop-preview.png' if width==1440 else 'mobile-preview.png')))
            page.goto(f'http://127.0.0.1:{server.server_port}/404.html')
            assert page.locator('h1').inner_text()=='Page not found'
            page.close(); print(f'PASS {motion} {width}px: menu/dialog focus, overflow, images, no pre-play video requests, skip/destination, carousel focus pause, console, 404 document')
        for width in (1024,1280,1440,320,390):
            page=browser.new_page(viewport={'width':width,'height':900},java_script_enabled=False)
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            for item in page.locator('.reveal').all():
                item.scroll_into_view_if_needed()
                assert item.is_visible()
                assert item.evaluate('(e)=>getComputedStyle(e).opacity')=='1'
                assert item.inner_text().strip() or item.locator('img,video').count()
            assert page.locator('h1').is_visible()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.close(); print(f'PASS no-JS content {width}px')
        browser.close()
finally: server.shutdown()
