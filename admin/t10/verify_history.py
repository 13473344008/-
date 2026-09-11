from verify_api import *
import helpers as h

def reopen(b):
 # Controlled T10 fixture; does not bypass approval or change any historical record.
 with db() as c:c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=?",(b,))
def edit(b,n):
 w=work(b);w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':str(25 if n==1 else 20)},{'field_key':'package_unit','operation':'set','value_text':'kg'}];w['inspections']=[{'item_code':'WEIGHT','name':'TEST Weight','value_type':'decimal','numeric_value':str(n),'unit':'kg','judgement':'informational','min_inclusive':True,'max_inclusive':True,'sort_order':1,'is_public':True}];ok('passport-batches/'+b,w,'PUT','editor')
 s=sample('text'+str(n));s.update(is_public=True,status='ready');s['translations'][0].update(translation_status='approved',title='T10 section '+str(n),content={'text':'T10 version '+str(n)})
 p='passport-batches/'+b+'/sections';ok(p,{'expected_token':ok(p)['token'],'section':s},token='editor')
def roll(b,target,current=None,key=None,reason='Restore verified historical business content',token='admin'):
 if current is None:current=ok('passport-batches/'+b+'/publication')['current']['id']
 return req('passport-batches/'+b+'/publication/rollback',{'target_revision_id':target,'expected_current_revision_id':current,'idempotency_key':key or str(uuid.uuid4()),'rollback_reason':reason},token=token)
def chain(pid,label,count=3):
 b=batch(pid,'TEST-T10-'+label+'-'+runid);a=asset(b);versions=[]
 for i in range(1,count+1):
  if i>1:reopen(b)
  edit(b,i)
  if i==2:asset(b,index=2)
  if i==1:
   submit(b);assert decision(b,'reject',extra={'rejection_reason':'T10 test first review rejected'}).get('code')==200
  submit(b);assert decision(b).get('code')==200
  result=publish(b);assert result.get('code')==200,result;assert result['data']['record']['publish_status']=='published',result
  versions.append(result['data'])
 return b,versions,a

def main():
 init();pid,_=product('TEST-P-T10-'+runid);b,vs,a=chain(pid,'MAIN',2 if mode=='fresh' else 3);basep='passport-batches/'+b+'/publication';n=len(vs);source=vs[0]['revision'];current=vs[-1]['revision'];v1=source['id']
 check('Initial published chain',current['version_number']==n)
 hist=ok(basep+'/history');check('Version History all published',len(hist['versions'])==n);check('Review history includes rejected and approved',len(hist['reviews'])==n+1 and any(r['decision']=='rejected' for r in hist['reviews']))
 for role,code in [('editor',403),('reviewer',403),('viewer',403),(None,401)]:check('Rollback permission '+str(role),roll(b,v1,token=role).get('code')==code)
 for reason in ['', '   ','<script>x</script>','x'*1001]:check('Reason rejected '+repr(reason[:20]),roll(b,v1,reason=reason).get('code')==422)
 for role in ['editor','reviewer','viewer']:check('Reconcile permission '+role,req(basep+'/reconcile',{'reason':'test'},token=role).get('code')==403)
 check('Anonymous reconcile',req(basep+'/reconcile',{'reason':'test'},token=None).get('code')==401)
 check('Reconcile reason required',req(basep+'/reconcile',{}).get('code')==422)
 check('Unknown target rejected',roll(b,str(uuid.uuid4())).get('code') in [404,409])
 other,ov,_=chain(pid,'OTHER',1);check('Cross batch target rejected',roll(b,ov[0]['revision']['id']).get('code') in [404,409])
 detail=ok(basep+'/versions/'+v1);check('Detail payload manifest assets review',detail['payload'] and detail['manifest'] and detail['assets'] and detail['version']['revision']['source_review_record_id']);check('Integrity verified',detail['integrity']['state']=='verified')
 diff=ok(basep+'/compare?left='+v1+'&right='+current['id']);changes={x['group']:x for x in diff['differences'] if x['change']!='unchanged'}
 for key in ['packaging','inspection','custom_sections','assets','hash']:check('Compare '+key,key in changes)
 check('Packaging exact 25 to 20',changes['packaging']['before']['quantity']=='25' and changes['packaging']['after']['quantity']=='20')
 with db() as c:
  oldrows=c.execute('select * from passport_revisions where batch_id=? order by version_number',(b,)).fetchall()
  for name,sql,args in [('Revision immutable','UPDATE passport_revisions SET payload_hash=? WHERE id=?',('0'*64,v1)),('Asset immutable','UPDATE published_assets SET public_label=? WHERE passport_revision_id=?',('changed',v1)),('Audit append-only update','UPDATE passport_audit_events SET summary=? WHERE batch_id=?',('changed',b)),('Audit append-only delete','DELETE FROM passport_audit_events WHERE batch_id=?',(b,)),('Publish record no delete','DELETE FROM publish_records WHERE batch_id=?',(b,))]:
   try:c.execute(sql,args);blocked=False
   except sqlite3.IntegrityError:blocked=True
   check(name,blocked)
 oldfiles={v['revision']['snapshot_path']:(rt/'publish'/v['revision']['snapshot_path']).read_bytes() for v in vs}
 # Rollback must not need original source media.
 sourcefile=rt/'private-media'/a['key'];orig=sourcefile.read_bytes();sourcefile.unlink()
 try:r=roll(b,v1,current['id'])
 finally:sourcefile.write_bytes(orig)
 check('Rollback succeeds without private original',r.get('code')==200 and r['data']['record']['publish_status']=='published')
 v=r['data'];check('Rollback new version number',v['revision']['version_number']==n+1);check('Rollback source and preceding head',v['revision']['rollback_source_revision_id']==v1 and v['revision']['source_revision_id']==current['id']);check('New publish record release',v['record']['id']!=vs[0]['record']['id'] and v['revision']['release_identifier']!=source['release_identifier']);check('Rollback business hash same payload hash different',v['revision']['content_hash']==source['content_hash'] and v['revision']['payload_hash']!=source['payload_hash'])
 check('Current new revision',ok(basep)['current']['id']==v['revision']['id']);check('History old files unchanged',all((rt/'publish'/p).read_bytes()==raw for p,raw in oldfiles.items()))
 with db() as c:check('Old DB revisions unchanged',c.execute('select * from passport_revisions where batch_id=? and version_number<=? order by version_number',(b,n)).fetchall()==oldrows)
 vd=ok(basep+'/versions/'+v['revision']['id']);check('Logical assets belong to new revision',all(x['passport_revision_id']==v['revision']['id'] for x in vd['assets']));check('CAS shared with reference counts',vd['assets'][0]['published_path']==detail['assets'][0]['published_path'] and vd['assets'][0]['reference_count']>=2);check('Rollback metadata schema',vd['payload']['publication']['kind']=='rollback' and vd['payload']['publication']['source_version_number']==1)
 hst=ok(basep+'/history');check('Explicit rollback type',hst['versions'][0]['version_type']=='rollback');check('Rollback audit start success',all(any(a['event_type']==e for a in hst['audit']) for e in ['rollback_requested','rollback_succeeded']))
 if mode!='fresh':
  second=roll(b,vs[1]['revision']['id'])['data'];check('Second rollback creates V5',second['revision']['version_number']==5)
  reopen(b);submit(b);assert decision(b).get('code')==200;v6=publish(b)['data'];check('Normal publish after rollback V6',v6['revision']['version_number']==6 and v6['record']['publish_status']=='published')
 # Test corruption only in T10 isolated files, restore exact bytes after detection; historical DB never edited.
 for kind,file in [('json',rt/'publish'/source['snapshot_path']),('asset',rt/'publish'/detail['assets'][0]['published_path']),('manifest',rt/'releases/manifests'/(source['release_identifier']+'.json'))]:
  original=file.read_bytes();file.write_bytes(original+b' ' if kind!='asset' else b'bad png')
  try:
   check('Corrupt '+kind+' detected',ok(basep+'/versions/'+v1+'/integrity')['state']=='integrity_error')
   check('Corrupt '+kind+' rollback blocked',roll(b,v1).get('code')==409)
  finally:file.write_bytes(original)
 check('Corruption fixture restored',ok(basep+'/versions/'+v1+'/integrity')['state']=='verified')
 # Current older than confirmed DB is severe; only explicit evidence-based reconcile repairs head.
 code=scalar('select batch_code from batches where id=?',(b,));head=rt/'publish/published'/(code+'.json');latest=head.read_bytes();head.write_bytes(oldfiles[source['snapshot_path']])
 check('DB published current old classified',ok(basep+'/health')['classification']=='db_published_current_old');check('Inconsistent current blocks rollback',roll(b,v1).get('code')==409);check('Inconsistent current blocks publish',publish(b).get('code')==409)
 rr=ok(basep+'/reconcile',{'reason':'Restore verified DB current from known older file'});check('Reconcile current old restored',head.read_bytes()==latest and ok(basep+'/health')['state']=='consistent')
 # Unknown valid JSON remains blocked; no blind guess.
 unknown=json.loads(latest);unknown['publication']['issued_at']='2026-09-01T00:00:00.000Z';head.write_text(json.dumps(unknown))
 try:check('Unknown current blocks recovery',req(basep+'/reconcile',{'reason':'Must refuse unknown content'}).get('code')==409 and ok(basep+'/health')['state']=='reconciliation_required')
 finally:head.write_bytes(latest)
 check('Health restored after controlled corruption',ok(basep+'/health')['state']=='consistent')
 # Same request stable, changed intent rejected, concurrent expected-current CAS.
 cur=ok(basep)['current']['id'];key=str(uuid.uuid4());one=roll(b,v1,cur,key);check('Rollback idempotency replay',roll(b,v1,cur,key)['data']['record']['id']==one['data']['record']['id']);check('Idempotency reason mismatch',roll(b,v1,cur,key,reason='different intent').get('code')==409)
 cur=ok(basep)['current']['id']
 with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(lambda _:roll(b,v1,cur),range(2)))
 check('Concurrent rollback one success',sum(x.get('code')==200 and x['data']['record']['publish_status']=='published' for x in out)==1)
 cur=ok(basep)['current']['id'];q=pubreq(b)
 with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(lambda i:roll(b,v1,cur) if i==0 else publish(b,q),range(2)))
 check('Publish rollback race controlled',sum(x.get('code')==200 and x['data']['record']['publish_status']=='published' for x in out)<=1 and all(x.get('code') in [200,409] for x in out) and ok(basep+'/health')['state']=='consistent')
 hist=ok(basep+'/history');check('Recovery audits visible',all(any(a['event_type']==e for a in hist['audit']) for e in ['reconcile_started','reconcile_completed','reconcile_failed']))
 for cat in ['Product','Batch','Review','Publish','Rollback','SystemRecovery']:check('Audit filter '+cat,all(x['category']==cat for x in ok(basep+'/history?category='+cat)['audit']))
 # Fixtures for service faults and browser, each with V1-3.
 fixtures={'batch_id':b,'product_id':pid,'versions':vs,'faults':{}}
 if mode!='fresh':
  bb,bv,_=chain(pid,'BROWSER');fixtures['browser']={'batch_id':bb,'versions':bv}
  for stage in ['build','validation','manifest','asset','rename','finalize']:
   fb,fv,_=chain(pid,'FAULT'+stage,1);fixtures['faults'][stage]={'batch_id':fb,'target':fv[0]['revision']['id']}
 (rt/'test-artifacts/history-fixtures.json').write_text(json.dumps(fixtures,indent=2))
 # Archive preserves all historical relations and files.
 with db() as c:counts={t:c.execute('select count(*) from '+t+' where batch_id=?',(other,)).fetchone()[0] for t in ['passport_revisions','publish_records','review_records','passport_audit_events']}
 check('Published batch archive',req('passport-batches/'+other+'/review/archive',{}).get('code')==200)
 with db() as c:check('Archive retains history',all(c.execute('select count(*) from '+t+' where batch_id=?',(other,)).fetchone()[0]>=n for t,n in counts.items()))
 check('Archived version readable',ok('passport-batches/'+other+'/publication/history')['versions'][0]['revision']['id']==ov[0]['revision']['id'])
 check('DB integrity',scalar('pragma integrity_check')=='ok')
 with db() as c:check('Foreign keys',c.execute('pragma foreign_key_check').fetchall()==[])
if __name__=='__main__':
 try:main()
 finally:(rt/'test-artifacts/history-tests.json').write_text(json.dumps(checks,indent=2))
