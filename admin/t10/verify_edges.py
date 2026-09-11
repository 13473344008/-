from verify_history import *
h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
for role in ['editor','reviewer','viewer']:tokens[role]=login(users[role]['username'],cred['test_password'])
f=json.loads((rt/'test-artifacts/history-fixtures.json').read_text());b=f['batch_id'];p='passport-batches/'+b+'/publication';target=f['versions'][0]['revision']['id']
try:
 for route in [p+'/versions/'+target,p+'/history',p+'/rollback',p+'/versions/'+target+'/assets',p+'/audit']:
  check('No DELETE '+route.split('/publication')[-1],req(route,{},'DELETE').get('code') in [404,405])
 for stage,x in f['faults'].items():
  hist=ok('passport-batches/'+x['batch_id']+'/publication/history');failed=next((v for v in hist['attempts'] if v['record']['publish_status']=='failed'),None)
  if failed:check('Failed attempt cannot be rollback target '+stage,roll(x['batch_id'],failed['revision']['id']).get('code') in [404,409])
 # Batch fixture still Draft; a real historical target of another batch does not enable it.
 draft=batch(f['product_id'],'TEST-T10-DRAFT-EDGE-'+runid)
 check('Draft rollback denied',req('passport-batches/'+draft+'/publication/rollback',{'target_revision_id':target,'expected_current_revision_id':None,'idempotency_key':str(uuid.uuid4()),'rollback_reason':'must deny Draft'}).get('code')==409)
 # Readonly detail accessible to all legitimate roles through live API.
 for role in ['viewer','editor','reviewer']:
  check('History detail accessible '+role,req(p+'/versions/'+target,token=role).get('code')==200)
 # Permanent history remains visible after product archive. No new work required for these fixtures.
 pid=f['product_id'];before=ok(p+'/history');check('Product archive succeeds',req('passport-products/'+pid+'/archive',{}).get('code')==200)
 after=ok(p+'/history');check('Product archive retains versions/reviews/attempts',all(before[k]==after[k] for k in ['versions','reviews','attempts']))
 check('Product archive retains release integrity',ok(p+'/versions/'+target+'/integrity')['state']=='verified')
 with db() as c:
  table_count=c.execute("select count(*) from sqlite_master where type='table' and name='publication_health'").fetchone()[0]
  check('Durable reconciliation status model',table_count==1)
finally:(rt/'test-artifacts/edges.json').write_text(json.dumps(checks,indent=2))
