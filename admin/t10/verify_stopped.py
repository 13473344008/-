import socket,errno,json
from pathlib import Path
checks=[]
for port in [18105,18106,19536,19538]:
 with socket.socket() as s:
  s.settimeout(1);ok=s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED;checks.append({'name':'T10 service stopped '+str(port),'status':'PASS' if ok else 'FAIL'});assert ok,port
Path('runtime/t10/test-artifacts/stopped.json').write_text(json.dumps(checks,indent=2));print('All four T10 local ports stopped')
