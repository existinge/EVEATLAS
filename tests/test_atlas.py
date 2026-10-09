import importlib.util, tempfile, unittest
from pathlib import Path
MODULE_PATH=Path(__file__).resolve().parents[1]/'tools'/'atlas.py'
spec=importlib.util.spec_from_file_location('atlas',MODULE_PATH);atlas=importlib.util.module_from_spec(spec);spec.loader.exec_module(atlas)
class AuditTest(unittest.TestCase):
    def test_valid_wikilink(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'Home.md').write_text('[[Page]]');(root/'Page.md').write_text('# Page')
            self.assertEqual(atlas.audit(root),[])
    def test_broken_link(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'Home.md').write_text('[[Missing]]')
            self.assertEqual(len(atlas.audit(root)),1)
    def test_secret_signature(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'Home.md').write_text('-----BEGIN OPENSSH PRIVATE KEY-----')
            self.assertEqual(len(atlas.audit(root)),1)
if __name__=='__main__':unittest.main()
