"""Behavioral browser checks. Skipped if a Chromium runtime is unavailable."""
import copy, importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline_motion',ROOT/'scripts/pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Motion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
            cls.pw=sync_playwright().start()
            cls.browser=p.launch(cls.pw)
        except Exception as exc:
            if hasattr(cls,'pw'):cls.pw.stop()
            raise unittest.SkipTest('Browser unavailable: '+str(exc))
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def prepare(self,name,out):
        d=p.read(ROOT/f'examples/{name}.json');tl={'total':54,'scenes':[]}
        for i,s in enumerate(d['scenes']):tl['scenes'].append(dict(copy.deepcopy(s),start=i*9,duration=9,captions=[]))
        p.prepare_page(d,ROOT/f'examples/{name}.json',out,tl)
        page=self.browser.new_page();page.goto((out/'index.html').as_uri());page.evaluate('ready()')
        self.addCleanup(page.close)
        return d,tl,page
    def test_all_builtin_examples_have_subject_motion(self):
        for name in ['oil','thermal','mesh','mri']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);d,tl,page=self.prepare(name,out)
                p.motion_review(page,d,tl,out)
                self.assertTrue(p.read(out/'motion-check.json')['passed'])
    def test_frozen_subject_rejected_despite_public_background_motion(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);d,tl,page=self.prepare('mri',out)
            page.evaluate('window.drawMRI=(v,t)=>{panel(100,450,500,400);text("Frozen subject",350,650,30)}')
            with self.assertRaisesRegex(ValueError,'Static mechanism'):p.motion_review(page,d,tl,out)
    def test_custom_subject_region_detects_moving_and_static_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);d=p.read(ROOT/'examples/mesh.json')
            d['animation_script']='@skill/examples/custom-animation.js'
            for s in d['scenes'][:3]:s['visual']={'type':'custom','key':'sieve','motion_region':[100,430,520,460],'demonstration':'较小颗粒穿过筛孔，大颗粒被筛网截留，展示尺寸筛分。'}
            d['cover']['visual']='custom';p.validate(d)
            tl={'total':54,'scenes':[dict(copy.deepcopy(s),start=i*9,duration=9,captions=[]) for i,s in enumerate(d['scenes'])]}
            p.prepare_page(d,ROOT/'examples/mesh.json',out,tl)
            page=self.browser.new_page();self.addCleanup(page.close);page.goto((out/'index.html').as_uri());page.evaluate('ready()')
            p.motion_review(page,d,tl,out)
            page.evaluate('window.drawPatentCustom=(v,t)=>{panel(120,460,470,400)}')
            with self.assertRaisesRegex(ValueError,'Static mechanism'):p.motion_review(page,d,tl,out)

if __name__=='__main__':unittest.main()
