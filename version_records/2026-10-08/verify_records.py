from pathlib import Path
import hashlib,json,tarfile
R=Path(__file__).resolve().parent
items=json.loads((R/'versions.json').read_text());inventory={e['version']:e['files'] for e in json.loads((R/'file_inventory.json').read_text())};count=0
for x in items:
 p=R/x['archive'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['archive_sha256'],str(p)
 expected={f['path']:f for f in inventory[x['version']] if f['recorded']}
 with tarfile.open(p,'r:gz') as t:
  assert set(t.getnames())==set(expected),str(p)
  for name,f in expected.items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==f['sha256'],name
 count+=len(expected)
assert sum(x['keep_project'] for x in items)==13
print('PASS:',len(items),'version archives,',count,'data/evidence files; SHA-256 and coverage verified')
