import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts/pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Contracts(unittest.TestCase):
    def sample(self):return p.read(ROOT/'examples/mesh.json')
    def test_examples_valid(self):
        for n in ['oil','thermal','mesh','mri']:p.validate(p.read(ROOT/f'examples/{n}.json'))
    def test_cover_hero_must_exist_and_match_type(self):
        d=self.sample();d['cover']['scene_id']='cta'
        with self.assertRaisesRegex(ValueError,'cover.scene_id'):p.validate(d)
    def test_text_only_video_is_rejected(self):
        d=self.sample()
        for s in d['scenes'][:-1]:s['visual']={'type':'flow','items':['输入','处理','输出']}
        d['cover']['visual']='flow'
        with self.assertRaisesRegex(ValueError,'At least two'):p.validate(d)
    def test_mri_decorative_scenes_do_not_count(self):
        d=p.read(ROOT/'examples/mri.json')
        for s in d['scenes'][:-1]:s['visual']['mode']='acquisition'
        with self.assertRaisesRegex(ValueError,'At least two'):p.validate(d)
    def test_mechanism_requires_action_description(self):
        d=self.sample();d['scenes'][0]['visual'].pop('demonstration')
        with self.assertRaisesRegex(ValueError,'changing state'):p.validate(d)
    def test_custom_requires_subject_region_and_script(self):
        d=self.sample();d['scenes'][0]['visual']={'type':'custom','demonstration':'过滤粒子受筛孔选择性阻挡，形成截留与透过两种运动。'}
        with self.assertRaisesRegex(ValueError,'custom requires'):p.validate(d)
    def test_patent_must_not_be_spoken(self):
        d=self.sample();d['scenes'][0]['narration']='专利号为 CN107158754B。'
        with self.assertRaises(ValueError):p.validate(d)
    def test_broken_provenance_rejected(self):
        d=self.sample();d['facts'][0]['source_id']='invented'
        with self.assertRaises(ValueError):p.validate(d)
    def test_unknown_visual_cannot_silently_fallback(self):
        d=self.sample();d['scenes'][0]['visual']['type']='made_up'
        with self.assertRaises(ValueError):p.validate(d)
    def test_wrong_mode_rejected(self):
        d=self.sample();d['scenes'][0]['visual']['mode']='hotspot'
        with self.assertRaises(ValueError):p.validate(d)
    def test_exact_word_alignment(self):
        words=[{'text':'油','start':.1,'end':.3},{'text':'通过','start':.35,'end':.7},{'text':'水','start':.9,'end':1.1},{'text':'保留','start':1.2,'end':1.6}]
        c=p.align('油通过，水保留。',words)
        self.assertEqual([a['text'] for a in c],['油通过','水保留']);self.assertAlmostEqual(c[0]['start'],.4);self.assertAlmostEqual(c[1]['end'],1.9)
    def test_mismatched_audio_text_rejected(self):
        with self.assertRaises(ValueError):p.align('水保留。',[{'text':'油通过','start':0,'end':1}])
    def test_nonmonotonic_words_rejected(self):
        with self.assertRaises(ValueError):p.align('油水',[{'text':'油','start':1,'end':2},{'text':'水','start':.5,'end':1}])
    def test_stale_timeline_rejected(self):
        d=self.sample()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);p.write(out/'timeline.json',{'project_hash':p.data_hash(d)})
            p.checkpoint(d,out);d['scenes'][0]['narration']='新的文案。'
            with self.assertRaises(ValueError):p.checkpoint(d,out)
    def test_portable_asset_resolution(self):
        self.assertEqual(p.asset('@skill/assets/Inspired.mp3',Path.cwd()/'unrelated/project.json'),(ROOT/'assets/Inspired.mp3').resolve())
    def test_closing_title_cannot_silently_change_patent(self):
        d=self.sample();d['closing_lines']=['另一个项目名称']
        with self.assertRaises(ValueError):p.validate(d)
if __name__=='__main__':unittest.main()
