from pathlib import Path
import time
import json,urllib.request,urllib.error,datetime,sqlite3,copy,concurrent.futures,sys
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t7';cred=json.loads((rt/'credentials.json').read_text());checks=[];base='http://127.0.0.1:18099/api/v1/';mode=sys.argv[1] if len(sys.argv)>1 else 'initial';admin=None
runid=datetime.datetime.now().strftime('%H%M%S')

def check(name,value):
 checks.append({'name':name,'status':'PASS' if value else 'FAIL'})
 if not value:raise AssertionError(name)
def req(path,data=None,method=None,token='admin',raw=None):
 time.sleep(0.025)
 headers={'Content-Type':'application/json'};tok=admin if token=='admin' else token
 if tok:headers['Authorization']='Bearer '+tok
 body=raw.encode() if raw else json.dumps(data).encode() if data is not None else None
 try:
  with urllib.request.urlopen(urllib.request.Request(base+path,data=body,headers=headers,method=method),timeout=20) as f:return json.load(f)
 except urllib.error.HTTPError as e:
  try:return json.load(e)
  except:return {'code':e.code}
def ok(path,data=None,method=None):
 x=req(path,data,method);assert x.get('code')==200,(path,x);return x.get('data')
def db():
 c=sqlite3.connect(rt/'db/passport-admin-t7.db');c.execute('pragma foreign_keys=on');return c
def scalar(sql,args=()):
 with db() as c:return c.execute(sql,args).fetchone()[0]
def get(path):return ok(path)
def sample(key,kind='text',hide=False):
 content={'text':'TEST ONLY — module content'} if kind=='text' else {'items':[{'key':'source','label':'Source','value':'TEST'}]} if kind=='key_value' else {'columns':[{'key':'result','label':'Result'}],'rows':[{'cells':['TEST']}]} if kind=='table' else {'caption':'TEST gallery caption'}
 return {'section_key':key,'operation':'add','section_type':kind,'sort_order':10,'is_visible':True,'is_public':False,'allow_hide':hide,'status':'draft','translations':[{'language_code':'en','translation_status':'draft','title':'TEST '+key,'content':content}]}
def put(path,d,sid='',token=None):return req(path+('/'+sid if sid else ''),{'expected_token':token or get(path)['token'],'section':d},'PUT' if sid else 'POST')
def mustput(path,d,sid=''):
 x=put(path,d,sid);assert x.get('code')==200,x;return x['data']['id']
def product(code):
 p=ok('passport-products',{'product_code':code,'content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'T7 TEST RECORD — NOT FOR COMMERCIAL USE','process_labels':{}}]})['id'];r=get('passport-products/'+p)['revisions'][0]['id'];return p,r
try:
 x=req('login',{'username':cred['admin_username'],'password':cred['admin_password'],'code':'0','uuid':'T7'},token=None);assert x.get('code')==200,x;admin=x['token'];check('JWT login',True)
 if mode=='restart':
  f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text())
  for path,value in f['snapshots'].items():check('Restart persists '+path,get(path)==value)
  sys.exit()
 pid,rid=product('PF-T7-API-TEST-'+runid);pp=f'passport-products/{pid}';path=f'{pp}/revisions/{rid}/sections';ids={}
 for kind in ['text','key_value','table','asset_gallery']:
  d=sample('test_'+kind,kind,kind=='text');ids[kind]=mustput(path,d);check('Create controlled '+kind,True)
 set=get(path);check('Four sections stored',len(set['sections'])==4)
 for i,kind in enumerate(ids):check('Get section '+kind,get(path+'/'+ids[kind])['section_type']==kind)
 for key in ['product','product_code','publication','sys_secret','__proto__','ABC','a'*65,'bad key']:
  check('Reserved or invalid key '+key,put(path,sample(key)).get('code')==422)
 bad=[]
 d=sample('bad');d['section_type']='unknown_super_section';bad.append(('unknown type',d))
 for field,value in [('extra',{}),('text',{}),('text',None)]:
  d=sample('bad');d['translations'][0]['content'][field]=value;bad.append(('content '+field+repr(value),d))
 for payload in ['<script>alert(1)</script>','javascript:alert(1)','<img src=x onerror=alert(1)>','<iframe src=x></iframe>']:
  d=sample('bad');d['translations'][0]['content']['text']=payload;bad.append(('XSS '+payload,d))
 d=sample('bad');d['translations'][0]['title']='a'*201;bad.append(('title limit',d))
 d=sample('bad');d['translations'][0]['content']['text']='a'*10001;bad.append(('text limit',d))
 d=sample('bad','key_value');d['translations'][0]['content']['items']*=101;bad.append(('items limit',d))
 d=sample('bad','key_value');del d['translations'][0]['content']['items'][0]['key'];bad.append(('missing item key',d))
 d=sample('bad','table');d['translations'][0]['content']['rows'][0]['cells']=['a','b'];bad.append(('table width',d))
 d=sample('bad','table');d['translations'][0]['content']['columns']*=21;bad.append(('table columns',d))
 d=sample('bad','table');d['translations'][0]['content']['rows']*=201;bad.append(('table rows',d))
 d=sample('bad');d['translations'][0]['content']['text']='a'*262145;bad.append(('JSON size',d))
 d=sample('bad','asset_gallery');d['translations'][0]['content']['asset_id']=rid;bad.append(('gallery asset injection',d))
 for name,d in bad:check('Reject '+name,put(path,d).get('code')==422)
 check('Duplicate raw content keys rejected',req(path,method='POST',raw=json.dumps({'expected_token':get(path)['token'],'section':sample('bad')}).replace('"text":', '"text":"duplicate","text":')).get('code')==422)
 for field,value in [('id',rid),('created_by',999),('product_revision_id',rid),('batch_id',rid),('sealed_at','now')]:
  d=sample('bad');d[field]=value;check('Mass assignment '+field,put(path,d).get('code')==422)
 token=get(path)['token'];d=sample('test_text',hide=True);d['translations'][0]['content']['text']='Updated TEST';check('Draft update',put(path,d,ids['text'],token).get('code')==200);check('Stale token rejected',put(path,d,ids['text'],token).get('code')==409)
 for lang in ['zh-CN','es','ar','fr','de']:
  tr={'language_code':lang,'translation_status':'draft','title':'TEST '+lang,'content':{'text':'اختبار' if lang=='ar' else 'TEST '+lang}}
  check('Translation '+lang,req(path+'/'+ids['text']+'/translations',{'expected_token':get(path)['token'],'translation':tr},'PUT').get('code')==200)
 check('Six translations coexist',scalar('select count(*) from custom_section_translations where custom_section_id=?',(ids['text'],))==6)
 tr={'language_code':'en','translation_status':'draft','title':'TEST replacement','content':{'text':'TEST edited'}}
 check('Translation upsert no duplicate',req(path+'/'+ids['text']+'/translations',{'expected_token':get(path)['token'],'translation':tr},'PUT').get('code')==200 and scalar('select count(*) from custom_section_translations where custom_section_id=?',(ids['text'],))==6)
 tr={'language_code':'fr','translation_status':'draft','title':'TEST','content':{'items':[{'key':'different','label':'x','value':'x'}]}}
 check('Translation structural alignment',req(path+'/'+ids['key_value']+'/translations',{'expected_token':get(path)['token'],'translation':tr},'PUT').get('code')==422)
 check('Fallback to owner source',next(x for x in get(path+'?language=fr')['effective'] if x['section_key']=='test_table')['language']=='en')
 keys=[x['section_key'] for x in get(path)['sections']][::-1];check('Reorder',req(path+'/reorder',{'expected_token':get(path)['token'],'keys':keys},'PUT').get('code')==200);check('Stable order', [x['section_key'] for x in get(path)['effective']]==keys)
 # Fault injection is confined to disposable T7 DB, and audit/translation rollback compares exact aggregates.
 for table in ['custom_section_translations','passport_audit_events']:
  before=get(path);n=scalar('select count(*) from passport_audit_events')
  with db() as c:c.execute(f"CREATE TRIGGER t7_fail BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT,'t7 injected'); END")
  try:check('Injected '+table+' failure',put(path,sample('rollback')).get('code')!=200)
  finally:
   with db() as c:c.execute('DROP TRIGGER t7_fail')
  check('Atomic rollback '+table,get(path)==before and scalar('select count(*) from passport_audit_events')==n)
 # SQL UNIQUE layer independently of API upsert.
 with db() as c:
  row=c.execute('select * from custom_section_translations where custom_section_id=? limit 1',(ids['text'],)).fetchone();cols=[x[1] for x in c.execute('pragma table_info(custom_section_translations)')];v=list(row);import uuid;v[0]=str(uuid.uuid4())
  try:c.execute('insert into custom_section_translations values('+','.join('?' for _ in v)+')',v);unique=False
  except sqlite3.IntegrityError:unique=True
  check('DB translation UNIQUE',unique)
 # Two simultaneous clients, each refreshes once on optimistic conflict.
 def concurrent_create(key):
  for _ in range(3):
   x=put(path,sample(key))
   if x.get('code')!=409:return x
  return x
 with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(concurrent_create,['parallel_a','parallel_b']))
 check('Concurrent different keys preserved',all(x.get('code')==200 for x in out))
 with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(concurrent_create,['same_key','same_key']))
 check('Concurrent same key single row',sum(x.get('code')==200 for x in out)==1 and scalar("select count(*) from custom_sections where product_revision_id=? and section_key='same_key'",(rid,))==1)
 token=get(path)['token'];tr={'language_code':'en','translation_status':'draft','title':'Concurrent TEST','content':{'text':'Concurrent'}}
 with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(lambda _:req(path+'/'+ids['text']+'/translations',{'expected_token':token,'translation':tr},'PUT'),range(2)))
 check('Concurrent translation conflict no duplicates',sum(x.get('code')==200 for x in out)==1 and scalar('select count(*) from custom_section_translations where custom_section_id=? and language_code="en"',(ids['text'],))==1)
 temp=mustput(path,sample('delete_test'));check('Delete draft section',req(path+'/'+temp,{'expected_token':get(path)['token']},'DELETE').get('code')==200)
 # Freeze and direct SQL trigger enforcement.
 r=get(pp)['revisions'][0];check('Seal with sections',req(pp+'/revisions/'+rid+'/seal',{'expected_token':r['token']}).get('code')==200)
 before=get(path)
 check('Frozen section update rejected',put(path,sample('test_text',hide=True),ids['text']).get('code')==409)
 check('Frozen translation rejected',req(path+'/'+ids['text']+'/translations',{'expected_token':before['token'],'translation':tr},'PUT').get('code')==409)
 check('Frozen delete rejected',req(path+'/'+ids['text'],{'expected_token':before['token']},'DELETE').get('code')==409)
 check('Frozen reorder rejected',req(path+'/reorder',{'expected_token':before['token'],'keys':[x['section_key'] for x in before['sections']]},'PUT').get('code')==409)
 for sql,args in [('update custom_sections set allow_hide=1 where id=?',(ids['text'],)),('delete from custom_section_translations where custom_section_id=?',(ids['text'],))]:
  with db() as c:
   try:c.execute(sql,args);frozen=False
   except sqlite3.IntegrityError:frozen=True
  check('DB freeze '+sql,frozen)
 check('Frozen aggregate unchanged',get(path)==before)
 r2=ok(pp+'/revisions',{'source_revision_id':rid})['id'];path2=f'{pp}/revisions/{r2}/sections';cloned=get(path2)
 check('Clone all sections',len(cloned['sections'])==len(before['sections']))
 check('Clone all new section IDs',not {x['id'] for x in cloned['sections']} & {x['id'] for x in before['sections']})
 check('Clone translations and IDs',sum(len(x['translations']) for x in cloned['sections'])==sum(len(x['translations']) for x in before['sections']) and not {t['id'] for x in cloned['sections'] for t in x['translations']} & {t['id'] for x in before['sections'] for t in x['translations']})
 row=next(x for x in cloned['sections'] if x['section_key']=='test_text');d=sample('test_text',hide=True);d['translations'][0]['content']['text']='R2 changed';check('Clone draft editable',put(path2,d,row['id']).get('code')==200);check('Clone change does not affect base',get(path)==before)
 ok(pp+'/default-revision',{'revision_id':rid,'expected_current_revision_id':None},'PUT')
 bid=ok('passport-batches',{'product_id':pid,'batch_code':'PF-T7-API-BATCH-'+runid,'content':{'quality_status':'pending'},'overrides':[],'inspections':[]})['id'];bp='passport-batches/'+bid;bs=bp+'/sections';s=get(bs)
 check('Batch inherits without copied rows',len(s['sections'])==0 and len(s['effective'])==len(before['effective']) and all(x['source']=='inherited' for x in s['effective']))
 d=sample('test_text');d['operation']='replace';d['translations'][0]['content']['text']='Batch TEST override';oid=mustput(bs,d)
 check('Override effective',next(x for x in get(bs)['effective'] if x['section_key']=='test_text')['source']=='overridden');check('Base unchanged by override',get(path)==before)
 check('Reset override',req(bs+'/'+oid,{'expected_token':get(bs)['token']},'DELETE').get('code')==200 and next(x for x in get(bs)['effective'] if x['section_key']=='test_text')['source']=='inherited')
 d=sample('test_text');d.update(operation='hide',is_visible=False,translations=[]);hid=mustput(bs,d);s=get(bs)
 check('Hide removes content retains provenance',not any(x['section_key']=='test_text' for x in s['effective']) and any(x['section_key']=='test_text' and 'content' not in x and not x['title'] for x in s['hidden']))
 check('Reset hide',req(bs+'/'+hid,{'expected_token':s['token']},'DELETE').get('code')==200 and any(x['section_key']=='test_text' for x in get(bs)['effective']))
 d=sample('test_table','table');d.update(operation='hide',is_visible=False,translations=[]);check('Cannot hide mandatory base',put(bs,d).get('code')==422)
 d=sample('test_table','table');d.update(operation='replace',is_visible=False);check('Cannot bypass hide with replace visibility',put(bs,d).get('code')==422)
 d=sample('test_table','table');d.update(operation='replace',status='disabled');check('Cannot bypass hide with disabled status',put(bs,d).get('code')==422)
 d=sample('test_text');d.update(operation='inherit',is_public=True,translations=[]);check('Inherit cannot promote private',put(bs,d).get('code')==422)
 d=sample('not_in_base');d['operation']='replace';check('Missing base override rejected',put(bs,d).get('code')==422)
 check('Add colliding base key rejected',put(bs,sample('test_text')).get('code')==422)
 d=sample('test_text');d.update(operation='inherit',sort_order=1,translations=[]);oid=mustput(bs,d);check('Inherit order override',get(bs)['effective'][0]['section_key']=='test_text');ok(bs+'/'+oid,{'expected_token':get(bs)['token']},'DELETE')
 own=mustput(bs,sample('customer_requirement'));check('Batch-only source',next(x for x in get(bs)['effective'] if x['section_key']=='customer_requirement')['source']=='batch-only');check('Batch-only does not pollute template',get(path)==before)
 d=sample('test_text');d['operation']='replace';oid=mustput(bs,d)
 b=get(bp);cid=ok(bp+'/clone',{'batch_code':'PF-T7-API-CLONE-'+runid,'expected_edit_version':b['batch']['edit_version']})['id'];cs='passport-batches/'+cid+'/sections'
 check('Clone batch local operations',len(get(cs)['sections'])==2 and not {x['id'] for x in get(cs)['sections']} & {x['id'] for x in get(bs)['sections']})
 check('Clone batch old content intact',get(bp)==b)
 check('T6 resolver composition',get(bp)['effective_sections']==get(bs)['effective'])
 # ACL all 14 routes, plus an authenticated role without section grants.
 rolekey='t7_none-'+runid;ok('role',{'roleName':'T7 no section access','roleKey':rolekey,'roleSort':99,'status':'2','admin':False,'dataScope':'1','menuIds':[]});role=scalar('select role_id from sys_role where role_key=?',(rolekey,));ok('sys-user',{'username':'t7-no-access-'+runid,'password':cred['test_password'],'nickName':'T7 Test','phone':'00000000000','email':'t7@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
 denied=req('login',{'username':'t7-no-access-'+runid,'password':cred['test_password'],'code':'0','uuid':'T7'},token=None)['token']
 for root,sid in [(path,ids['text']),(bs,own)]:
  for method,suffix in [('GET',''),('GET','/'+sid),('POST',''),('PUT','/'+sid),('DELETE','/'+sid),('PUT','/reorder'),('PUT','/'+sid+'/translations')]:
   check('Anonymous '+method+root+suffix,req(root+suffix,None if method=='GET' else {},method,token=None).get('code')==401)
   check('Casbin '+method+root+suffix,req(root+suffix,None if method=='GET' else {},method,token=denied).get('code')==403)
 check('Audits generated',scalar("select count(distinct event_type) from passport_audit_events where event_type like '%section%'")>=9)
 paths=[pp,path,path2,bp,bs,cs];(rt/'test-artifacts/api-fixtures.json').write_text(json.dumps({'product':pid,'r1':rid,'r2':r2,'batch':bid,'clone':cid,'snapshots':{p:get(p) for p in paths}},ensure_ascii=False,indent=2))
except Exception as e:
 checks.append({'name':'harness completion','status':'FAIL','error':repr(e)});raise
finally:
 (rt/f'test-artifacts/api-{mode}.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'checks',sum(x['status']=='FAIL' for x in checks),'FAIL')
