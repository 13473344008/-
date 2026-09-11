# Business-specific contract check. The upstream heuristic does not scan app/passport.
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[2];backend=R/'admin/go-admin/app/passport';front=R/'admin/go-admin-ui/src/api/passport/history.ts';structs={};checks=[]
for root in ['models','service','service/dto']:
 for p in (backend/root).glob('*.go'):
  if p.name.endswith('_test.go'):continue
  text=p.read_text()
  for name,body in re.findall(r'type (\w+) struct \{(.*?)\n\}',text,re.S):
   fields=set(re.findall(r'json:"([^",]+)',body)) - {'-'};embeds=re.findall(r'^\s*(?:models\.)?(\w+)\s*$',body,re.M);structs[name]=(fields,embeds)
def fields(name):
 own,embedded=structs[name];out=set(own)
 for e in embedded:
  if e in structs:out.update(fields(e))
 return out
source=front.read_text()
for ts,go in [('RollbackRequest','RollbackRequest'),('CurrentHealth','CurrentHealth'),('VersionHistory','VersionHistory'),('VersionDetail','VersionDetail'),('VersionDiff','VersionDiff'),('Difference','Difference'),('IntegrityResult','IntegrityResult'),('AuditItem','AuditItem') ]:
 body=re.search(r'export interface '+ts+r' \{(.*?)(?=\nexport |\nconst )',source,re.S)[1]
 # Fields at the outer object level only, including one-line interfaces.
 depth=0;part='';outer=''
 for char in body:
  if char=='{':depth+=1
  elif char=='}':depth-=1
  if depth==0:outer+=char
 props=set(re.findall(r'(?:^|;)\s*(\w+)\??\s*:',outer));missing=props-fields(go)
 checks.append({'name':ts+' TypeScript properties match '+go,'status':'PASS' if not missing else 'FAIL','missing':sorted(missing)});assert not missing,(ts,missing)
(R/'runtime/t10/test-artifacts/contracts.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS; upstream generic check is separately reported')
