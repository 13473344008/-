# Reuse transport helpers, without running the main acceptance suite.
from pathlib import Path
exec((Path(__file__).with_name('verify_api.py')).read_text().split('\ntry:\n')[0])
try:
 x=req('login',{'username':cred['admin_username'],'password':cred['admin_password'],'code':'0','uuid':'T7'},token=None);admin=x['token']
 f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());p=f['product'];r=f['r2'];bid=f['batch'];path=f'passport-products/{p}/revisions/{r}/sections';bs=f'passport-batches/{bid}/sections'
 # Reserve explicit grants through upstream roles/users and verify parent ownership scope.
 key='t7_owner_'+runid
 ok('role',{'roleName':'T7 owner test','roleKey':key,'roleSort':99,'status':'2','admin':False,'dataScope':'5','menuIds':[9100,9101,9102,9201,9202,9301,9302]})
 role=scalar('select role_id from sys_role where role_key=?',(key,));ok('sys-user',{'username':key,'password':cred['test_password'],'nickName':'T7 Owner TEST','phone':'00000000000','email':'t7@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
 owner=req('login',{'username':key,'password':cred['test_password'],'code':'0','uuid':'T7'},token=None)['token']
 for root in [path,bs]:
  check('Owner scope denies foreign read '+root,req(root,token=owner).get('code')==404)
  check('Owner scope denies foreign write '+root,req(root,{'expected_token':get(root)['token'],'section':sample('foreign')},'POST',token=owner).get('code')==404)
 token=get(path)['token'];d=sample('bad_null','table');d['translations'][0]['content']['rows'][0]['cells']=[None];check('HTTP rejects null table cell',put(path,d).get('code')==422)
 row=get(path)['sections'][0];d={k:row[k] for k in sample('x')};d['translations']=[{k:t[k] for k in ['language_code','translation_status','title','content']} for t in row['translations']];d['section_key']='renamed';check('Stable section key immutable',put(path,d,row['id']).get('code')==422)
 d=sample('sealed_insert');check('Sealed add rejected',put(f'passport-products/{p}/revisions/{f["r1"]}/sections',d).get('code')==409)
 before=get(bs);bp=f'passport-batches/{bid}';b=get(bp)
 # T6 aggregate save changes core work but must keep T7 operations and content.
 content={k:b['batch'][k] for k in ['production_date','expiry_date','quality_status','internal_note']};content['internal_note']='T7 regression TEST only'
 check('T6 save with T7 sections',req(bp,{'expected_edit_version':b['batch']['edit_version'],'content':content,'overrides':[],'inspections':[]},'PUT').get('code')==200)
 check('T6 save preserves section aggregate',get(bs)==before)
 # Audit failure on deletion must retain section, translations, edit counter and audit.
 before=get(bs);b=get(bp);sid=next(x['id'] for x in before['sections'] if x['operation']=='add')
 with db() as c:c.execute("CREATE TRIGGER t7_delete_fail BEFORE INSERT ON passport_audit_events BEGIN SELECT RAISE(ABORT,'injected'); END")
 try:check('Delete audit fault rejected',req(bs+'/'+sid,{'expected_token':before['token']},'DELETE').get('code')!=200)
 finally:
  with db() as c:c.execute('DROP TRIGGER t7_delete_fail')
 check('Delete rolls translations counters audit back',get(bs)==before and get(bp)==b)
 # Refresh persistence baseline after the authorized core-field regression edit.
 f['snapshots']={p:get(p) for p in f['snapshots']};(rt/'test-artifacts/api-fixtures.json').write_text(json.dumps(f,ensure_ascii=False,indent=2))
except Exception as e:
 checks.append({'name':'Edges completion','status':'FAIL','error':repr(e)});raise
finally:
 (rt/'test-artifacts/edges.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'checks',sum(x['status']=='FAIL' for x in checks),'FAIL')
