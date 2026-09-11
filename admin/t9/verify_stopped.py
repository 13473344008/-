from pathlib import Path
import socket,errno,json
checks=[]
for port in [18103,18104,19534,19535,19536]:
 with socket.socket() as s:s.settimeout(1);ok=s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED
 checks.append({'name':'Stopped localhost:'+str(port),'status':'PASS' if ok else 'FAIL'});assert ok,port
(Path(__file__).resolve().parents[2]/'runtime/t9/test-artifacts/stopped.json').write_text(json.dumps(checks,indent=2));print('5/5 localhost ports stopped')
