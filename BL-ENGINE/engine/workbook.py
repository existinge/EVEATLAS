"""Private XLSX canonical watch-history loader using Python's standard library.

No workbook bytes are committed; supplied XLSX is read-only.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import re
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from .identity import normalize

NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
PKG="http://schemas.openxmlformats.org/package/2006/relationships"

def _rows(archive, path, strings):
    root=ET.fromstring(archive.read(path))
    for row in root.findall(".//m:sheetData/m:row",NS):
        cells={}
        for cell in row.findall("m:c",NS):
            col=re.match(r"[A-Z]+",cell.attrib["r"]).group()
            node=cell.find("m:v",NS)
            inline=cell.find("m:is/m:t",NS)
            value=(node.text if node is not None else (inline.text if inline is not None else None))
            if cell.attrib.get("t")=="s" and value is not None:
                value=strings[int(value)]
            # Discard error cells and formula-dependent alias values.
            if cell.attrib.get("t")=="e" or value in ("#NAME?","#REF!","#VALUE!"):
                value=None
            cells[col]=value
        yield cells

def read_workbook(path):
    """Read only specified factual columns; imported formula outputs are not trusted."""
    path=Path(path)
    sheets={}
    with ZipFile(path) as z:
        names=set(z.namelist())
        shared=[]
        if "xl/sharedStrings.xml" in names:
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for entry in root.findall("m:si",NS):
                shared.append("".join((t.text or "") for t in entry.findall(".//m:t",NS)))
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        relroot=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels={r.attrib["Id"]:r.attrib["Target"] for r in relroot.findall("{"+PKG+"}Relationship")}
        for item in workbook.findall(".//m:sheets/m:sheet",NS):
            name=item.attrib["name"]
            if name not in {"WATCH","Alias Map","Viewing Reconciliation 2026","Oct 2026 Overrides","Manual Overrides","Rejected Log"}:
                continue
            target=rels[item.attrib["{"+NS["r"]+"}id"]]
            target=target.lstrip("/")
            if not target.startswith("xl/"):target="xl/"+target
            if target in names:sheets[name]=list(_rows(z,target,shared))
    return sheets

def import_canonical(path):
    """Returns records, status events, and diagnostics. Does not write to the workbook."""
    sheets=read_workbook(path)
    if not sheets.get("WATCH"):
        raise ValueError("Canonical workbook lacks readable WATCH data")
    raw=sheets["WATCH"]
    records=[]; events=[]; diagnostics={"watch_rows":0,"unmatched_overrides":[],"ambiguous_overrides":[],"duplicate_keys":[]}
    for line,row in enumerate(raw[1:],start=2):
        title=(row.get("A") or "").strip()
        if not title:continue
        key=normalize(title)
        if not key:continue
        country=(row.get("C") or "").strip()
        year=row.get("E")
        try:year=int(float(year)) if year not in ("",None) else None
        except (ValueError,TypeError):year=None
        ident="watch-row-"+str(line)
        records.append({"id":ident,"title":title,"aliases":[],"country":country,"year":year,"source_row":line})
        status=(row.get("B") or "Unknown").strip()
        events.append({"production_id":ident,"status":status,"timestamp":"2026-01-01","source":"WATCH","sequence":0})
    diagnostics["watch_rows"]=len(records)
    by_title=defaultdict(list)
    for record in records:by_title[normalize(record["title"])].append(record)
    diagnostics["duplicate_keys"]=[k for k,v in by_title.items() if len(v)>1]

    # User corrections override old sheet status, but only for uniquely identified works.
    sheetspec=[
        ("Viewing Reconciliation 2026","A","B","D"),
        ("Oct 2026 Overrides","A","B","C"),
    ]
    for sheet,titlecol,statuscol,datecol in sheetspec:
        for i,row in enumerate(sheets.get(sheet,[])[1:],start=2):
            title=(row.get(titlecol) or "").strip()
            status=(row.get(statuscol) or "").strip()
            if not title or not status:continue
            match=by_title.get(normalize(title),[])
            if len(match)!=1:
                bucket="unmatched_overrides" if not match else "ambiguous_overrides"
                diagnostics[bucket].append({"sheet":sheet,"row":i,"title":title,"status":status})
                continue
            events.append({"production_id":match[0]["id"],"status":status,
                           "timestamp":str(row.get(datecol) or "2026-10-26"),
                           "source":sheet,"sequence":i})
    # Alias-map rows should connect to a UNIQUE canonical title, never to a guessed production.
    for row in sheets.get("Alias Map",[])[1:]:
        canonical=(row.get("A") or "").strip()
        alias=(row.get("B") or "").strip()
        if not canonical or not alias:continue
        matches=by_title.get(normalize(canonical),[])
        if len(matches)==1 and normalize(alias)!=normalize(canonical):
            if alias not in matches[0]["aliases"]:matches[0]["aliases"].append(alias)
    return {"records":records,"events":events,"diagnostics":diagnostics}
