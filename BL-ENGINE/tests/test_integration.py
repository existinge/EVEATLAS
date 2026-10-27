import json
import sys
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.workbook import import_canonical
from engine.cli import run
from engine.identity import resolve

def workbook(path):
    # Minimal valid OOXML workbook exercising inline strings and old cached error cells.
    sheetnames=["WATCH","Alias Map","Viewing Reconciliation 2026","Oct 2026 Overrides"]
    data=[
      [["Title","Status","Country","Region Group","Year"],["Boys Be Brave!","Completed","South Korea","","2024"],["Duty First, Kiss Later","Completed","Japan","","2026"],["Crush on You","Maybe","Thailand","","2025"]],
      [["Canonical Title","Alias","Normalized Alias"],["Boys Be Brave!","고백을 못하고","#NAME?"]],
      [["Title","Status from user","Context","Date reviewed"],["Boys Be Brave!","Completed","","2026-10-26"]],
      [["Title","User status","Last updated"],["Crush on You","Dropped / Do Not Recommend","2026-10-27"]]
    ]
    def xmlsheet(rows):
      out=['<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
      for ri,row in enumerate(rows,1):
        out.append(f'<row r="{ri}">')
        for ci,val in enumerate(row):
          col=chr(65+ci)
          out.append(f'<c r="{col}{ri}" t="inlineStr"><is><t>{escape(val)}</t></is></c>')
        out.append('</row>')
      out.append('</sheetData></worksheet>')
      return ''.join(out)
    with ZipFile(path,"w") as z:
      z.writestr("xl/workbook.xml",'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{n}" sheetId="{i}" r:id="rId{i}"/>' for i,n in enumerate(sheetnames,1))+'</sheets></workbook>')
      z.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>' for i in range(1,5))+'</Relationships>')
      for i,rows in enumerate(data,1):z.writestr(f"xl/worksheets/sheet{i}.xml",xmlsheet(rows))

class Integration(unittest.TestCase):
 def test_end_to_end(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);w=d/"canonical.xlsx";workbook(w)
   loaded=import_canonical(w)
   self.assertEqual(loaded["diagnostics"]["watch_rows"],3)
   self.assertEqual(resolve("고백을 못하고",loaded["records"])["state"],"matched")
   candidates=[{"title":"고백을 못하고"},{"title":"Crush on You"},
               {"title":"Novel BL","criteria":{k:1 for k in ["romance_payoff","acting_chemistry","plot_stakes","pursuit","visual_fit","pacing"]}}]
   (d/"candidates.json").write_text(json.dumps(candidates),encoding="utf-8")
   result=run(w,d/"candidates.json",d/"report.json")
   self.assertEqual(result["summary"]["excluded"],2)
   self.assertEqual(result["summary"]["unknown_discoveries"],1)
   self.assertEqual(result["summary"]["recommendations"],0)
   self.assertEqual(result["results"]["unknown_discoveries"][0]["fit_score"],10)
   self.assertEqual(len(loaded["diagnostics"]["unmatched_overrides"]),0)
   self.assertEqual(len(loaded["diagnostics"]["ambiguous_overrides"]),0)

if __name__=="__main__":unittest.main()
