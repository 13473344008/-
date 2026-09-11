import verify_api as v
from verify_api import *
try:
 before=json.loads((rt/'test-artifacts/restart-before.json').read_text())
 for name,tables in before.items():
  with sqlite3.connect(rt/'db'/name) as c:
   for table,rows in tables.items():check(name+' restart exact '+table,[list(x) for x in c.execute('select * from '+table+' order by id')]==rows)
 for mode,port in [('initial',18101),('fresh',18102)]:
  v.base=f'http://127.0.0.1:{port}/api/v1/';v.admin=login(cred['admin_username'],cred['admin_password']);f=json.loads((rt/'test-artifacts'/('fresh-api-fixtures.json' if mode=='fresh' else 'api-fixtures.json')).read_text())
  for bid,state in f['snapshots'].items():check(mode+' restart API exact review '+bid,ok('passport-batches/'+bid+'/review')==state)
  f=json.loads((rt/'test-artifacts'/('fresh-browser-fixtures.json' if mode=='fresh' else 'browser-fixtures.json')).read_text());x=ok('passport-batches/'+f['bid']+'/review');check(mode+' browser approved history survives restart',x['state']=='ready_for_publish' and len(x['history'])==2 and x['history'][1]['decision']=='rejected')
finally:(rt/'test-artifacts/restart.json').write_text(json.dumps(checks,indent=2))
