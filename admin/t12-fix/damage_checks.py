from flow import *
auth();f=json.loads((rt/'test-artifacts/db-failure-state.json').read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 current=ok(bp+'/publication');check('Browser Reconcile confirms original record',next(x for x in current['history'] if x['record']['id']==f['operation'])['record']['publish_status']=='published');check('Reconcile clears active lock',not current['active_record_id']);rid=f['target'];v=ok(bp+'/publication/versions/'+rid);rev=v['version']['revision'];check('Independent damage fixture has two assets',len(v['assets'])==2)
 snapshot=rt/'publish'/rev['snapshot_path'];payload=json.loads(snapshot.read_text());asset=rt/'publish'/payload['assets'][0]['path'];manifest=rt/'releases/manifests'/(rev['release_identifier']+'.json')
 oldcurrent=(rt/'publish/published/PF-T12-TEST-DB-FAILURE.json').read_bytes();out=[]
 for name,path in [('JSON',snapshot),('Asset',asset),('Manifest',manifest)]:
  raw=path.read_bytes()
  try:
   path.write_bytes(b'T12 controlled '+name.encode()+b' corruption');check('Corrupt '+name+' Verify fails',ok(bp+'/publication/versions/'+rid+'/integrity')['state']=='integrity_error');r=req(bp+'/publication/rollback',{'target_revision_id':rid,'expected_current_revision_id':current['current']['id'],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 reject corrupt '+name});check('Corrupt '+name+' Rollback rejected',r['code']==409);check('Corrupt '+name+' cannot change Current',(rt/'publish/published/PF-T12-TEST-DB-FAILURE.json').read_bytes()==oldcurrent);out.append({'kind':name,'path':str(path.relative_to(rt)),'status':r['code'],'current_unchanged':True})
  finally:path.write_bytes(raw)
  check('Restored '+name+' integrity verified',ok(bp+'/publication/versions/'+rid+'/integrity')['state']=='verified')
 (rt/'test-artifacts/damage-details.json').write_text(json.dumps(out,indent=2))
finally:(rt/'test-artifacts/damage-checks.json').write_text(json.dumps(checks,indent=2))
