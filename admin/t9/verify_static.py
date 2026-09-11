from pathlib import Path
import socket,errno,urllib.request,urllib.error,json,hashlib
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t9';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
for port in [18103,18104,19534,19535]:
 with socket.socket() as s:s.settimeout(1);check('Backend/UI stopped '+str(port),s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED)
root=rt/'publish'
for p in sorted(root.rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(root))
 with urllib.request.urlopen('http://127.0.0.1:19536/'+rel) as f:raw=f.read();mime=f.headers.get_content_type()
 check('Backend-off static '+rel,hashlib.sha256(raw).digest()==hashlib.sha256(p.read_bytes()).digest() and mime==('application/json' if p.suffix=='.json' else 'image/png'))
 if p.suffix=='.json':
  data=json.loads(raw)
  for a in data['assets']:
   with urllib.request.urlopen('http://127.0.0.1:19536/'+a['path']) as f:b=f.read()
   check('Backend-off referenced image '+rel+' '+a['key'],hashlib.sha256(b).hexdigest()==a['sha256'])
for rel in ['published/TEST-ABSENT.json','assets/sha256/aa/'+'a'*64+'.png','../private-media/','%2e%2e/settings.yml','tmp/','']:
 try:urllib.request.urlopen('http://127.0.0.1:19536/'+rel);status=200
 except urllib.error.HTTPError as e:status=e.code
 check('Missing/unsafe static returns 404 '+rel,status==404)
(rt/'test-artifacts/static-independent.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS')
