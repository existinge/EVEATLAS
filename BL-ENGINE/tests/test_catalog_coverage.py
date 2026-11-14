import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.catalog_coverage import Crosswalk,CatalogIndex,catalog_batches,run_catalog_round,ConnectorReplayTransport
from engine.firecrawl_research import IdentityIndex,FirecrawlProvider

class CatalogTests(unittest.TestCase):
 def setUp(self):
  self.idx=IdentityIndex();self.idx.add('Original Romance', ['原作'],status='Completed');self.idx.add('Known Series', ['既知'],status='Skip');self.cw=Crosswalk()
 def row(self,**kw):return dict(title='Original Romance Season 2',production_id='synthetic-s2',relation='sequel',parent_title='Original Romance',reviewed_novel=True,source={'url':'https://example.invalid/season2','reviewed':True,'excerpt':'New season, original cast'},**kw)
 def test_reviewed_alias(self):
  self.cw.add(dict(title='Known Series',aliases=['新しい別名'],production_id='known',source={'url':'https://example.invalid/known','reviewed':True,'excerpt':'Both names'}));self.assertEqual(CatalogIndex(self.idx,self.cw).check({'title':'新しい別名'})['state'],'known')
 def test_no_unverified_crosswalk(self):
  with self.assertRaises(ValueError):self.cw.add(dict(title='X',production_id='x',source={'url':'https://example.invalid/x'}))
 def test_sequel_parent_only(self):
  self.cw.add(self.row());self.assertEqual(CatalogIndex(self.idx,self.cw).check({'title':'Original Romance Season 2'})['state'],'unresolved')
 def test_exact_sequel_blocks(self):
  self.cw.add(self.row());self.idx.add('Original Romance Season 2',status='Skip');self.assertEqual(CatalogIndex(self.idx,self.cw).check({'title':'Original Romance Season 2'})['state'],'known')
 def test_edit_not_new(self):
  row=self.row();row['relation']='edit';self.cw.add(row);self.assertEqual(CatalogIndex(self.idx,self.cw).check({'title':row['title']})['reason'],'alternate_edit_not_new')
 def test_catalog_failure_continues(self):
  def transport(op,args):
   if args['url'].endswith('/bad'):raise RuntimeError('TLS failure')
   return {'json':{'titles':[{'title':'Known Series'}]}}
  plan=[{'id':'bad','url':'https://example.invalid/bad'},{'id':'good','url':'https://example.invalid/good'}];calls=[]
  result=run_catalog_round(self.idx,self.cw,FirecrawlProvider(transport),plan,lambda c:calls.append(c))
  self.assertEqual([x['status'] for x in result['coverage']],['failed','retrieved']);self.assertEqual(len(result['excluded']),1);self.assertFalse(calls)
 def test_coverage_not_exhaustive(self):
  ledger=[];list(catalog_batches(FirecrawlProvider(lambda o,a:{'json':{'titles':[]},'next':'page2'}),[{'id':'x','url':'https://example.invalid/catalog'}],ledger));self.assertEqual(ledger[0]['status'],'partial');self.assertFalse(ledger[0]['coverage_complete'])

 def test_crosswalk_dedup(self):
  self.cw.add(dict(title='Unseen Film',aliases=['新作映画'],production_id='new',reviewed_novel=True,source={'url':'https://example.invalid/film','reviewed':True,'excerpt':'Both titles'}))
  provider=FirecrawlProvider(lambda o,a:{'json':{'titles':[{'title':'Unseen Film'},{'title':'新作映画'}]}})
  calls=[]; result=run_catalog_round(self.idx,self.cw,provider,[{'id':'x','url':'https://example.invalid/catalog'}],lambda c:calls.append(c) or c)
  self.assertEqual(len(calls),1);self.assertEqual(result['coverage'][0]['crosswalk_duplicates'],1)
 def test_connector_replay(self):
  t=ConnectorReplayTransport([{'operation':'scrape','selector':'https://example.invalid/catalog','receipt_id':'test','response':{'json':{'titles':[]}}}]); p=FirecrawlProvider(t)
  p.extract('https://example.invalid/catalog',{},'public'); self.assertEqual(t.calls[0]['receipt_id'],'test')
  with self.assertRaises(RuntimeError):p.extract('https://example.invalid/unknown',{},'public')
 def test_body_error(self):
  ledger=[];list(catalog_batches(FirecrawlProvider(lambda o,a:{'metadata':{'statusCode':200},'body_error':'401','json':{'titles':[{'title':'Fake'}]}}),[{'id':'x','url':'https://example.invalid/catalog'}],ledger));self.assertEqual(ledger[0]['status'],'failed')

if __name__=='__main__':unittest.main()
