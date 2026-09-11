from flow import *
auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 v=ok(bp+'/publication');check('Real UI V1 published',v['current']['version_number']==1 and v['state']=='published');f['versions']=[v['current']['id']];save(f)
 p=json.loads((rt/'publish/published/PF-T12-TEST-001.json').read_text());check('V1 two real uploaded images',len(p['assets'])==2);check('PNG and JPEG normalized to PNG',all(a['mime_type']=='image/png' for a in p['assets']))
 print(p['assets'],flush=True)
 files={str(q.relative_to(rt/'publish')):hashlib.sha256(q.read_bytes()).hexdigest() for q in (rt/'publish').rglob('*') if q.is_file()};(rt/'test-artifacts/v1-files.json').write_text(json.dumps(files,indent=2))
 with db() as c:
  c.row_factory=sqlite3.Row
  source=dict(c.execute('select * from batches where id=?',(b,)).fetchone());audit=c.execute('select * from passport_audit_events where batch_id=? order by id',(b,)).fetchall()
 (rt/'test-artifacts/clone-source-before.json').write_text(json.dumps({'batch':source,'audit':[dict(x) for x in audit]},indent=2))
finally:(rt/'test-artifacts/v1-checks.json').write_text(json.dumps(checks,indent=2))
