import json,urllib.request,urllib.error,datetime,sqlite3,sys,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t6';cred=json.loads((rt/'credentials.json').read_text());checks=[];base='http://127.0.0.1:18097/api/v1/';phase=sys.argv[1] if len(sys.argv)>1 else 'initial';pbase='passport-products';bbase='passport-batches'
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
 r=req('login',{'username':user,'password':password,'code':'0','uuid':'T6'});check('JWT login '+user,r.get('code')==200);return r['token']
def sample(code):return {'product_code':code,'content':{'source_language':'en','package_quantity':'25','package_unit':'kg','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'T6 Test — TEST RECORD — NOT FOR COMMERCIAL USE','process_labels':{}}]}
def getp(pid,tok=None):return req(pbase+'/'+pid,token=tok or admin)['data']
def getb(bid):return req(bbase+'/'+bid,token=admin)['data']
def work(v=None):
 if v is None:return {'content':{'quality_status':'pending','production_date':None,'expiry_date':None,'internal_note':'TEST RECORD — NOT FOR COMMERCIAL USE'},'overrides':[],'inspections':[]}
 w=work();w['content']={k:v['batch'][k] for k in w['content']};w['expected_edit_version']=v['batch']['edit_version'];return w
def product(code,tok=None):
 tok=tok or admin;r=req(pbase,sample(code),tok);check('Create product '+code,r.get('code')==200);pid=r['data']['id'];v=getp(pid,tok)['revisions'][0];rid=v['id'];check('Seal product '+code,req(pbase+'/'+pid+'/revisions/'+rid+'/seal',{'expected_token':v['token']},tok).get('code')==200);check('Default product '+code,req(pbase+'/'+pid+'/default-revision',{'revision_id':rid,'expected_current_revision_id':None},tok,method='PUT').get('code')==200);return pid,rid
try:
 admin=login(cred['admin_username'],cred['admin_password'])
 if phase=='restart':
  f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());check('Product revisions persist',getp(f['product'])==f['product_detail'])
  for bid,v in f['batches'].items():check('Batch aggregate effective audit persist '+v['batch']['batch_code'],getb(bid)==v)
  exit()
 pid,r1=product('PF-T6-API-TEST')
 z=req(bbase,{'product_id':pid,'batch_code':'PF-T6-API-A',**work()},admin);check('Create batch HTTP',z.get('code')==200);bid=z['data']['id'];v=getb(bid);check('Saved fixed base R1',v['batch']['base_product_revision_id']==r1)
 check('Duplicate normalized code409',req(bbase,{'product_id':pid,'batch_code':' pf-t6-api-a ',**work()},admin).get('code')==409)
 for method,path,data in [('GET','',None),('POST','',{}),('GET','/'+bid,None),('PUT','/'+bid,{}),('POST','/'+bid+'/clone',{})]:check('Anonymous denied '+method+path,req(bbase+path,data,method=method).get('code')==401)
 for field,val in [('id',bid),('product_id',pid),('base_product_revision_id',r1),('batch_code','REBOUND'),('workflow_status','published'),('created_by',999),('reviewed_by',1),('current_passport_revision_id',r1)]:
  w=work(v);w[field]=val;check('Update mass assignment rejected '+field,req(bbase+'/'+bid,w,admin,method='PUT').get('code')==422)
 check('Create supplied base rejected',req(bbase,{'product_id':pid,'base_product_revision_id':r1,'batch_code':'PF-T6-BAD-BASE',**work()},admin).get('code')==422)
 check('Duplicate JSON keys rejected',req(bbase,token=admin,method='POST',raw='{"batch_code":"A","batch_code":"B"}').get('code')==422)
 check('No ordinary batch delete',req(bbase+'/'+bid,token=admin,method='DELETE').get('code') in [404,405])
 for key in ['product_code','batch_code','product_id','base_product_revision_id','workflow_status','created_by','product_name']:
  w=work(getb(bid));w['overrides']=[{'field_key':key,'operation':'clear'}];check('Forbidden override HTTP '+key,req(bbase+'/'+bid,w,admin,method='PUT').get('code')==422)
 for name,o in [('wrong numeric',{'field_key':'package_quantity','operation':'set','value_text':'NaN'}),('clear with value',{'field_key':'storage_conditions','operation':'clear','value_text':'x'}),('asset clear unavailable',{'field_key':'product_image_asset','operation':'clear'})]:
  w=work(getb(bid));w['overrides']=[o];check(name,req(bbase+'/'+bid,w,admin,method='PUT').get('code')==422)
 w=work(getb(bid));w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':'20'}];check('Aggregate override save',req(bbase+'/'+bid,w,admin,method='PUT').get('code')==200);check('Effective20',next(f for f in getb(bid)['effective'] if f['field_key']=='package_quantity')['value']=='20')
 # Use real official role/user APIs, no handcrafted JWT or direct Casbin bypass.
 for rolekey,menus,scope,uname in [('t6_none',[],'1','t6-no-access'),('t6_owner',[9100,9101,9102,9201,9202],'5','t6-owner'),('t6_view',[9100,9201],'1','t6-view')]:
  z=req('role',{'roleName':'T6 '+rolekey,'roleKey':rolekey,'roleSort':99,'status':'2','admin':False,'dataScope':scope,'menuIds':menus},admin);check('Create role '+rolekey,z.get('code')==200)
  db=sqlite3.connect(rt/'db/passport-admin-t6.db');role=db.execute('select role_id from sys_role where role_key=?',(rolekey,)).fetchone()[0];db.close()
  z=req('sys-user',{'username':uname,'password':cred['test_password'],'nickName':'T6 Test','phone':'00000000000','email':'t6@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'},admin);check('Create user '+uname,z.get('code')==200)
  tok=login(uname,cred['test_password'])
  if not menus:check('No Casbin grant denied',req(bbase,token=tok).get('code')==403)
  elif rolekey=='t6_view':
   check('Read-only role can list',req(bbase,token=tok).get('code')==200);check('Read-only role cannot write',req(bbase,{},tok).get('code')==403)
  else:
   own,_=product('PF-T6-OWNER-TEST',tok);x=req(bbase,{'product_id':own,'batch_code':'PF-T6-OWNER-BATCH',**work()},tok);check('Owner creates batch',x.get('code')==200);oid=x['data']['id'];check('Owner sees own',req(bbase+'/'+oid,token=tok).get('code')==200);check('Owner cannot see others',req(bbase+'/'+bid,token=tok).get('code')==404);check('Owner cannot edit others',req(bbase+'/'+bid,work(getb(bid)),tok,method='PUT').get('code')==404);check('Owner list filters',req(bbase,token=tok)['data']['count']==1)
 p=getp(pid);z=req(pbase+'/'+pid+'/revisions',{'source_revision_id':r1},admin);check('T5 clone R2 regression',z.get('code')==200);r2=z['data']['id'];r=getp(pid)['revisions'][0];tr=sample('unused')['translations'][0];check('T5 confirm R2',req(pbase+'/'+pid+'/revisions/'+r2+'/translations',{'expected_token':r['token'],'translation':tr},admin,method='PUT').get('code')==200);r=getp(pid)['revisions'][0];check('T5 seal R2',req(pbase+'/'+pid+'/revisions/'+r2+'/seal',{'expected_token':r['token']},admin).get('code')==200);check('T5 switch default',req(pbase+'/'+pid+'/default-revision',{'revision_id':r2,'expected_current_revision_id':r1},admin,method='PUT').get('code')==200)
 check('Old batch still R1 HTTP',getb(bid)['batch']['base_product_revision_id']==r1)
 z=req(bbase,{'product_id':pid,'batch_code':'PF-T6-API-B',**work()},admin);check('New batch uses R2',z.get('code')==200 and getb(z['data']['id'])['batch']['base_product_revision_id']==r2);b2=z['data']['id']
 z=req(bbase+'/'+bid+'/clone',{'batch_code':'PF-T6-API-CLONE','expected_edit_version':getb(bid)['batch']['edit_version']},admin);check('HTTP clone',z.get('code')==200);cid=z['data']['id'];check('Clone keeps R1',getb(cid)['batch']['base_product_revision_id']==r1)
 (rt/'test-artifacts/api-fixtures.json').write_text(json.dumps({'product':pid,'r1':r1,'r2':r2,'product_detail':getp(pid),'batches':{b:getb(b) for b in [bid,b2,cid]}},ensure_ascii=False,indent=2))
except Exception as e:
 checks.append({'name':'HTTP harness completion','status':'FAIL','error':str(e)});raise
finally:
 (rt/'test-artifacts'/f'api-{phase}.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(phase,len(checks),'PASS',sum(x['status']=='PASS' for x in checks),'FAIL',sum(x['status']=='FAIL' for x in checks))
