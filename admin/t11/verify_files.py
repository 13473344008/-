from pathlib import Path
import hashlib,json,sqlite3
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t11';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
try:
 before=json.loads((rt/'test-artifacts/protected-before.json').read_text());changed=[p for p,h in before.items() if not (r/p).is_file() or hashlib.sha256((r/p).read_bytes()).hexdigest()!=h];check('All protected T4-T10 evidence and migrations unchanged',not changed)
 baseline=json.loads((rt/'test-artifacts/baseline-before.json').read_text());check('T0 baseline 53 files unchanged',len(baseline)==53 and all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in baseline.items()));check('POC seven backup files match',sum(p.startswith('site/') for p in baseline)==7 and all((rt/'baseline'/p).read_bytes()==(r/p).read_bytes() for p in baseline if p.startswith('site/')))
 with sqlite3.connect(rt/'db/passport-admin-t11.db') as c:
  check('SQLite integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check('SQLite foreign_key_check empty',c.execute('pragma foreign_key_check').fetchall()==[])
  for code,n,p,h,payload in c.execute('SELECT b.batch_code,p.version_number,p.snapshot_path,p.payload_hash,p.payload FROM passport_revisions p JOIN batches b ON b.id=p.batch_id WHERE p.published_at IS NOT NULL'):
   raw=(rt/'publish'/p).read_bytes();check('Frozen payload hash '+code+' v'+str(n),hashlib.sha256(raw).hexdigest()==h and raw.decode()==payload);v=json.loads(raw)
   for a in v['assets']:
    b=(rt/'publish'/a['path']).read_bytes();check('Frozen asset hash '+code+' v'+str(n),hashlib.sha256(b).hexdigest()==a['sha256'] and len(b)==a['file_size'])
   check('Public internal fields excluded '+code+' v'+str(n),all(x not in raw for x in [b'created_by',b'updated_by',b'review_id',b'candidate_hash',b'internal_note',b'storage_key',b'/Users/',b'PRIVATE-']))
 check('Public release has no private preview files',all(p.suffix in ['.json','.png'] and p.relative_to(rt/'publish').parts[0] in ['published','versions','assets'] for p in (rt/'publish').rglob('*') if p.is_file()))
 (rt/'test-artifacts/protection-summary.json').write_text(json.dumps({'protected_files':len(before),'changed':changed,'t0_files':len(baseline),'poc_files':7},indent=2))
finally:(rt/'test-artifacts/files.json').write_text(json.dumps(checks,indent=2));print(len(checks),'file checks')
