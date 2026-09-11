from flow import *
from media_checks import upload
auth()
try:
 pid=ok('passport-products',{'product_code':'PF-T12-TEST-DB-FAILURE','content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'DB fault TEST','process_labels':{}}]},token='editor')['id'];rid=ok('passport-products/'+pid)['revisions'][0]['id'];rp=f'passport-products/{pid}/revisions/{rid}'
 check('Fault main image formal upload',upload(rp+'/media','fault-main.png','image/png',png([171,22,43]))['code']==200);sid=putsection(rp+'/sections',section('fault_gallery','asset_gallery'));check('Fault gallery formal upload',upload(rp+'/sections/'+sid+'/media','fault-gallery.png','image/png',png([41,54,193]))['code']==200);ok(rp+'/seal',{'expected_token':ok(rp)['token']},token='editor');ok('passport-products/'+pid+'/default-revision',{'revision_id':rid,'expected_current_revision_id':None},'PUT','editor');b=batch(pid,'PF-T12-TEST-DB-FAILURE');bp='passport-batches/'+b;submit(b);decision(b);v1=publish(b)['data'];check('Fault V1 with actual two images',v1['record']['asset_count']==2)
 with db() as c:
  c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=? AND workflow_status='published'",(b,))
 submit(b);decision(b);request=pubreq(b)
 with db() as c:c.execute("CREATE TRIGGER t12_fix_finalize BEFORE UPDATE OF published_at ON passport_revisions WHEN NEW.batch_id='"+b+"' AND NEW.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'T12 injected SQLite finalize failure'); END")
 try:
  r=publish(b,request);check('Actual ordinary Publish SQLite failure',r['code']==200 and r['data']['record']['publish_status']=='recovery_required');check('DB failure classified after file switch',ok(bp+'/publication/health')['classification']=='file_switched_db_pending');check('DB Current still old',ok(bp+'/publication')['current']['id']==v1['revision']['id']);check('Recovery blocks new Publish',publish(b)['code']==409);check('Recovery blocks Rollback',req(bp+'/publication/rollback',{'target_revision_id':v1['revision']['id'],'expected_current_revision_id':v1['revision']['id'],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 blocked test'})['code']==409)
 finally:
  with db() as c:c.execute('DROP TRIGGER t12_fix_finalize')
 (rt/'test-artifacts/db-failure-state.json').write_text(json.dumps({'batch_id':b,'target':v1['revision']['id'],'operation':r['data']['record']['id'],'request':request},indent=2))
finally:(rt/'test-artifacts/db-failure.json').write_text(json.dumps(checks,indent=2))
