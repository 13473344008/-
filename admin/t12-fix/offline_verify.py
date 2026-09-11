from pathlib import Path
import sqlite3,json,hashlib
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t12-fix';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
with sqlite3.connect(rt/'db/passport-admin-t12-fix.db') as c:
 c.row_factory=sqlite3.Row
 for row in c.execute('select p.*,b.batch_code,r.id record_id,r.asset_count from passport_revisions p join batches b on b.id=p.batch_id join publish_records r on r.passport_revision_id=p.id where p.sealed_at is not null'):
  v=dict(row);expected={k:v[k] for k in ['version_number','batch_code','release_identifier','payload_hash','content_hash','asset_manifest_hash','asset_count','snapshot_path','schema_version','builder_version']};expected.update(publish_record_id=v['record_id'],passport_revision_id=v['id'],review_id=v['source_review_record_id']);raw=(rt/'releases/manifests'/(v['release_identifier']+'.json')).read_bytes()
  check('Exact Manifest all fields '+v['snapshot_path'],raw==json.dumps(expected,separators=(',',':'),sort_keys=True).encode())
  check('Payload Hash '+v['snapshot_path'],hashlib.sha256((rt/'publish'/v['snapshot_path']).read_bytes()).hexdigest()==v['payload_hash'])
 check('SQLite final integrity',c.execute('pragma integrity_check').fetchone()[0]=='ok');check('SQLite final FK',not c.execute('pragma foreign_key_check').fetchall())
 for b in c.execute('select batch_code,current_passport_revision_id from batches where current_passport_revision_id is not null').fetchall():
  h=c.execute('select payload_hash from passport_revisions where id=?',(b[1],)).fetchone()[0];check('Current matches confirmed DB '+b[0],hashlib.sha256((rt/'publish/published'/(b[0]+'.json')).read_bytes()).hexdigest()==h)
for label,file in [('T4-T11 protection','protected-before.json'),('53 baseline','baseline-before.json')]:
 hashes=json.loads((r/'runtime/t12/test-artifacts'/file).read_text());check(label,all((r/p).is_file() and hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in hashes.items()))
(rt/'test-artifacts/offline-verify.json').write_text(json.dumps({'checks':checks},indent=2))
