from pathlib import Path
import time,json,urllib.request,urllib.error,datetime,sqlite3,copy,concurrent.futures,sys,hashlib,uuid
R=Path(__file__).resolve().parents[2];mode=sys.argv[1] if len(sys.argv)>1 else 'initial';rt=R/('runtime/t12-fix/fresh' if mode=='fresh' else 'runtime/t12-fix');cred=json.loads((rt/'credentials.json').read_text());checks=[];base='http://127.0.0.1:'+('18112' if mode=='fresh' else '18111')+'/api/v1/';admin=None;runid=datetime.datetime.now().strftime('%H%M%S');tokens={};users={}

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
 c=sqlite3.connect(rt/'db'/('fresh-acceptance.db' if mode=='fresh' else 'passport-admin-t12-fix.db'));c.execute('pragma foreign_keys=on');return c
def scalar(sql,args=()):
 with db() as c:return c.execute(sql,args).fetchone()[0]
def login(username,password):
 x=req('login',{'username':username,'password':password,'code':'0','uuid':'T12'},token=None);assert x.get('code')==200,x;return x['token']
def product(code,token='editor'):
 p=ok('passport-products',{'product_code':code,'content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'T12 TEST ONLY','process_labels':{}}]},token=token)['id'];r=ok('passport-products/'+p,token=token)['revisions'][0];ok(f'passport-products/{p}/revisions/{r["id"]}/seal',{'expected_token':r['token']},token=token);v=ok('passport-products/'+p,token=token);ok(f'passport-products/{p}/default-revision',{'revision_id':r['id'],'expected_current_revision_id':None},'PUT',token);return p,r['id']
def batch(pid,code,token='editor',dates=True):
 return ok('passport-batches',{'product_id':pid,'batch_code':code,'record_type':'test','content':{'production_date':'2026-09-09' if dates else None,'expiry_date':'2027-09-09' if dates else None,'quality_status':'pending','internal_note':'T12 TEST'},'overrides':[],'inspections':[]},token=token)['id']
def submit(bid,token='editor'):
 return ok('passport-batches/'+bid+'/review/submit',{'expected_edit_version':ok('passport-batches/'+bid,token=token)['batch']['edit_version']},token=token)['id']
def decision(bid,action='approve',token='reviewer',extra=None):
 v=ok('passport-batches/'+bid+'/review',token=token)['current'];return req('passport-batches/'+bid+'/review/'+action,{'review_id':v['id'],'candidate_hash':v['candidate_hash'],**(extra or {})},token=token)
def work(bid):
 d=ok('passport-batches/'+bid)['batch'];return {'content':{k:d[k] for k in ['production_date','expiry_date','quality_status','internal_note']},'overrides':[],'inspections':[],'expected_edit_version':d['edit_version']}
def sample(key='module'):
 return {'section_key':key,'operation':'add','section_type':'text','sort_order':1,'is_visible':True,'is_public':False,'allow_hide':False,'status':'draft','translations':[{'language_code':'en','translation_status':'draft','title':'T12 TEST module','content':{'text':'T12 frozen custom text'}}]}
def snap():
 with db() as c:return {t:c.execute('select * from '+t+' order by id').fetchall() for t in ['batches','review_records','passport_audit_events']}
