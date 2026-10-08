#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifests/files.json').read_text())
for name,e in manifest.items():
    p=ROOT/name
    assert p.is_file(), 'Missing: '+name
    assert p.stat().st_size==e['size'], 'Size mismatch: '+name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'], 'Hash mismatch: '+name
actual={str(p.relative_to(ROOT)) for group in ['projects','course_materials'] for p in (ROOT/group).rglob('*') if p.is_file()}
assert actual==set(manifest), 'File coverage mismatch'
print('PASS:',len(manifest),'files; all SHA-256 values and paths verified')
