from flow import *
auth();f=json.loads((rt/'test-artifacts/fault-fixture.json').read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 old=ok(bp+'/publication')['current'];request={'target_revision_id':f['target'],'expected_current_revision_id':old['id'],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 actual SQLite finalize failure'}
 with db() as c:c.execute("CREATE TRIGGER t12_fault_finalize BEFORE UPDATE OF published_at ON passport_revisions WHEN NEW.batch_id='"+b+"' AND NEW.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'T12 injected finalize failure'); END")
 try:
  r=ok(bp+'/publication/rollback',request);check('Actual SQLite failure enters recovery_required',r['record']['publish_status']=='recovery_required');health=ok(bp+'/publication/health');check('Actual file switched DB pending classification',health['classification']=='file_switched_db_pending')
  check('Recovery blocks API Publish',publish(b)['code']==409);check('Recovery blocks API Rollback',req(bp+'/publication/rollback',{**request,'idempotency_key':str(uuid.uuid4())})['code']==409)
 finally:
  with db() as c:c.execute('DROP TRIGGER t12_fault_finalize')
 recovered=ok(bp+'/publication/reconcile',{'reason':'T12 TEST — reconcile after controlled SQLite finalize failure'});check('Admin reconcile finalizes original operation',recovered['record']['id']==r['record']['id'] and recovered['record']['publish_status']=='published')
 version=ok(bp+'/publication/versions/'+f['target']);target=rt/'publish'/version['version']['revision']['snapshot_path'] if 'revision' in version['version'] else None
 if target is None:
  with db() as c:target=rt/'publish'/c.execute('select snapshot_path from passport_revisions where id=?',(f['target'],)).fetchone()[0]
 raw=target.read_bytes()
 try:
  target.write_bytes(b'{T12-corrupted-json');check('Corrupt JSON integrity error',ok(bp+'/publication/versions/'+f['target']+'/integrity')['state']=='integrity_error')
  check('Corrupt version rollback rejected',req(bp+'/publication/rollback',{'target_revision_id':f['target'],'expected_current_revision_id':recovered['revision']['id'],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 corrupt target must fail'})['code']==409)
 finally:target.write_bytes(raw)
 check('Restored JSON full verification succeeds',ok(bp+'/publication/versions/'+f['target']+'/integrity')['state']=='verified')
finally:(rt/'test-artifacts/failure-api.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
