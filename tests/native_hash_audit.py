"""Direct URL fragments and privacy text enlargement, with optional pre-fix CSS."""
import argparse,json,subprocess,ast
from pathlib import Path
from functools import partial
from threading import Thread
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tests/evidence/full-mobile'
a=argparse.ArgumentParser();a.add_argument('--before',action='store_true');args=a.parse_args()
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start()
module=ast.parse((ROOT/'tests/full_mobile_audit.py').read_text(encoding='utf-8-sig'));measure=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MEASURE' for t in n.targets));results=[]
try:
 with sync_playwright() as p:
  for engine in ('chromium','webkit'):
   browser=getattr(p,engine).launch();context=browser.new_context(reduced_motion='reduce')
   for width in (320,375,390,430,768,1024,1440):
    for scale in (1,2):
     page=context.new_page();page.set_viewport_size({'width':width,'height':900})
     css=subprocess.check_output(['git','show','HEAD:styles.css'],cwd=ROOT).decode() if args.before else (ROOT/'styles.css').read_text()
     page.route('**/styles.css',lambda r:r.fulfill(body=css+f'\nhtml{{font-size:{scale*100}% !important}}',content_type='text/css'))
     for fragment in ('about','community','contact'):
      page.goto(f'http://127.0.0.1:{server.server_port}/index.html#{fragment}');page.evaluate('document.fonts.ready');page.wait_for_timeout(300)
      target=page.locator('#'+fragment).bounding_box();nav=page.locator('#navbar').bounding_box();results.append({'engine':engine,'width':width,'scale':scale,'fragment':fragment,'top':target['y'],'navBottom':nav['y']+nav['height'],'pass':target['y']>=nav['y']+nav['height']-2})
     if args.before:
      privacy=subprocess.check_output(['git','show','HEAD:privacy.html'],cwd=ROOT).decode();page.route('**/privacy.html',lambda r:r.fulfill(body=privacy,content_type='text/html'))
     page.goto(f'http://127.0.0.1:{server.server_port}/privacy.html');page.add_style_tag(content=f'html{{font-size:{scale*100}% !important}}');data=page.locator('body').evaluate(measure);results.append({'engine':engine,'width':width,'scale':scale,'page':'privacy','data':data,'pass':not data['issues'] and not data['overflow']});page.close()
   browser.close()
finally:server.shutdown()
(OUT/f'native-hash-{"before" if args.before else "after"}.json').write_text(json.dumps(results,indent=2));bad=[r for r in results if not r['pass']];print(len(results),'checks;',len(bad),'failures');print(bad[:5]);assert not bad
