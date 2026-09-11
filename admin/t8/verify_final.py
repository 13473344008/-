from pathlib import Path
import json,hashlib,sqlite3,socket,subprocess,errno
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t8';checks=[]
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
b=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];check('53 original hashes unchanged',len(b)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items()));check('7 site files unchanged',sum(p.startswith('site/') for p in b)==7 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items() if p.startswith('site/')))
old=json.loads((rt/'test-artifacts/protected-before.json').read_text());changed=[p for p,h in old.items() if not (R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('36278 historical protected files and T4-T7 migrations unchanged',len(old)==36278 and not changed)
for repo,sha in [('go-admin','595c4a6be5b1aade8dc30fe2b90ea13dfba61b05'),('go-admin-ui','e106f68d362d3a7aaa43244eb74cede1a83f4da5')]:check(repo+' locked commit',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'admin'/repo,text=True).strip()==sha)
for p in sorted((rt/'db').glob('*.db')):
 with sqlite3.connect(p) as c:
  check(p.name+' integrity ok',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check(p.name+' foreign keys clean',c.execute('pragma foreign_key_check').fetchall()==[])
  check(p.name+' unique review attempt',c.execute('select count(*) from (select batch_id,attempt_number from review_records group by batch_id,attempt_number having count(*)>1)').fetchone()[0]==0)
  check(p.name+' one pending attempt per batch',c.execute("select count(*) from (select batch_id from review_records where decision='pending' group by batch_id having count(*)>1)").fetchone()[0]==0)
  check(p.name+' no orphan review',c.execute('select count(*) from review_records r left join batches b on b.id=r.batch_id where b.id is null').fetchone()[0]==0)
  check(p.name+' no leftover injected trigger',c.execute("select count(*) from sqlite_master where type='trigger' and name like 't8_%'").fetchone()[0]==0)
  if p.name in ['passport-admin-t8.db','fresh-acceptance.db']:
   check(p.name+' locked candidate matches review',c.execute("select count(*) from batches b left join review_records r on r.id=b.current_review_record_id where b.workflow_status='pending_review' and (r.id is null or r.batch_id!=b.id or r.decision not in ('pending','approved') or r.candidate_input!=b.submitted_input or r.candidate_hash!=b.submitted_content_hash or r.source_edit_version!=b.edit_version)").fetchone()[0]==0)
   check(p.name+' all candidate hashes verified',all(hashlib.sha256(raw.encode()).hexdigest()==h for raw,h in c.execute('select candidate_input,candidate_hash from review_records')))
   check(p.name+' no self decisions',c.execute('select count(*) from review_records r,json_each(r.contributors) a where r.reviewed_by=a.value').fetchone()[0]==0)
   check(p.name+' no public snapshots or published assets',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in ['passport_revisions','published_assets','publish_records']))
   check(p.name+' approved history audited',c.execute("select count(*) from review_records r where r.decision in ('approved','rejected') and not exists(select 1 from passport_audit_events a where a.batch_id=r.batch_id and a.event_type='review_'||r.decision and json_extract(a.after_data,'$.review_id')=r.id)").fetchone()[0]==0)
with sqlite3.connect(rt/'db/passport-admin-t8.db') as c:
 tables=list(json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables'])+['review_records'];check('20 business tables 327 columns',len(tables)==20 and sum(len(c.execute('pragma table_info('+t+')').fetchall()) for t in tables)==327)
 check('109 integrity and freeze triggers',c.execute("select count(*) from sqlite_master where type='trigger'").fetchone()[0]==109)
 check('8 new review APIs',c.execute('select count(*) from sys_api where id between 9401 and 9408').fetchone()[0]==8)
 check('13 migrations',c.execute('select count(*) from sys_migration').fetchone()[0]==13)
check('Backend tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin',text=True)=='')
changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui',text=True).splitlines();check('Only two UI locale tracked entries',sorted(changes)==['src/lang/en-US/index.ts','src/lang/zh-CN/index.ts'])
for repo in ['go-admin','go-admin-ui']:check(repo+' diff check',subprocess.run(['git','diff','--check'],cwd=R/'admin'/repo,capture_output=True).returncode==0)
for port in [18101,18102,19532,19533]:
 with socket.socket() as s:s.settimeout(1);check('Local stopped '+str(port),s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED)
(rt/'test-artifacts/final.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS; protected',len(old))
