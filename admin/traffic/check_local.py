from pathlib import Path
import json,urllib.request,urllib.error,sqlite3,time
R=Path(__file__).resolve().parents[2];m=R/'runtime/t12-manual-20260911';base='http://127.0.0.1:18121/api/v1/';cred=json.loads((R/'runtime/t12-fix/credentials.json').read_text());users=json.loads((R/'runtime/t12-fix/test-artifacts/users.json').read_text());checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n

def req(path,data=None,token=None,headers=None):
 h={'Content-Type':'application/json',**(headers or {})}
 if token:h['Authorization']='Bearer '+token
 try:
  with urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(data).encode() if data else None,headers=h),timeout=10) as r:return json.load(r)
 except urllib.error.HTTPError as e:return json.load(e)
try:
 for role in ['editor','reviewer','viewer','admin']:
  d=req('login',{'username':cred['admin_username'] if role=='admin' else users[role]['username'],'password':cred['admin_password'] if role=='admin' else cred['test_password'],'code':'0','uuid':'traffic'},headers={'X-Forwarded-For':'8.8.8.8'});check(role+' login',d['code']==200);token=d['token'];v=req('passport-traffic?days=7&pageIndex=1&pageSize=20',token=token);check(role+' scoped statistics',v['code']==200 and v['data']['available']);check(role+' no visitor identities',all(x not in json.dumps(v['data']) for x in ['127.0.0.1','8.8.8.8','user_agent','visitor_id']));check(role+' real region database configured',v['data']['geo_ready'])
 before=req('passport-traffic?batch_code=PF-T12-TEST-001',token=token)['data']['count']
 with urllib.request.urlopen('http://127.0.0.1:19554/b/PF-T12-TEST-001') as r:check('Actual static page accessible',r.status==200)
 after=req('passport-traffic?batch_code=PF-T12-TEST-001',token=token)['data'];check('One page request adds one real visit',after['count']==before+1);check('Local visits labeled local',all(x['region']=='Local network' for x in after['list']));check('Unknown batch returns empty',req('passport-traffic?batch_code=NOT-A-BATCH',token=token)['data']['count']==0);check('Invalid date window422',req('passport-traffic?days=1000',token=token)['code']==422);check('Anonymous statistics denied',req('passport-traffic')['code']==401)
 time.sleep(1)
 with sqlite3.connect(m/'db/manual.db') as c:
  row=c.execute('select ipaddr,login_location from sys_login_log order by id desc limit 1').fetchone();check('Login IP header cannot spoof location',row==('127.0.0.1','Local network'));check('New operation locations recorded',c.execute("select count(*) from sys_opera_log where oper_location='Local network'").fetchone()[0]>0);check('Database integrity',c.execute('pragma integrity_check').fetchone()[0]=='ok');check('Foreign keys',not c.execute('pragma foreign_key_check').fetchall());check('18 migrations',c.execute('select count(*) from sys_migration').fetchone()[0]==18)
 print('Checks passed:',len(checks))
finally:(m/'change-evidence/api-checks.json').write_text(json.dumps(checks,indent=2))
