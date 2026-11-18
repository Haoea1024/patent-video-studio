"""Cover generation works without an audio timeline or external image service."""
import importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline_cover',ROOT/'scripts/pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Covers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
            cls.pw=sync_playwright().start();cls.browser=p.launch(cls.pw)
        except Exception as exc:
            if hasattr(cls,'pw'):cls.pw.stop()
            raise unittest.SkipTest('Browser unavailable: '+str(exc))
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def page(self,d,out):
        tl={'total':54,'scenes':[dict(s,start=i*9,duration=9,captions=[]) for i,s in enumerate(d['scenes'])]}
        p.prepare_page(d,out/'project.json',out,tl)
        page=self.browser.new_page();self.addCleanup(page.close);page.goto((out/'index.html').as_uri());page.evaluate('ready()');return page
    def test_four_distinct_covers_without_audio(self):
        from PIL import Image
        fingerprints=[]
        for name in ['oil','thermal','mesh','mri']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);d=p.read(ROOT/f'examples/{name}.json');page=self.page(d,out)
                p.cover_assets(page,d,out/'project.json',out)
                report=p.read(out/'cover-check.json');fingerprints.append(report['image_sha256'])
                self.assertTrue(report['passed']);self.assertFalse((out/'timeline.json').exists())
                self.assertEqual(p.read(out/'cover-brief.json')['title'],d['title'])
                self.assertIn(d['audience'],(out/'cover-prompt.txt').read_text(encoding='utf-8'))
                with Image.open(out/'cover-thumbnail.jpg') as im:self.assertEqual(im.size,(270,480))
        self.assertEqual(len(set(fingerprints)),4)
    def test_explicit_hero_and_time_change_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);d=p.read(ROOT/'examples/mri.json');page=self.page(d,out)
            p.cover_assets(page,d,out/'project.json',out);original=p.read(out/'cover-check.json')['image_sha256'];page.close()
            d['cover'].update(scene_id='rebuild',time=7);p.validate(d);page=self.page(d,out)
            p.cover_assets(page,d,out/'project.json',out)
            self.assertNotEqual(original,p.read(out/'cover-check.json')['image_sha256'])
            self.assertEqual(p.read(out/'cover-brief.json')['hero_scene'],'rebuild')
    def test_provided_image_preserved_and_blank_rejected(self):
        from PIL import Image, ImageDraw, ImageChops
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);d=p.read(ROOT/'examples/mri.json');d['cover']['image']='provided.png'
            im=Image.new('RGB',(1080,1920),'#112233');ImageDraw.Draw(im).rectangle((120,200,960,1720),fill='#deb456');im.save(out/'provided.png')
            p.cover_assets(None,d,out/'project.json',out)
            with Image.open(out/'cover.png') as rendered:self.assertIsNone(ImageChops.difference(im,rendered.convert('RGB')).getbbox())
            Image.new('RGB',(1080,1920),'white').save(out/'provided.png')
            with self.assertRaisesRegex(ValueError,'blank'):p.cover_assets(None,d,out/'project.json',out)
    def test_stale_cover_rejected_before_video_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);d=p.read(ROOT/'examples/mri.json');page=self.page(d,out)
            p.cover_assets(page,d,out/'project.json',out)
            p.write(out/'timeline.json',{'project_hash':p.data_hash(d)});p.write(out/'motion-check.json',{'project_hash':p.data_hash(d),'passed':True})
            (out/'cover.png').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed cover'):p.check(d,out/'project.json',out)

if __name__=='__main__':unittest.main()
