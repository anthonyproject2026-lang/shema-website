import hashlib
import json
import unittest
import subprocess
from pathlib import Path
from PIL import Image
from test_upgrade import Elements

ROOT = Path(__file__).resolve().parents[1]
IDS = ['padmanabhaswamy-temple-161693828','varkala-cliff-121378838','munnar-tea-gardens-68764763','fort-kochi-162909249','aranmula-kannadi-101277121','kasaragod-sarees-96010319','malabar-pepper-151971300','alleppey-coir-137695846']

class DestinationsCraftsTests(unittest.TestCase):
    def test_previous_culture_and_security_preserved(self):
        old = subprocess.check_output(['git','show','HEAD:index.html'],cwd=ROOT).decode('utf-8')
        new = (ROOT/'index.html').read_text(encoding='utf-8')
        def culture(s): return s.split('id="culture"',1)[1].split('</section>',1)[0]
        self.assertEqual(culture(old),culture(new))
        for filename in ('_headers','script.js'):
            self.assertEqual(subprocess.check_output(['git','show','HEAD:'+filename],cwd=ROOT).decode().replace('\r\n','\n'),(ROOT/filename).read_text(encoding='utf-8'))

    def test_all_eight_cards_and_licensed_derivatives(self):
        raw = (ROOT/'images/destinations-crafts/manifest.json').read_text(encoding='utf-8')
        records = json.loads(raw)
        self.assertEqual([r['id'] for r in records], IDS)
        self.assertNotRegex(raw, r'[A-Za-z]:\\|local_path|evidence_path')
        html = (ROOT/'index.html').read_text(encoding='utf-8')
        credits = (ROOT/'media-credits.html').read_text(encoding='utf-8')
        parser = Elements(); parser.feed(credits)
        credit_links = {a.get('href') for t,a in parser.items if t=='a'}
        for r in records:
            with self.subTest(card=r['name']):
                self.assertEqual(html.count('data-media-id="'+r['id']+'"'),1)
                card = html.split('data-media-id="'+r['id']+'"',1)[1].split('</figure>',1)[0]
                self.assertIn(r['caption'], card)
                self.assertIn(r['author'], card)
                self.assertIn(r['license'], card)
                self.assertIn(r['source_url'], credit_links)
                self.assertIn(r['license_url'], credit_links)
                self.assertIn(r['title'], credits)
                self.assertIn(r['modifications'], credits)
                p = Elements(); p.feed('<div '+card)
                image = next(a for t,a in p.items if t=='img')
                self.assertEqual(image['loading'],'lazy')
                self.assertEqual(image['alt'],r['caption'])
                self.assertEqual((int(image['width']),int(image['height'])),(r['derivatives'][1]['width'],r['derivatives'][1]['height']))
                for d in r['derivatives']:
                    path = ROOT/d['path']
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),d['sha256'])
                    with Image.open(path) as im:
                        self.assertEqual(im.size,(d['width'],d['height']))
                        self.assertFalse(im.getexif())
                        self.assertFalse({'exif','icc_profile','xmp'} & im.info.keys())
                self.assertTrue(r['external_links'])
        for phrase in ['not a finished saree photograph','GI-certified Malabar provenance is not established','not certified goods']:
            self.assertIn(phrase,html)
