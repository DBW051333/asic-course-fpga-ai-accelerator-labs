#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,tarfile
ROOT=Path(__file__).resolve().parent
entries=json.loads((ROOT/'inventory.json').read_text())
count=0
for e in entries:
 p=ROOT/e['archive']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==e['archive_sha256'],str(p)
 expected={f['path']:f for f in e['files'] if f['retained']}
 with tarfile.open(p,'r:gz') as t:
  assert set(t.getnames())==set(expected),str(p)
  for name,f in expected.items():
   assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==f['sha256'],name
   count+=1
print('PASS:',len(entries),'failure archives,',count,'retained files and all SHA-256 values verified')
