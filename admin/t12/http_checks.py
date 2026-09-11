import http.client,json
from pathlib import Path
rt=Path('runtime/t12');checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
def get(path,headers={}):
 c=http.client.HTTPConnection('127.0.0.1',19542);c.request('GET',path,headers=headers);r=c.getresponse();body=r.read();out=(r.status,dict((k.lower(),v) for k,v in r.getheaders()),body);c.close();return out
try:
 for p in ['/b/../../etc/passwd','/b/%2e%2e/%2e%2e/etc/passwd','/b/%252e%252e','/b/PF%2fTEST','/b/PF\\TEST','/b/'+'x'*65,'/private-media/a.png','/versions/a.json','/assets/no.png','/products/PF-STD.json','/batches/PF-TEST.json']:
  check('HTTP traversal/restricted '+p,get(p)[0] in [400,404])
 status,heads,raw=get('/published/PF-T12-TEST-001.json');check('Current JSON MIME',status==200 and 'application/json' in heads['content-type']);check('Current revalidation', 'no-cache' in heads['cache-control']);p=json.loads(raw)
 for path in ['/versions/PF-T12-TEST-001/v1.json']:
  status,hh,_=get(path);check('Immutable cache '+path,status==200 and 'immutable' in hh['cache-control']);check('ETag 304 '+path,get(path,{'If-None-Match':hh['etag']})[0]==304)
 status,hh,_=get('/b/PF-T12-TEST-001');check('HTML no-cache','no-cache' in hh['cache-control']);check('CSP without unsafe-inline',"default-src 'none'" in hh['content-security-policy'] and 'unsafe-inline' not in hh['content-security-policy']);check('frame ancestors none',"frame-ancestors 'none'" in hh['content-security-policy']);check('nosniff',hh['x-content-type-options']=='nosniff');check('referrer policy',hh['referrer-policy']=='no-referrer');check('No indexing','noindex' in hh['x-robots-tag']);check('Missing JSON actual404',get('/published/TEST-NO.json')[0]==404);check('Missing image actual404',get('/assets/sha256/aa/'+'a'*64+'.png')[0]==404)
 secret=rt/'private-media/t12-symlink-test.txt';secret.write_text('T12 NONSECRET SYMLINK PROBE');link=rt/'publish/published/PF-T12-TEST-SYMLINK.json';link.symlink_to(secret.resolve())
 try:check('Nginx symlink escape denied',get('/published/PF-T12-TEST-SYMLINK.json')[0] in [403,404])
 finally:link.unlink();secret.unlink()
finally:(rt/'test-artifacts/http-checks.json').write_text(json.dumps(checks,indent=2));print(len(checks),'checks')
