from pathlib import Path
import sqlite3,json,hashlib,sys,urllib.request
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t10';action=sys.argv[1]
def snapshot(root):
 db=root/'db'/('fresh-acceptance.db' if root.name=='fresh' else 'passport-admin-t10.db')
 with sqlite3.connect(db) as c:
  tables={t:c.execute('select * from '+t+' order by id').fetchall() for t in ['passport_revisions','publish_records','published_assets','review_records','passport_audit_events']}
  heads=c.execute('select id,current_passport_revision_id,active_publish_record_id,workflow_status,next_version_number from batches order by id').fetchall()
 files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['publish','releases/manifests'] for p in (root/folder).rglob('*') if p.is_file()}
 return {'tables':tables,'heads':heads,'files':files}
checks=[]
for root in [rt,rt/'fresh']:
 path=root/'test-artifacts/restart-before.json';now=snapshot(root)
 if action=='snapshot':path.write_text(json.dumps(now,ensure_ascii=False));continue
 before=json.loads(path.read_text());match=json.loads(json.dumps(now))==before;checks.append({'name':root.name+' exact DB/public/manifests restart persistence','status':'PASS' if match else 'FAIL'});assert match
if action!='snapshot':(rt/'test-artifacts/persistence.json').write_text(json.dumps(checks,indent=2))
