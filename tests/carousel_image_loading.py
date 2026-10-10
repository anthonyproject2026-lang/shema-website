"""Check navigation while lazy images retain their HTML aspect ratio.

--before uses HEAD's CSS read-only to retain a pre-fix reproduction.
"""
import json
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
before='--before' in sys.argv
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width in (320,390,430,1440):
  page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
  # Keep carousel images pending to reproduce pre-decode intrinsic sizing.
  page.route('**/images/optimized/*.webp',lambda route:route.abort())
  if before:
   css=subprocess.check_output(['git','show','HEAD:styles.css'],cwd=ROOT).decode('utf-8')
   page.route('**/styles.css',lambda route:route.fulfill(body=css,content_type='text/css'))
  page.goto((ROOT/'index.html').as_uri())
  page.locator('#carouselPauseBtn').click()
  for index in range(10):
   page.locator('.carousel-dot').nth(index).click()
   result=page.evaluate("""index=>{
    const v=document.querySelector('#carouselViewport'),c=document.querySelectorAll('.kerala-card')[index];
    const vr=v.getBoundingClientRect(),r=c.getBoundingClientRect(),p=c.querySelector('p').getBoundingClientRect();
    const left=vr.left+v.clientLeft,right=vr.right-v.clientLeft;
    return {index,title:c.querySelector('h3').textContent,delta:r.left-left,width:r.width,viewport:right-left,
     aligned:Math.abs(r.left-left)<.5&&Math.abs(r.right-right)<.5,
     captionVisible:p.left>=left&&p.right<=right&&p.top>=r.top&&p.bottom<=r.bottom};
   }""",index)
   results.append(dict(result,phoneWidth=width))
   if before and index==1 and width<500:
    page.locator('#keralaCarousel').screenshot(path=str(ROOT/f'tests/evidence/carousel/before-pending-theyyam-{width}.png'))
  page.close()
 browser.close()
failures=[r for r in results if not r['aligned'] or not r['captionVisible']]
(ROOT/f'tests/evidence/carousel/{"before" if before else "after"}-pending.json').write_text(json.dumps(results,indent=2))
print(f'Pending images: {len(results)} checks, {len(failures)} failures')
assert not failures,failures[:2]
