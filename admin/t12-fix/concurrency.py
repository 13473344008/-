from flow import *
auth();results={}
def race(fn,values):
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:return list(pool.map(fn,values))
try:
 pid,rid=product('PF-T12-TEST-CONCURRENCY');p='passport-products/'+pid
 out=race(lambda _:req(p+'/revisions',{'source_revision_id':rid},token='editor'),range(5));results['revision']=out
 with db() as c:
  nums=[x[0] for x in c.execute('select revision_number from product_revisions where product_id=?',(pid,))]
 check('Concurrent Revision numbers unique',len(nums)==len(set(nums)) and len(nums)>=2)
 data={'product_id':pid,'batch_code':'PF-T12-TEST-RACE','record_type':'test','content':{'production_date':'2026-09-10','expiry_date':'2027-09-10','quality_status':'pending'},'overrides':[],'inspections':[]};out=race(lambda _:req('passport-batches',data,token='editor'),range(5));results['batch']=out;check('Same Batch code one success',sum(x['code']==200 for x in out)==1);b=next(x['data']['id'] for x in out if x['code']==200);bp='passport-batches/'+b
 v=ok(bp)['batch']['edit_version'];out=race(lambda _:req(bp+'/review/submit',{'expected_edit_version':v},token='editor'),range(5));results['submit']=out;check('Concurrent Submit exactly one attempt',sum(x['code']==200 for x in out)==1 and len(ok(bp+'/review')['history'])==1)
 review=ok(bp+'/review')['current'];q={'review_id':review['id'],'candidate_hash':review['candidate_hash'],'rejection_reason':'T12 concurrent rejection'};out=race(lambda action:req(bp+'/review/'+action,q,token='reviewer'),['approve','reject','approve','reject','approve']);results['decision']=out;check('Concurrent Approve Reject exactly one decision',sum(x['code']==200 for x in out)==1)
 if ok(bp+'/review')['state']=='draft':submit(b);check('Race rejected candidate reapproved',decision(b)['code']==200)
 out=race(lambda q:publish(b,q),[pubreq(b) for _ in range(5)]);results['publish']=out;check('Concurrent Publish exactly one success',sum(x.get('code')==200 and x['data']['record']['publish_status']=='published' for x in out)==1)
 current=ok(bp+'/publication')['current']['id'];out=race(lambda _:req(bp+'/publication/rollback',{'target_revision_id':current,'expected_current_revision_id':current,'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 concurrent rollback'}),range(5));results['rollback']=out;check('Concurrent Rollback exactly one success',sum(x.get('code')==200 and x['data']['record']['publish_status']=='published' for x in out)==1)
 check('No duplicate Published versions',scalar('select count(*) from passport_revisions where batch_id=? and published_at is not null',(b,))==2)
 ownpid,ownrid=product('PF-T12-TEST-SELF',token='editor_reviewer');own=batch(ownpid,'PF-T12-TEST-SELF',token='editor_reviewer');submit(own,token='editor_reviewer');check('Combined EditorReviewer selfapproval denied',decision(own,token='editor_reviewer')['code']==403)
 fault,aa=approved(pid,'FAULT');res=publish(fault);check('Separate fault fixture real API publication',res['data']['record']['publish_status']=='published');(rt/'test-artifacts/fault-fixture.json').write_text(json.dumps({'batch_id':fault,'target':res['data']['revision']['id']}))
finally:
 (rt/'test-artifacts/concurrency.json').write_text(json.dumps({'checks':checks,'responses':results,'response_database_locked_mentions':sum('database is locked' in json.dumps(x).lower() for x in results.values())},ensure_ascii=False,indent=2))
