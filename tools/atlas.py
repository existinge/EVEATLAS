#!/usr/bin/env python3
"""Dependency-free vault hygiene and diff review helper; NOT a security scanner."""
from pathlib import Path
import argparse, re, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
WIKILINK = re.compile(r'(?<!!)\[\[([^\]]+)\]\]')
SECRET = re.compile(r'(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')

def audit(root=ROOT):
    files = list(root.rglob('*.md'))
    names = {}
    for f in files:
        if '.git' in f.parts: continue
        names.setdefault(f.stem.casefold(), []).append(f)
    errors = []
    for f in files:
        if '.git' in f.parts: continue
        source = f.read_text(encoding='utf-8')
        if SECRET.search(source): errors.append(f'{f.relative_to(root)}: possible exposed credential')
        for raw in WIKILINK.findall(source):
            target = raw.split('|',1)[0].split('#',1)[0].strip()
            if not target: continue
            direct = root / (target if target.endswith('.md') else target+'.md')
            if direct.is_file(): continue
            stem = Path(target).stem.casefold()
            matches = names.get(stem,[])
            if len(matches)==1: continue
            errors.append(f'{f.relative_to(root)}: unresolved/ambiguous wikilink [[{raw}]]')
    return errors

def review(base):
    try:
        changed = subprocess.check_output(['git','diff','--name-status',f'{base}...HEAD'], cwd=ROOT, text=True,stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print('Cannot read Git diff; fetch/check base ref:',str(e));return 2
    print('Changed files relative to',base,':\n',changed or '(none)')
    bad = [x for x in changed.splitlines() if x.startswith('D\t')]
    if bad: print('REVIEW REQUIRED: deletions present')
    errs=audit()
    for err in errs:print('ERROR:',err)
    print('Human + independent agent review still required; this is NOT an approval.')
    return 1 if errs or bad else 0

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('audit'); new=sub.add_parser('new-project');new.add_argument('slug');new.add_argument('title')
    rev=sub.add_parser('review');rev.add_argument('--base',default='origin/main')
    a=p.parse_args()
    if a.action=='audit':
        errs=audit()
        for e in errs:print('ERROR:',e)
        print(f'Vault audit: {len(errs)} issue(s)')
        return bool(errs)
    if a.action=='review':return review(a.base)
    if not re.fullmatch('[a-z0-9][a-z0-9-]*',a.slug):p.error('slug must be lowercase kebab-case')
    f=ROOT/'01-Projects'/f'{a.slug}.md'
    if f.exists():print('Refusing to overwrite:',f);return 1
    template=(ROOT/'06-Templates/Project Template.md').read_text(encoding='utf-8')
    f.write_text(template.replace('Project Name',a.title,1),encoding='utf-8')
    print('Created:',f.relative_to(ROOT));return 0
if __name__=='__main__':sys.exit(main())
