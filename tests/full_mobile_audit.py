"""Complete rendered layout audit; --url supports read-only host verification."""
import argparse,json,subprocess
from pathlib import Path
from functools import partial
from threading import Thread
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests/evidence/full-mobile'; OUT.mkdir(parents=True,exist_ok=True)
a=argparse.ArgumentParser(); a.add_argument('--url'); a.add_argument('--before',action='store_true'); a.add_argument('--output'); a.add_argument('--landscape-only',action='store_true'); a.add_argument('--engine',choices=('chromium','webkit')); args=a.parse_args()
if args.output: OUT=ROOT/args.output; OUT.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
 def copyfile(self,source,outputfile):
  try: super().copyfile(source,outputfile)
  except (ConnectionResetError,ConnectionAbortedError,BrokenPipeError): pass
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'none'")
  super().end_headers()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT))); Thread(target=server.serve_forever,daemon=True).start()
base=(args.url or f'http://127.0.0.1:{server.server_port}').rstrip('/')
# Text-node ranges are tested against every real clipping ancestor, excluding
# intentionally offscreen carousel slides and closed navigation/dialog controls.
MEASURE=r'''root=>{
 const issues=[]; let nodes=0;
 const walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
 while(walk.nextNode()){
  const n=walk.currentNode,e=n.parentElement;
  if(!n.textContent.trim()||e.closest('script,style,.skip-link,.nav-links:not(.active),.event-gallery-modal:not(.active)'))continue;
  if(e.closest('.kerala-card')&&!e.closest('.kerala-card').classList.contains('audit-active'))continue;
  if(!e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;
  const range=document.createRange();range.selectNodeContents(n); nodes++;
  for(const r of range.getClientRects()){
   if(r.width<.1||r.height<.1)continue;
   for(let p=e;p;p=p.parentElement){
    const s=getComputedStyle(p),b=p.getBoundingClientRect();
    const x=['hidden','clip'].includes(s.overflowX),y=['hidden','clip'].includes(s.overflowY);
    if((x&&(r.left<b.left-1||r.right>b.right+1))||(y&&(r.top<b.top-1||r.bottom>b.bottom+1)))
     issues.push({text:n.textContent.trim().slice(0,90),ancestor:p.id||p.className,rect:{top:r.top,bottom:r.bottom,left:r.left,right:r.right},clip:{top:b.top,bottom:b.bottom,left:b.left,right:b.right}});
   }
  }
 }
 return {nodes,issues,overflow:document.documentElement.scrollWidth>innerWidth+1};
}'''
results=[]; blockers=[]
try:
 with sync_playwright() as p:
  for engine in ((args.engine,) if args.engine else ('chromium','webkit')):
   try: browser=getattr(p,engine).launch()
   except Exception as e: blockers.append({'engine':engine,'error':str(e)});continue
   context=browser.new_context(has_touch=True)
   cases=[(w,900,m,1,False) for w in (320,375,390,430,768,1024,1440) for m in ('reduce','no-preference')]
   cases += [(w,h,'reduce',scale,False) for w,h,scale in ((667,375,1),(844,390,1),(320,900,2),(390,900,2),(768,900,2),(1440,900,2))]
   cases += [(390,900,'reduce',1,True)]
   landscape=[(667,375,'no-preference',1,False),(844,390,'no-preference',1,False)]
   cases = landscape if args.landscape_only else cases + landscape
   if args.before: cases=[(390,900,'reduce',1,False)]
   for w,h,m,scale,fallback in cases:
    page=context.new_page();page.set_viewport_size({'width':w,'height':h});page.emulate_media(reduced_motion=m)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    if fallback:page.route('**/fonts.googleapis.com/**',lambda r:r.abort());page.route('**/fonts.gstatic.com/**',lambda r:r.abort())
    if args.before:
     css=subprocess.check_output(['git','show','HEAD:styles.css'],cwd=ROOT).decode()
     page.route('**/styles.css',lambda r:r.fulfill(body=css,content_type='text/css'))
    label=f'{engine}-{w}x{h}-{m}-text{scale}'+('-fallback' if fallback else '')
    for filename in ('index.html','privacy.html','media-credits.html','404.html'):
     page.goto(base+'/'+filename,wait_until='domcontentloaded');page.evaluate('document.fonts.ready')
     if scale==2:page.add_style_tag(content='html {font-size:200% !important}')
     sections=page.locator('main > section,footer') if filename=='index.html' else page.locator('main,body > .container')
     inventory=[];issues=[]
     if filename=='index.html':
      page.locator('#carouselPauseBtn').click()
      page.locator('.kerala-card').first.evaluate("e=>e.classList.add('audit-active')")
     for i in range(sections.count()):
      section=sections.nth(i);section.scroll_into_view_if_needed();page.wait_for_timeout(450 if m=='no-preference' else 100)
      section.locator('img').evaluate_all("imgs=>imgs.forEach(i=>i.loading='eager')")
      section.locator('img').evaluate_all("imgs=>Promise.all(imgs.map(i=>i.decode().catch(()=>{})))")
      data=section.evaluate(MEASURE)
      if section.get_attribute('id')=='kerala':
       for slide in range(10):
        page.locator('.carousel-dot').nth(slide).click();page.wait_for_timeout(550 if m=='no-preference' else 20)
        page.locator('.kerala-card').evaluate_all('(es,i)=>es.forEach((e,j)=>e.classList.toggle("audit-active",i===j))',slide)
        data['issues'].extend(section.evaluate(MEASURE)['issues'])
      name=section.get_attribute('id') or section.get_attribute('class') or filename
      inventory.append({'section':name,**data});issues.extend(data['issues'])
      if data['overflow']:issues.append({'overflow':name})
      # Readable viewport tiles cover every section, not a full-page thumbnail.
      if engine=='chromium' and w==390 and scale==1 and m=='reduce' and not fallback:
       box=section.bounding_box();top=page.evaluate('scrollY')+box['y'];height=box['height']
       for tile,offset in enumerate(range(0,int(height)+1,700)):
        page.evaluate('(y)=>scrollTo(0,y)',max(0,top+offset-110));page.wait_for_timeout(100)
        page.screenshot(path=str(OUT/f'{"before" if args.before else "after"}-{filename}-{i:02}-{tile:02}.png'))
     extra={}
     if filename=='index.html':
      banner=page.locator('.community-banner');banner.scroll_into_view_if_needed()
      extra['banner']=banner.evaluate(MEASURE)
      if w in (320,390,1440) and m=='reduce':banner.screenshot(path=str(OUT/f'{"before" if args.before else "after"}-banner-{label}.png'))
      toggle=page.locator('#navToggle')
      if toggle.is_visible():
       toggle.click();links=page.locator('#navLinks > a');extra['menu']=[]
       for link in links.all():
        link.scroll_into_view_if_needed();b=link.bounding_box();extra['menu'].append({'label':link.inner_text(),'reachable':b['y']>=-1 and b['y']+b['height']<=h+1,'height':b['height']})
       page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
       toggle.click();links.first.click();assert toggle.get_attribute('aria-expanded')=='false'
      extra['hash']=[]
      for href in page.locator('#navLinks > a').evaluate_all("els=>els.map(e=>e.getAttribute('href'))"):
       if not href.startswith('#'):continue
       # Use real links and wait for scroll to settle; reassignment of an
       # unchanged hash does not scroll, and smooth scrolling is asynchronous.
       target=page.locator(href)
       if toggle.is_visible(): toggle.click()
       page.locator('#navLinks > a[href="'+href+'"]').click()
       last=None;stable=0
       for poll in range(30):
        page.wait_for_timeout(100);current=target.bounding_box()['y']
        stable=stable+1 if last is not None and abs(current-last)<.5 else 0
        last=current
        if stable>=3:break
       b=target.bounding_box();nav=page.locator('#navbar').bounding_box()
       extra['hash'].append({'href':href,'top':b['y'],'navBottom':nav['y']+nav['height'],'clear':b['y']>=nav['y']+nav['height']-2})
      extra['fonts']=page.evaluate("({status:document.fonts.status,faces:[...document.fonts].map(f=>({family:f.family,status:f.status}))})")
     results.append({'case':label,'page':filename,'inventory':inventory,'issues':issues,'errors':errors.copy(),**extra})
    page.close();(OUT/'progress.json').write_text(json.dumps(results,indent=2));print('DONE',label,flush=True)
   browser.close()
finally:server.shutdown()
failures=[r for r in results if r['issues'] or r['errors'] or any(not x['reachable'] for x in r.get('menu',[])) or any(not x['clear'] for x in r.get('hash',[]))]
(OUT/('before.json' if args.before else 'after.json')).write_text(json.dumps({'results':results,'blockers':blockers,'failures':len(failures)},indent=2))
print(f'{len(results)} page cases; {len(failures)} failures; {len(blockers)} engine blockers')
for r in failures[:10]:print(r['case'],r['page'],r['issues'][:3],r.get('hash',[]))
assert not failures
