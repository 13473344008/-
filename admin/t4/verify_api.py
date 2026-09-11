import json,urllib.request,urllib.error,sqlite3,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t4';cred=json.loads((rt/'credentials.json').read_text());results=[]
def req(path,data=None,token=None,method=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 r=urllib.request.Request('http://127.0.0.1:18094/api/v1/'+path,data=None if data is None else json.dumps(data).encode(),headers=h,method=method)
 try:
  with urllib.request.urlopen(r,timeout=15) as f:return json.load(f)
 except urllib.error.HTTPError as e:return json.loads(e.read())
def check(name,v):
 results.append({'name':name,'status':'PASS' if v else 'FAIL'})
 if not v:raise AssertionError(name)
def login(who):
 x=req('login',{'username':cred[who+'_username'],'password':cred[who+'_password'],'code':'0','uuid':'T4'})
 check(who+' JWT login',x.get('code')==200 and bool(x.get('token')));return x['token']
try:
 admin=login('admin');check('JWT authenticated getinfo',req('getinfo',token=admin).get('code')==200)
 check('invalid JWT denied',req('getinfo',token='invalid').get('code')==401)
 if len(sys.argv)==1:
  x=req('role',{'roleName':'T4 Test Reader','roleKey':'t4_reader','roleSort':99,'status':'2','admin':False,'dataScope':'1','menuIds':[1,52],'remark':'T4 TEST RECORD — NOT FOR COMMERCIAL USE'},admin)
  check('create test role API',x.get('code')==200)
  c=sqlite3.connect(rt/'db/passport-admin-validated.db');role=c.execute("select role_id from sys_role where role_key='t4_reader'").fetchone()[0]
  x=req('sys-user',{'username':cred['test_username'],'password':cred['test_password'],'nickName':'T4 Reader','phone':'00000000000','email':'t4@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2','sex':'0','remark':'T4 TEST'},admin)
  check('create test user API',x.get('code')==200)
 reader=login('test')
 allowed=req('role?pageIndex=1&pageSize=10',token=reader);denied=req('sys-user?pageIndex=1&pageSize=10',token=reader)
 check('reader granted role GET',allowed.get('code')==200);check('reader ungranted user GET denied',denied.get('code')==403)
 c=sqlite3.connect(rt/'db/passport-admin-validated.db');check('role user link in SQLite',c.execute("select count(*) from sys_user u join sys_role r on u.role_id=r.role_id where u.username='t4-reader' and r.role_key='t4_reader'").fetchone()[0]==1)
 check('Casbin persisted policies',c.execute("select count(*) from casbin_rule where v0='t4_reader'").fetchone()[0]>0)
 check('role menu relation persisted',c.execute("select count(*) from sys_role_menu m join sys_role r on m.role_id=r.role_id where r.role_key='t4_reader'").fetchone()[0]>0)
except Exception as e:
 results.append({'name':'API harness completion','status':'FAIL','detail':str(e)});raise
finally:
 label='api-restart' if len(sys.argv)>1 else 'api-initial';(rt/'evidence'/f'{label}.json').write_text(json.dumps(results,indent=2));print(label,results)
