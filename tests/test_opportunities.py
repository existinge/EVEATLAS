import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('opportunities',Path(__file__).resolve().parents[1]/'tools/opportunities.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
class TestOpportunity(unittest.TestCase):
 def test_missing_is_unknown(self):
  r=o.score({'id':'t','pain':3});self.assertFalse(r['complete']);self.assertIn('payment_evidence',r['unknown'])
 def test_complete(self):
  sample={k:1 for k in (*o.POS,*o.NEG)};self.assertTrue(o.score(sample)['complete'])
 def test_out_of_range(self):
  with self.assertRaises(ValueError):o.score({'pain':6})
if __name__=='__main__':unittest.main()
