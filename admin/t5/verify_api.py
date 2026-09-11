import json,urllib.request,urllib.error,datetime,sqlite3,sys,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t5';cred=json.loads((rt/'credentials.json').read_text());checks=[];base='http://127.0.0.1:18095/api/v1/';pbase='passport-products';phase=sys.argv[1] if len(sys.argv)>1 else 'initial'
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL','time':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 if not v:raise AssertionError(n)
def req(path,data=None,token=None,method=None,raw=None):
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 body=raw.encode() if raw is not None else json.dumps(data).encode() if data is not None else None
 r=urllib.request.Request(base+path,data=body,headers=headers,method=method)
 try:
  with urllib.request.urlopen(r,timeout=15) as f:return json.load(f)
 except urllib.error.HTTPError as e:
  try:return json.loads(e.read())
  except Exception:return {'code':e.code}
def login(user,password):
 r=req('login',{'username':user,'password':password,'code':'0','uuid':'T5'});check('JWT login '+user,r.get('code')==200);return r['token']
def sample(code):return {'product_code':code,'content':{'source_language':'en','process_steps':[{'step_key':'washing'}]},'translations':[{'language_code':'en','translation_status':'draft','product_name':'T5 Test — TEST RECORD — NOT FOR COMMERCIAL USE','process_labels':{'washing':'T5 washing'}}]}
def get(pid):return req(pbase+'/'+pid,token=admin)['data']
try:
 admin=login(cred['admin_username'],cred['admin_password'])
 if phase=='restart':
  f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());v=get(f['product']);check('Product persists after backend restart',v['product']['product_code']=='PF-T5-API-TEST');check('Revision and six translations persist',len(v['revisions'])==2 and all(len(r['translations'])==6 for r in v['revisions']));check('Default persists',v['product']['current_revision_id']==f['r2']);check('All business detail bytes unchanged after restart',v==f['detail']);exit()
 r=req(pbase,sample('pf-t5-api-test'),admin);check('HTTP product initial aggregate create',r.get('code')==200);pid=r['data']['id'];v=get(pid);r1=v['revisions'][0]['id'];check('Product identity separated from R1',v['product']['id']!=r1 and v['revisions'][0]['revision_number']==1)
 r=req(pbase,sample(' PF-T5-API-TEST '),admin);check('Duplicate code readable error',r.get('code')==409 and '编码已存在' in r.get('msg',''))
 for field,value in [('id','fake'),('created_by',999),('current_revision_id',r1)]:
  body=sample('PF-T5-INJECTION-'+field.upper());body[field]=value;check('Reject mass assignment '+field,req(pbase,body,admin).get('code')==422)
 check('Reject duplicate JSON keys',req(pbase,token=admin,method='POST',raw='{"product_code":"PF-T5-A","product_code":"PF-T5-B"}').get('code')==422)
 check('Immutable code update rejected',req(pbase+'/'+pid,{'product_code':'PF-T5-CHANGED'},admin,method='PUT').get('code')==422)
 paths=[('GET','',None),('POST','',{}),('GET','/'+pid,None),('PUT','/'+pid,{}),('POST','/'+pid+'/archive',{}),('GET','/'+pid+'/revisions',None),('POST','/'+pid+'/revisions',{}),('GET','/'+pid+'/revisions/'+r1,None),('PUT','/'+pid+'/revisions/'+r1,{}),('PUT','/'+pid+'/revisions/'+r1+'/translations',{}),('POST','/'+pid+'/revisions/'+r1+'/seal',{}),('PUT','/'+pid+'/default-revision',{})]
 for method,path,data in paths:check('Anonymous denied '+method+' '+path,req(pbase+path,data,method=method).get('code')==401)
 check('No ordinary hard delete route',req(pbase+'/'+pid,token=admin,method='DELETE').get('code') in [404,405])
 # Restricted own-data role proves module adapter to upstream data scope.
 for rolekey,menus,scope,uname in [('t5_none',[],'1','t5-no-access'),('t5_owner',[9100,9101,9102],'5','t5-owner')]:
  z=req('role',{'roleName':'T5 '+rolekey,'roleKey':rolekey,'roleSort':99,'status':'2','admin':False,'dataScope':scope,'menuIds':menus},admin);check('Create permission test role '+rolekey,z.get('code')==200)
  db=sqlite3.connect(rt/'db/passport-admin-t5.db');role=db.execute('select role_id from sys_role where role_key=?',(rolekey,)).fetchone()[0];db.close()
  z=req('sys-user',{'username':uname,'password':cred['test_password'],'nickName':'T5 Test','phone':'00000000000','email':'t5@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'},admin);check('Create permission test user '+uname,z.get('code')==200)
  tok=login(uname,cred['test_password'])
  if not menus:check('Authenticated without Casbin grant denied',req(pbase,token=tok).get('code')==403)
  else:
   x=req(pbase,sample('PF-T5-OWNER-TEST'),tok);check('Granted non-admin creates own product',x.get('code')==200);own=x['data']['id'];check('Own data scope permits own detail',req(pbase+'/'+own,token=tok).get('code')==200);check('Own data scope hides others detail',req(pbase+'/'+pid,token=tok).get('code')==404);check('Own data scope blocks others writes',req(pbase+'/'+pid,{'lifecycle_status':'disabled'},tok,method='PUT').get('code')==404);z=req(pbase,token=tok);check('Own data scope list filtered',z.get('code')==200 and z['data']['count']==1)
 for lang in ['en','zh-CN','es','ar','fr','de']:
  r=get(pid)['revisions'][0];z=req(pbase+'/'+pid+'/revisions/'+r1+'/translations',{'expected_token':r['token'],'translation':{'language_code':lang,'translation_status':'approved','product_name':'T5 '+lang+' TEST RECORD — NOT FOR COMMERCIAL USE','process_labels':{}}},admin,method='PUT');check('Translation HTTP '+lang,z.get('code')==200)
 r=get(pid)['revisions'][0];check('Seal via HTTP',req(pbase+'/'+pid+'/revisions/'+r1+'/seal',{'expected_token':r['token']},admin).get('code')==200)
 check('Set R1 default via HTTP',req(pbase+'/'+pid+'/default-revision',{'revision_id':r1,'expected_current_revision_id':None},admin,method='PUT').get('code')==200)
 r=get(pid)['revisions'][0];check('Frozen translation HTTP rejection',req(pbase+'/'+pid+'/revisions/'+r1+'/translations',{'expected_token':r['token'],'translation':{'language_code':'en','product_name':'bad'}},admin,method='PUT').get('code')==409)
 check('Frozen revision HTTP rejection',req(pbase+'/'+pid+'/revisions/'+r1,{'expected_token':r['token'],'content':{'source_language':'en','process_steps':[]}},admin,method='PUT').get('code')==409)
 z=req(pbase+'/'+pid+'/revisions',{'source_revision_id':r1},admin);check('Clone HTTP',z.get('code')==200);r2=z['data']['id'];r=get(pid)['revisions'][0];check('Clone defaults and six copied translations',r['revision_status']=='draft' and len(r['translations'])==6 and r['sealed_at'] is None)
 z=req(pbase+'/'+pid+'/revisions/'+r2+'/translations',{'expected_token':r['token'],'translation':{'language_code':'en','product_name':'T5 R2 TEST RECORD — NOT FOR COMMERCIAL USE','translation_status':'approved','process_labels':{}}},admin,method='PUT');check('Confirm R2 source language',z.get('code')==200)
 r=get(pid)['revisions'][0];check('Seal R2 HTTP',req(pbase+'/'+pid+'/revisions/'+r2+'/seal',{'expected_token':r['token']},admin).get('code')==200);check('Switch R2 default HTTP',req(pbase+'/'+pid+'/default-revision',{'revision_id':r2,'expected_current_revision_id':r1},admin,method='PUT').get('code')==200)
 detail=get(pid);(rt/'test-artifacts/api-fixtures.json').write_text(json.dumps({'product':pid,'r1':r1,'r2':r2,'detail':detail},ensure_ascii=False));check('R1 and R2 retained over HTTP',len(detail['revisions'])==2)
except Exception as e:
 checks.append({'name':'HTTP harness completion','status':'FAIL','error':str(e)});raise
finally:
 (rt/'test-artifacts'/f'api-{phase}.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(phase,len(checks),'PASS',sum(x['status']=='PASS' for x in checks),'FAIL',sum(x['status']=='FAIL' for x in checks))
