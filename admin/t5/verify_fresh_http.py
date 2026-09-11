import json,urllib.request,datetime
from pathlib import Path
rt=Path(__file__).resolve().parents[2]/'runtime/t5';c=json.loads((rt/'credentials.json').read_text());checks=[]
def req(path,data=None,token=None):
 h={'Content-Type':'application/json'}
 if token:h['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18096/api/v1/'+path,data=None if data is None else json.dumps(data).encode(),headers=h),timeout=10) as f:return json.load(f)
def check(name,v):
 checks.append({'name':name,'status':'PASS' if v else 'FAIL','time':datetime.datetime.now(datetime.timezone.utc).isoformat()});assert v,name
x=req('login',{'username':'admin','password':c['admin_password'],'code':'0','uuid':'T5'});check('Fresh database actual login',x['code']==200);t=x['token'];x=req('passport-products',token=t);check('Fresh products API initially empty',x['code']==200 and x['data']['count']==0)
x=req('passport-products',{'product_code':'PF-T5-FRESH-TEST','content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','product_name':'T5 Fresh — TEST RECORD — NOT FOR COMMERCIAL USE','process_labels':{}}]},t);check('Fresh product creation through HTTP',x['code']==200);id=x['data']['id'];x=req('passport-products/'+id,token=t);check('Fresh R1 and translation usable',x['code']==200 and len(x['data']['revisions'])==1 and len(x['data']['revisions'][0]['translations'])==1)
(rt/'test-artifacts/fresh-http-tests.json').write_text(json.dumps(checks,indent=2));print('Fresh HTTP',len(checks),'PASS')
