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
base='http://127.0.0.1:18098/api/v1/'
try:
 admin=login(cred['admin_username'],cred['admin_password'])
 check('Fresh Products opens empty',req(pbase,token=admin)['data']['count']==0)
 check('Fresh Batches opens empty',req(bbase,token=admin)['data']['count']==0)
 pid,rid=product('PF-T6-FRESH-TEST')
 w=work();w['content']['production_date']='2026-09-08';w['content']['expiry_date']='2027-09-08';w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':'20'}]
 w['inspections']=[{'item_code':'BULK_DENSITY','name':'Bulk Density TEST','value_type':'decimal','numeric_value':'0.4','unit':'g/ml','min_limit':'0.3','max_limit':'0.5','min_inclusive':True,'max_inclusive':True,'judgement':'pass','sort_order':0,'is_public':False}]
 z=req(bbase,{'product_id':pid,'batch_code':'PF-T6-FRESH-BATCH',**w},admin);check('Fresh create aggregate',z.get('code')==200);bid=z['data']['id'];v=getb(bid)
 check('Fresh persisted base',v['batch']['base_product_revision_id']==rid)
 check('Fresh persisted real dates',v['batch']['production_date']=='2026-09-08' and v['batch']['expiry_date']=='2027-09-08')
 check('Fresh override20',next(x for x in v['effective'] if x['field_key']=='package_quantity')['value']=='20')
 check('Fresh dynamic inspection',v['inspections'][0]['numeric_value']=='0.4')
 check('Fresh transactional audit',len(v['audit'])==3)
 (rt/'test-artifacts/fresh-fixtures.json').write_text(json.dumps({'product':pid,'batch':bid,'detail':v},ensure_ascii=False,indent=2))
except Exception as e:
 checks.append({'name':'Fresh HTTP completion','status':'FAIL','error':str(e)});raise
finally:
 (rt/'test-artifacts/fresh-http-tests.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'checks',sum(x['status']=='FAIL' for x in checks),'FAIL')
