import re
import unittest
from html.parser import HTMLParser
from PIL import Image
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT = Path(__file__).resolve().parents[1]
class Elements(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]
    def handle_starttag(self, tag, attrs): self.items.append((tag,dict(attrs)))
class UpgradeTests(unittest.TestCase):
    def test_local_assets_and_fragment_targets_exist(self):
        for page in ROOT.glob('*.html'):
            parser=Elements(); parser.feed(page.read_text(encoding='utf-8'))
            ids={a['id'] for _,a in parser.items if 'id' in a}
            for tag,a in parser.items:
                for attr in ('src','href','poster'):
                    value=a.get(attr,''); url=urlsplit(value)
                    if not value or url.scheme or url.netloc: continue
                    if url.path:
                        self.assertTrue((ROOT/unquote(url.path.lstrip('/'))).is_file(),(page.name,value))
                    elif url.fragment:
                        self.assertIn(url.fragment,ids,(page.name,value))
                for candidate in a.get('srcset','').split(','):
                    if candidate.strip(): self.assertTrue((ROOT/candidate.split()[0]).is_file())
    def test_static_images_and_honest_empty_gallery(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertNotIn('/.netlify/images?',html)
        self.assertIn('No photographs are available',html)
        self.assertNotIn('ten approved',html)
        self.assertRegex(html,r'preload="none"')
    def test_not_found_recovery(self):
        html=(ROOT/'404.html').read_text(encoding='utf-8')
        self.assertIn('/index.html#contact',html)
        self.assertIn('/index.html#events',html)

    def test_responsive_widths_match_intrinsic_files_and_are_unique(self):
        for page in ROOT.glob('*.html'):
            parser=Elements(); parser.feed(page.read_text(encoding='utf-8'))
            for tag,attrs in parser.items:
                for attr in ('srcset', 'imagesrcset'):
                    descriptors=[]
                    for candidate in attrs.get(attr, '').split(','):
                        if not candidate.strip(): continue
                        path,descriptor=candidate.split()
                        descriptors.append(descriptor)
                        asset=ROOT/unquote(urlsplit(path).path.lstrip('/'))
                        self.assertTrue(asset.is_file(), (page.name, attr, path))
                        if descriptor.endswith('w'):
                            with Image.open(asset) as image:
                                self.assertEqual(int(descriptor[:-1]), image.width,
                                                 (page.name, attr, path))
                    self.assertEqual(len(descriptors), len(set(descriptors)),
                                     (page.name, tag, attr, descriptors))

    def test_culture_thumbnail_mapping_and_discovery_safety(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        culture=html.split('id="culture"',1)[1].split('</section>',1)[0]
        cards=culture.split('<div class="culture-item reveal">')[1:]
        self.assertEqual(len(cards),8)
        import json
        records=json.loads((ROOT/'images/culture/manifest.json').read_text(encoding='utf-8'))
        credits=(ROOT/'media-credits.html').read_text(encoding='utf-8')
        cp=Elements(); cp.feed(credits)
        credit_links=[a['href'] for tag,a in cp.items if tag=='a']
        for card, record in zip(cards, records):
            card=card.split('</figure>',1)[0]+'</figure>'
            parser=Elements(); parser.feed(card)
            images=[a for tag,a in parser.items if tag=='img']
            self.assertEqual(len(images),1)
            image=images[0]
            self.assertEqual(image['src'],record['derivatives'][1]['path'])
            self.assertEqual(image['loading'],'lazy')
            self.assertTrue(image['alt'])
            with Image.open(ROOT/image['src']) as asset:
                self.assertEqual((int(image['width']),int(image['height'])),asset.size)
            self.assertIn('Photograph:',card)
            self.assertIn(record['author'],card)
            self.assertIn(record['license'],card)
            self.assertIn(record['source_url'],credit_links)
            self.assertIn(record['license_url'],credit_links)
            self.assertIn(record['title'],credits)
            if 'SA' in record['license']: self.assertIn('ShareAlike',credits)
            for derivative in record['derivatives']:
                with Image.open(ROOT/derivative['path']) as asset:
                    self.assertEqual(asset.size,(derivative['width'],derivative['height']))
                    self.assertFalse(asset.getexif())
                    self.assertNotIn('icc_profile',asset.info)
        parser=Elements(); parser.feed(culture)
        links=[a for tag,a in parser.items if tag=='a' and a.get('target')=='_blank']
        self.assertEqual(len(links),8)
        self.assertEqual({a['href'] for a in links},{r['video_url'] for r in records})
        for link in links:
            self.assertEqual(set(link['rel'].split()),{'noopener','noreferrer'})
        self.assertIn('Source: Kerala Tourism',culture)
        self.assertIn('separate from SHEMA events',culture)
        for tag,a in parser.items:
            self.assertNotIn(tag,('iframe','video','script'))
            self.assertNotIn('download',a)
