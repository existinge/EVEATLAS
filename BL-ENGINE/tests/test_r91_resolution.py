import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.firecrawl_research import IdentityIndex
from engine.r91_resolution import ResolutionRegistry,R91Index,apply_private_overlay,resolve_prior_quarantine,interact_titles,LiveConnectorTransport

SRC=lambda u,e:{'url':u,'excerpt':e,'reviewed':True}
class R91Tests(unittest.TestCase):
 def setUp(self):
  self.idx=IdentityIndex();self.idx.add('Known English',['æ¢ç¥ä½å'],status='Completed',score=8)
  self.reg=ResolutionRegistry()
 def add(self,**kw):
  row=dict(title='åè£',aliases=['Candidate'],production_id='official:123',production_id_type='official_program_id',scope_class='target_male_male_live_action',source=SRC('https://example.invalid/123','paired native and English titles'),**kw);self.reg.add(row);return row
 def test_resolution_requires_attributable_id(self):
  with self.assertRaises(ValueError):self.reg.add(dict(title='X',production_id_type='slug',scope_class='non_bl',source=SRC('https://example.invalid/x','not BL')))
 def test_out_of_scope_excluded_not_added_to_history(self):
  self.reg.add(dict(title='Documentary',production_id='jfdb:1',production_id_type='jfdb',scope_class='documentary',source=SRC('https://example.invalid/doc','documentary')))
  r=R91Index(self.idx,self.reg).check({'title':'Documentary'});self.assertEqual(r['state'],'known');self.assertIn('verified_out_of_scope',r['reason']);self.assertNotIn('documentary',self.idx.by_key)
 def test_native_crosswalk_blocks_existing_english(self):
  self.reg.add(dict(title='æ¢ç¥ä½å',aliases=['Known English'],production_id='official:k',production_id_type='program',scope_class='target_male_male_live_action',source=SRC('https://example.invalid/k','same production')))
  self.assertEqual(R91Index(self.idx,self.reg).check({'title':'æ¢ç¥ä½å'})['state'],'known')
 def test_private_overlay_is_blocker_only(self):
  idx=IdentityIndex();apply_private_overlay(idx,[{'title':'Only for Fans','status':'Completed','score':4,'explicit':True}]);self.assertEqual(idx.check({'title':'Only for Fans'})['effective']['score'],4)
 def test_overlay_requires_explicit_history(self):
  with self.assertRaises(ValueError):apply_private_overlay(self.idx,[{'title':'Guess','status':'Completed'}])
 def test_target_survives_when_distinct(self):
  self.add(reviewed_novel=True,country='Japan',format='series');audit=resolve_prior_quarantine([{'candidate':{'title':'åè£'}}],self.reg,self.idx);self.assertEqual(len(audit['target_survivors']),1)
 def test_accounted_resolution_blocks(self):
  self.add(accounted_for=True);self.assertEqual(R91Index(self.idx,self.reg).check({'title':'Candidate'})['reason'],'recovered_accounted_identity')
 def test_edit_is_not_new(self):
  self.add(relation='edit',parent_title='Parent');self.assertEqual(R91Index(self.idx,self.reg).check({'title':'Candidate'})['reason'],'alternate_edit_not_new')
 def test_interact_pagination_envelope(self):
  r={'success':True,'scrapeId':'abc','stdout':'noise\n["A","B","A"]\n'};self.assertEqual(interact_titles(r),['A','B'])
  with self.assertRaises(ValueError):interact_titles({'success':False,'stdout':'[]'})
 def test_live_connector_contract(self):
  def invoke(op,args):return {'success':True,'scrapeId':'live-1','stdout':'["A"]'}
  t=LiveConnectorTransport(invoke);out=t('interact',{'url':'https://example.invalid/catalog'});self.assertTrue(out['success']);self.assertEqual(t.calls[0]['receipt_id'],'live-1')
 def test_resolution_collision_quarantines(self):
  self.add();self.reg.add(dict(title='Candidate',production_id='official:other',production_id_type='program',scope_class='target_male_male_live_action',source=SRC('https://example.invalid/o','other production')));self.assertEqual(R91Index(self.idx,self.reg).check({'title':'Candidate'})['state'],'quarantine')

 def test_verified_special_survives_parent_only_fuzzy(self):
  idx=IdentityIndex();idx.add("School Trip: Joined a Group I'm Not Close To",status='Completed')
  reg=ResolutionRegistry();reg.add(dict(title="School Trip : Joined a Group I'm Not Close To (Special)",production_id='official:special',production_id_type='program',scope_class='target_male_male_live_action',relation='special',parent_title="School Trip: Joined a Group I'm Not Close To",reviewed_novel=True,source=SRC('https://example.invalid/special','official distinct special')))
  r=R91Index(idx,reg).check({'title':"School Trip : Joined a Group I'm Not Close To (Special)"})
  self.assertEqual(r['state'],'unresolved')

if __name__=='__main__':unittest.main()
