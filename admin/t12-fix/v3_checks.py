from flow import *
auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 v=ok(bp+'/publication')['current'];check('Rollback V3 new ID with V1 source',v['version_number']==3 and v['rollback_source_revision_id']==f['versions'][0] and v['id'] not in f['versions'][:2]);f['versions']=f['versions'][:2]+[v['id']];save(f)
 old=json.loads((rt/'test-artifacts/v2-files.json').read_text());check('Rollback preserves all old immutable JSON and images',all(hashlib.sha256((rt/'publish'/p).read_bytes()).hexdigest()==sha for p,sha in old.items() if not p.startswith('published/')))
 for i,rid in enumerate(f['versions'],1):check('V'+str(i)+' full integrity with images',ok(bp+'/publication/versions/'+rid+'/integrity')['state']=='verified')
 history=ok(bp+'/publication/history');(rt/'test-artifacts/main-history.json').write_text(json.dumps(history,indent=2));check('V1 V2 V3 retained',len(history['versions'])==3)
 cl=scalar("select id from batches where batch_code='PF-T12-TEST-CLONE-ROLLBACK'");check('Rolled back Published clone Draft',ok('passport-batches/'+cl)['batch']['workflow_status']=='draft')
 # No archive business endpoint exists at T12; set only this isolated clone status to exercise the explicitly unsupported source state.
 with db() as c:c.execute("UPDATE batches SET workflow_status='archived' WHERE id=? AND workflow_status='draft'",(cl,))
 check('Archived Clone explicitly rejected',req('passport-batches/'+cl+'/clone',{'batch_code':'PF-T12-TEST-CLONE-ARCHIVED','expected_edit_version':ok('passport-batches/'+cl)['batch']['edit_version']},token='editor')['code']==409)
finally:(rt/'test-artifacts/v3-checks.json').write_text(json.dumps(checks,indent=2))
