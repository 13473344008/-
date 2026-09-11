from pathlib import Path
import json,hashlib,urllib.request,socket
rt=Path('runtime/t12-fix');checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
def get(p):
 with urllib.request.urlopen('http://127.0.0.1:19544/'+p) as r:return r.read(),r.headers
try:
 check('SQLite configured path remains offline',not (rt/'db/passport-admin-t12-fix.db').exists())
 for port in [18111,19543]:
  with socket.socket() as s:check('Backend UI unavailable '+str(port),s.connect_ex(('127.0.0.1',port))!=0)
 for n in [1,2,3]:
  raw,h=get('versions/PF-T12-TEST-001/v'+str(n)+'.json');p=json.loads(raw);check('Restored historical V'+str(n),p['publication']['version']==n if 'version' in p['publication'] else p['publication']['version_number']==n)
  for a in p['assets']:
   raw,h=get(a['path']);check('Restored V'+str(n)+' image '+a['key'],hashlib.sha256(raw).hexdigest()==a['sha256'] and len(raw)==a['file_size']);check('Restored image immutable '+a['key'],'immutable' in h['Cache-Control'])
 for p in (rt/'backups/restored-publish/assets').rglob('*.png'):
  rel=str(p.relative_to(rt/'backups/restored-publish'));raw,h=get(rel);check('Every restored CAS image reachable '+p.name,raw==p.read_bytes())
finally:(rt/'test-artifacts/restored-http.json').write_text(json.dumps(checks,indent=2))
