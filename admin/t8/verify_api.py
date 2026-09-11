from pathlib import Path
import time,json,urllib.request,urllib.error,datetime,sqlite3,copy,concurrent.futures,sys,hashlib,uuid
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t8';cred=json.loads((rt/'credentials.json').read_text());checks=[];mode=sys.argv[1] if len(sys.argv)>1 else 'initial';base='http://127.0.0.1:'+('18102' if mode=='fresh' else '18101')+'/api/v1/';admin=None;runid=datetime.datetime.now().strftime('%H%M%S');tokens={};users={}
def check(name,value):
 checks.append({'name':name,'status':'PASS' if value else 'FAIL'});print(checks[-1],flush=True)
 if not value:raise AssertionError(name)
def req(path,data=None,method=None,token='admin'):
 time.sleep(.035);headers={'Content-Type':'application/json'};tok=admin if token=='admin' else tokens.get(token,token)
 if tok:headers['Authorization']='Bearer '+tok
 try:
  with urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method),timeout=25) as f:return json.load(f)
 except urllib.error.HTTPError as e:
  try:return json.load(e)
  except:return {'code':e.code}
def ok(path,data=None,method=None,token='admin'):
 x=req(path,data,method,token);assert x.get('code')==200,(path,x);return x.get('data')
def db():
 c=sqlite3.connect(rt/'db'/('fresh-acceptance.db' if mode=='fresh' else 'passport-admin-t8.db'));c.execute('pragma foreign_keys=on');return c
def scalar(sql,args=()):
 with db() as c:return c.execute(sql,args).fetchone()[0]
def login(username,password):
 x=req('login',{'username':username,'password':password,'code':'0','uuid':'T8'},token=None);assert x.get('code')==200,x;return x['token']
def product(code,token='editor'):
 p=ok('passport-products',{'product_code':code,'content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'T8 TEST ONLY','process_labels':{}}]},token=token)['id'];r=ok('passport-products/'+p,token=token)['revisions'][0];ok(f'passport-products/{p}/revisions/{r["id"]}/seal',{'expected_token':r['token']},token=token);v=ok('passport-products/'+p,token=token);ok(f'passport-products/{p}/default-revision',{'revision_id':r['id'],'expected_current_revision_id':None},'PUT',token);return p,r['id']
def batch(pid,code,token='editor',dates=True):
 return ok('passport-batches',{'product_id':pid,'batch_code':code,'record_type':'test','content':{'production_date':'2026-09-09' if dates else None,'expiry_date':'2027-09-09' if dates else None,'quality_status':'pending','internal_note':'T8 TEST'},'overrides':[],'inspections':[]},token=token)['id']
def submit(bid,token='editor'):
 return ok('passport-batches/'+bid+'/review/submit',{'expected_edit_version':ok('passport-batches/'+bid,token=token)['batch']['edit_version']},token=token)['id']
def decision(bid,action='approve',token='reviewer',extra=None):
 v=ok('passport-batches/'+bid+'/review',token=token)['current'];return req('passport-batches/'+bid+'/review/'+action,{'review_id':v['id'],'candidate_hash':v['candidate_hash'],**(extra or {})},token=token)
def work(bid):
 d=ok('passport-batches/'+bid)['batch'];return {'content':{k:d[k] for k in ['production_date','expiry_date','quality_status','internal_note']},'overrides':[],'inspections':[],'expected_edit_version':d['edit_version']}
def sample(key='module'):
 return {'section_key':key,'operation':'add','section_type':'text','sort_order':1,'is_visible':True,'is_public':False,'allow_hide':False,'status':'draft','translations':[{'language_code':'en','translation_status':'draft','title':'T8 TEST module','content':{'text':'T8 frozen custom text'}}]}
def snap():
 with db() as c:return {t:c.execute('select * from '+t+' order by id').fetchall() for t in ['batches','review_records','passport_audit_events']}
def main():
 global admin
 admin=login(cred['admin_username'],cred['admin_password']);check('JWT admin login',True)
 if mode=='restart':
  f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text())
  for bid,v in f['snapshots'].items():check('Restart exact review '+bid,ok('passport-batches/'+bid+'/review')==v)
  return
 for kind in ['editor','reviewer','viewer','editor_reviewer']:
  key='passport_'+kind;role=scalar('select role_id from sys_role where role_key=?',(key,));username='t8-'+kind+'-'+runid
  ok('sys-user',{'username':username,'password':cred['test_password'],'nickName':'T8 '+kind,'phone':'00000000000','email':'t8@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
  tokens[kind]=login(username,cred['test_password']);users[kind]={'username':username,'id':scalar('select user_id from sys_user where username=?',(username,))};check(kind+' user login and role exists',True)
 (rt/'test-artifacts'/('fresh-users.json' if mode=='fresh' else 'users.json')).write_text(json.dumps(users))
 pid,rid=product('PF-T8-'+runid);bid=batch(pid,'BT-T8-'+runid);path='passport-batches/'+bid;rp=path+'/review'
 check('Editor creates sealed Product and Batch',True)
 # All writes and all new routes audited through real HTTP against Casbin.
 with db() as c:apis=c.execute("select path,action from sys_api where path like '/api/v1/passport-%'").fetchall()
 for raw,method in apis:
  url=raw.removeprefix('/api/v1/').replace(':id',bid if 'batches' in raw else pid).replace(':revisionId',rid).replace(':sectionId',str(uuid.uuid4()))
  if method!='GET':
   check('Viewer denied '+method+' '+raw,req(url,{},method,'viewer').get('code')==403)
   if '/review/' not in raw:check('Reviewer denied edit '+method+' '+raw,req(url,{},method,'reviewer').get('code')==403)
  if '/review' in raw:check('Anonymous denied '+method+' '+raw,req(url,None if method=='GET' else {},method,None).get('code')==401)
 for a in ['approve','reject']:check('Editor denied '+a,req(rp+'/'+a,{},token='editor').get('code')==403)
 check('Viewer reads batch',req(path,token='viewer').get('code')==200)
 check('Reviewer queue accessible',req('passport-reviews',token='reviewer').get('code')==200)
 check('Editor no queue',req('passport-reviews',token='editor').get('code')==403)
 bad=batch(pid,'BT-T8-MISSING-'+runid,dates=False);res=req('passport-batches/'+bad+'/review/submit',{'expected_edit_version':1},token='editor');check('Structured missing dates prevents Submit',res.get('code')==422 and len(res.get('data',{}).get('errors',[]))==2)
 sec=path+'/sections';sid=ok(sec,{'expected_token':ok(sec)['token'],'section':sample()},token='editor')['id']
 check('Optional languages and private Draft section ready',ok(rp+'/readiness',token='editor')['ready'])
 # Audit failures must roll back entire transition.
 def fault(action,token):
  before=snap()
  with db() as c:c.execute("CREATE TRIGGER t8_fault BEFORE INSERT ON passport_audit_events BEGIN SELECT RAISE(ABORT,'T8 fault'); END")
  try:
   x=req(rp+'/submit',{'expected_edit_version':ok(path)['batch']['edit_version']},token=token) if action=='submit' else decision(bid,action,token,{'rejection_reason':'T8 reject'} if action=='reject' else {})
  finally:
   with db() as c:c.execute('DROP TRIGGER t8_fault')
  check(action+' audit failure fails',x.get('code')!=200);check(action+' exact transaction rollback',before==snap())
 fault('submit','editor');rv=submit(bid);frozen=ok(rp)['current'];check('Draft to Pending frozen input',ok(rp)['state']=='pending_review' and frozen['candidate']['batch']['batch_code']=='BT-T8-'+runid)
 check('Candidate SHA256 stored',scalar('select candidate_hash from review_records where id=?',(rv,))==hashlib.sha256(scalar('select candidate_input from review_records where id=?',(rv,)).encode()).hexdigest())
 for method,url,data in [('PUT',path,work(bid)),('POST',sec,{'expected_token':ok(sec)['token'],'section':sample('second')}),('PUT',sec+'/'+sid,{'expected_token':ok(sec)['token'],'section':sample()}),('DELETE',sec+'/'+sid,{'expected_token':ok(sec)['token']}),('PUT',sec+'/reorder',{'expected_token':ok(sec)['token'],'keys':['module']}),('PUT',sec+'/'+sid+'/translations',{'expected_token':ok(sec)['token'],'translation':sample()['translations'][0]})]:
  check('Pending rejects '+method+url,req(url,data,method,'editor').get('code')==409)
 check('Repeated submit conflict',req(rp+'/submit',{'expected_edit_version':ok(path)['batch']['edit_version']},token='editor').get('code')==409)
 check('Reject reason required',decision(bid,'reject').get('code')==422)
 for badcomment in ['<script>alert(1)</script>','a'*2001]:check('Unsafe comment rejected',decision(bid,extra={'comment':badcomment}).get('code')==422)
 fault('reject','reviewer');fault('approve','reviewer')
 # Product default independently changes without changing frozen candidate.
 r2=ok(f'passport-products/{pid}/revisions',{'source_revision_id':rid},token='editor')['id'];rev=next(r for r in ok('passport-products/'+pid)['revisions'] if r['id']==r2)
 tr=copy.deepcopy(rev['translations'][0]);tr={k:v for k,v in tr.items() if k in ['language_code','translation_status','product_name','process_labels','application','storage_condition','safety_notice','description','manufacturer','origin','appearance','specification']};tr['translation_status']='approved'
 # Clone resets translations to Draft; copy DTO from original API inputs.
 tr={'language_code':'en','translation_status':'approved','product_name':'T8 NEW DEFAULT','process_labels':{}}
 ok(f'passport-products/{pid}/revisions/{r2}/translations',{'expected_token':rev['token'],'translation':tr},'PUT','editor');rev=next(r for r in ok('passport-products/'+pid)['revisions'] if r['id']==r2)
 ok(f'passport-products/{pid}/revisions/{r2}/seal',{'expected_token':rev['token']},token='editor');ok(f'passport-products/{pid}/default-revision',{'revision_id':r2,'expected_current_revision_id':rid},'PUT','editor');check('Default change leaves frozen candidate byte-identical',ok(rp)['current']==frozen)
 check('Admin cannot disable product under review',req('passport-products/'+pid,{'lifecycle_status':'disabled'},'PUT').get('code')==409)
 check('Reviewer rejects',decision(bid,'reject',extra={'rejection_reason':'T8 add corrected note','comment':'T8 review comment'}).get('code')==200);check('Reject returns Draft and keeps reason',ok(rp)['state']=='draft' and ok(rp)['history'][0]['rejection_reason']=='T8 add corrected note')
 w=work(bid);w['content']['internal_note']='T8 corrected';ok(path,w,'PUT','editor');rv2=submit(bid);check('Resubmit distinct immutable history',rv2!=rv and len(ok(rp)['history'])==2 and ok(rp)['history'][1]['decision']=='rejected')
 check('Reviewer approves',decision(bid).get('code')==200);check('Approved is locked Ready for Publish',ok(rp)['state']=='ready_for_publish' and ok(path)['batch']['workflow_status']=='pending_review' and ok(path)['batch']['review_state']=='ready_for_publish')
 check('Approved rejects edits',req(path,work(bid),'PUT','editor').get('code')==409);check('Repeated approve conflict',decision(bid).get('code')==409)
 check('No public records',all(scalar('select count(*) from '+t)==0 for t in ['passport_revisions','publish_records','published_assets']))
 for sql,args in [('update review_records set comment=? where id=?',('tampered',rv2)),('delete from review_records where id=?',(rv,)),('update batches set submitted_content_hash=? where id=?',('0'*64,bid)),('update custom_section_translations set title=? where custom_section_id=?',('changed',sid)),('update batches set internal_note=? where id=?',('changed',bid))]:
  with db() as c:
   try:c.execute(sql,args);denied=False
   except sqlite3.IntegrityError:denied=True
  check('DB freeze '+sql,denied)
 check('Return requires reason',req(rp+'/return',{'review_id':rv2,'reason':''},token='editor').get('code')==422)
 ok(rp+'/return',{'review_id':rv2,'reason':'T8 explicit new edit'},token='editor');check('Return clears candidate pointer preserves approval history',ok(rp)['state']=='draft' and ok(rp)['current'] is None and len(ok(rp)['history'])==2)
 submit(bid);check('New attempt after return',len(ok(rp)['history'])==3)
 for kind in ['approve','mixed','submit']:
  b=batch(pid,'BT-T8-RACE-'+kind+'-'+runid)
  if kind!='submit':submit(b)
  record=ok('passport-batches/'+b+'/review')['current']
  def race(i):
   if kind=='submit':return req('passport-batches/'+b+'/review/submit',{'expected_edit_version':1},token='editor')
   return req('passport-batches/'+b+'/review/'+('reject' if kind=='mixed' and i%2 else 'approve'),{'review_id':record['id'],'candidate_hash':record['candidate_hash'],**({'rejection_reason':'T8 race reject'} if kind=='mixed' and i%2 else {})},token='reviewer')
  with concurrent.futures.ThreadPoolExecutor(5) as pool:out=list(pool.map(race,range(5)))
  check('Five concurrent '+kind+' exactly one success',sum(x.get('code')==200 for x in out)==1 and sum(x.get('code')==409 for x in out)==4)
 bself=batch(pid,'BT-T8-SELF-'+runid,token='editor_reviewer');submit(bself,'editor_reviewer');check('Composite cannot self approve',decision(bself,token='editor_reviewer').get('code')==403);check('Composite cannot self reject',decision(bself,'reject','editor_reviewer',{'rejection_reason':'self'}).get('code')==403)
 badmin=batch(pid,'BT-T8-ADMIN-SELF-'+runid,token='admin');submit(badmin,'admin');check('Admin self review also forbidden',decision(badmin,token='admin').get('code')==403)
 # Real JWT remains the same while DB permissions are revoked.
 uid=users['editor']['id']
 with db() as c:c.execute("update sys_user set status='1' where user_id=?",(uid,))
 check('Disabled account stale JWT denied',req(path,token='editor').get('code')==401)
 with db() as c:c.execute("update sys_user set status='2',role_id=(select role_id from sys_role where role_key='passport_viewer') where user_id=?",(uid,))
 check('Role downgrade stale JWT write denied',req(rp+'/submit',{},token='editor').get('code')==403)
 with db() as c:c.execute("update sys_user set role_id=(select role_id from sys_role where role_key='passport_editor') where user_id=?",(uid,))
 check('Integrity',scalar('pragma integrity_check')=='ok')
 with db() as c:check('No foreign key errors',c.execute('pragma foreign_key_check').fetchall()==[])
 fixtures={'product_id':pid,'batch_id':bid,'self_batch_id':bself,'snapshots':{b:ok('passport-batches/'+b+'/review') for b in [bid,bself,badmin]}}
 (rt/'test-artifacts'/('fresh-api-fixtures.json' if mode=='fresh' else 'api-fixtures.json')).write_text(json.dumps(fixtures,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 finally:(rt/'test-artifacts'/('api-'+mode+'.json')).write_text(json.dumps(checks,ensure_ascii=False,indent=2))
