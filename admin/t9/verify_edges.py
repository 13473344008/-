from verify_api import *
import helpers as h
h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
for role in ['editor','reviewer']:tokens[role]=login(users[role]['username'],cred['test_password'])
f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());pid=f['product_id']
def reopen(bid):
 with db() as c:c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=?",(bid,))
 submit(bid);assert decision(bid).get('code')==200
try:
 b,a=approved(pid,'REALDB',True);first=publish(b)['data'];oldpath=rt/'publish/published'/('TEST-T9-REALDB-'+runid+'.json');old=oldpath.read_bytes();reopen(b)
 with db() as c:c.execute("CREATE TRIGGER t9_fault_db_commit BEFORE UPDATE OF published_at ON passport_revisions WHEN NEW.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'injected T9 actual DB finalize failure'); END")
 try:result=publish(b)
 finally:
  with db() as c:c.execute('DROP TRIGGER t9_fault_db_commit')
 check('Real final DB transaction failure enters recovery',result['data']['record']['publish_status']=='recovery_required')
 check('After rename actual current is new, DB remains old',oldpath.read_bytes()!=old and ok('passport-batches/'+b+'/publication')['current']['id']==first['revision']['id'])
 check('Recovery lock prevents new attempt',publish(b).get('code')==409)
 r=ok('passport-batches/'+b+'/publication/reconcile',{});check('Reconcile confirms same original record',r['record']['id']==result['data']['record']['id'] and r['record']['publish_status']=='published')
 check('V1 historical file preserved after DB recovery',(rt/'publish'/first['revision']['snapshot_path']).read_bytes()==old)
 # Real source-integrity and symlink failures with an existing published head.
 for kind in ['hash','symlink','missing']:
  reopen(b);source=rt/'private-media'/a['key'];original=source.read_bytes();source.unlink()
  if kind=='hash':source.write_bytes(png((255,0,0)))
  elif kind=='symlink':source.symlink_to('/etc/hosts')
  before=oldpath.read_bytes()
  try:failed=publish(b)
  finally:
   if source.exists() or source.is_symlink():source.unlink()
   source.write_bytes(original)
  check('Source '+kind+' fails safely',failed.get('code')==200 and failed['data']['record']['publish_status']=='failed' and oldpath.read_bytes()==before)
  retry=publish(b);check('Source '+kind+' repaired retry',retry['data']['record']['publish_status']=='published')
 # Malformed declared PNG cannot enter approved frozen assets.
 invalidbatch=batch(pid,'TEST-T9-MIME-'+runid);assetInfo=asset(invalidbatch);source=rt/'private-media'/assetInfo['key'];original=source.read_bytes();source.write_bytes(b'<html><script>not an image</script></html>')
 try:ready=ok('passport-batches/'+invalidbatch+'/review/readiness')
 finally:source.write_bytes(original)
 check('HTML disguised as image rejected before submit',not ready['ready'])
 # Unknown request fields fail strict decode, no arbitrary raw public payload API.
 readybatch,_=approved(pid,'UNKNOWN');request=pubreq(readybatch)
 check('Client supplied public JSON forbidden',publish(readybatch,{**request,'payload':{'fake':True}}).get('code')==422)
 # Static and DB hashes without trusting API status alone.
 with db() as c:
  for rid,ph,snapshot,payload in c.execute('select id,payload_hash,snapshot_path,payload from passport_revisions where published_at is not null'):
   raw=(rt/'publish'/snapshot).read_bytes();check('Persisted actual snapshot '+rid,hashlib.sha256(raw).hexdigest()==ph and raw.decode()==payload)
 check('Edges integrity',scalar('pragma integrity_check')=='ok')
 with db() as c:check('Edges foreign keys',c.execute('pragma foreign_key_check').fetchall()==[])
finally:(rt/'test-artifacts/edges.json').write_text(json.dumps(checks,indent=2))
