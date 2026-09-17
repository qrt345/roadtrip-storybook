"""Behavioral regression checks for the reusable builder; no network required."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'roadtrip-storybook'
spec=importlib.util.spec_from_file_location('trip_build',SKILL/'scripts/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.data=json.loads((SKILL/'assets/examples/mountain-rail.json').read_text(encoding='utf-8'))

    def tearDown(self): self.temp.cleanup()

    def write(self,name,data):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return p

    def run_build(self,*args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return builder.main([str(x) for x in args])

    def test_single_build_and_existing_output_protection(self):
        source=self.write('trip.json',self.data);output=self.root/'trip.html'
        self.assertEqual(self.run_build('--input',source,'--output',output),0)
        output.write_text('existing user file',encoding='utf-8')
        self.assertEqual(self.run_build('--input',source,'--output',output),1)
        self.assertEqual(output.read_text(),'existing user file')
        self.assertEqual(self.run_build('--input',source,'--output',output,'--force'),0)
        self.assertIn('id="trip-data"',output.read_text(encoding='utf-8'))

    def test_batch_invalid_file_produces_no_partial_outputs(self):
        self.write('input/a.json',self.data)
        invalid=copy.deepcopy(self.data);invalid['id']='broken';invalid['pages'][0]['map']['legs'][0]['to']='missing'
        self.write('input/b.json',invalid)
        self.assertEqual(self.run_build('--batch',self.root/'input','--out-dir',self.root/'out'),1)
        self.assertFalse((self.root/'out').exists())

    def test_unique_trip_ids_required_for_batch(self):
        self.write('input/a.json',self.data);self.write('input/b.json',self.data)
        self.assertEqual(self.run_build('--batch',self.root/'input','--out-dir',self.root/'out'),1)
        self.assertFalse((self.root/'out').exists())

    def test_source_cannot_escape_input_directory(self):
        (self.root/'private.md').write_text('not intended for the handout',encoding='utf-8')
        self.data['source_md']='../private.md'
        source=self.write('input/trip.json',self.data)
        self.assertEqual(self.run_build('--input',source,'--output',self.root/'trip.html'),1)
        self.assertFalse((self.root/'trip.html').exists())

    def test_source_is_embedded_and_not_interpreted_as_html(self):
        (self.root/'source.md').write_text('# Source\n<script>window.bad=true</script>\nFinal source line',encoding='utf-8')
        self.data['source_md']='source.md'
        source=self.write('trip.json',self.data);output=self.root/'trip.html'
        self.assertEqual(self.run_build('--input',source,'--output',output),0)
        html=output.read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;window.bad=true&lt;/script&gt;',html)
        self.assertIn('Final source line',html)

    def test_embedded_json_cannot_terminate_script(self):
        self.data['pages'][0]['title']='</script><script>window.injected=true</script>'
        self.data['pages'][0]['accent_line']=0
        result=builder.render(builder.validate(self.data),'')
        self.assertNotIn('</script><script>window.injected',result)
        self.assertIn('\\u003c/script\\u003e',result)

    def test_data_that_looks_like_template_marker_stays_data(self):
        self.data['title']='__DATA__'
        result=builder.render(self.data,'')
        self.assertIn('<title>__DATA__</title>',result)

    def test_check_only_writes_nothing(self):
        source=self.write('trip.json',self.data)
        self.assertEqual(self.run_build('--input',source,'--check'),0)
        self.assertEqual([p.name for p in self.root.iterdir()],['trip.json'])

    def test_one_page_and_no_route_supported(self):
        self.data['pages']=self.data['pages'][2:]
        self.data['pages'][0]['map']['legs']=[]
        source=self.write('trip.json',self.data)
        self.assertEqual(self.run_build('--input',source,'--output',self.root/'trip.html'),0)

    def test_invalid_page_reference_rejected(self):
        self.data['pages'][0]['map']['nodes'][0]['page']='nonexistent'
        with self.assertRaises(ValueError):builder.validate(self.data)

    def test_nonfinite_coordinates_and_css_injection_rejected(self):
        self.data['pages'][0]['map']['nodes'][0].update(x=float('nan'),y=150)
        with self.assertRaises(ValueError):builder.validate(self.data)
        self.data['pages'][0]['map']['nodes'][0].update(x=150,y=150)
        self.data['theme']['accent']='red;display:none'
        with self.assertRaises(ValueError):builder.validate(self.data)

    def test_plain_data_fields_reject_html_objects_and_typos(self):
        self.data['pages'][0]['title']={'html':'<b>hello</b>'}
        with self.assertRaises(ValueError):builder.validate(self.data)
        self.data['pages'][0]['title']='valid';self.data['pages'][0]['sectons']=[]
        with self.assertRaises(ValueError):builder.validate(self.data)


if __name__=='__main__':unittest.main(verbosity=2)
