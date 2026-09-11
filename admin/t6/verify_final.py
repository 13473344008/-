from pathlib import Path
import json,hashlib,sqlite3,socket,subprocess,datetime,errno
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t6';checks=[]
def check(name,v):
 checks.append({'name':name,'status':'PASS' if v else 'FAIL','time':datetime.datetime.now(datetime.timezone.utc).isoformat()});assert v,name
b=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];check('Original 53 baseline hashes unchanged',len(b)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items()));check('All 7 site files unchanged',sum(p.startswith('site/') for p in b)==7 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items() if p.startswith('site/')))
old=json.loads((rt/'test-artifacts/protected-before.json').read_text());check('T4 T5 protected evidence code and historical migrations unchanged',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in old.items()))
for repo,sha in [('go-admin','595c4a6be5b1aade8dc30fe2b90ea13dfba61b05'),('go-admin-ui','e106f68d362d3a7aaa43244eb74cede1a83f4da5')]:check(repo+' commit remains locked',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'admin'/repo,text=True).strip()==sha)
for name in ['passport-admin-t6.db','fresh-acceptance.db','service-final.db','upgrade-from-t5.db']:
 with sqlite3.connect(rt/'db'/name) as c:
  check(name+' integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check(name+' foreign_key_check empty',c.execute('pragma foreign_key_check').fetchall()==[])
with sqlite3.connect(rt/'db/passport-admin-t6.db') as c:
 for table,cols in [('batches','batch_code'),('batch_overrides','batch_id,field_key'),('inspection_items','batch_id,item_code')]:check('No duplicates '+table,len(c.execute('select '+cols+',count(*) from '+table+' group by '+cols+' having count(*)>1').fetchall())==0)
 check('No invalid fixed base relation',c.execute("select count(*) from batches b left join product_revisions r on r.id=b.base_product_revision_id and r.product_id=b.product_id where r.id is null or r.revision_status!='sealed'").fetchone()[0]==0)
 for table in ['batch_overrides','inspection_items','passport_audit_events']:check('No orphan batch ownership '+table,c.execute('select count(*) from '+table+' x left join batches b on b.id=x.batch_id where x.batch_id is not null and b.id is null').fetchone()[0]==0)
 check('No formal review or publish data in T6 working DB',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in ['passport_revisions','published_assets','publish_records','custom_sections','certifications']) and c.execute("select count(*) from batches where workflow_status!='draft' or submitted_at is not null or current_passport_revision_id is not null").fetchone()[0]==0)
 check('Five Batch business APIs registered',c.execute("select count(*) from sys_api where path like '/api/v1/passport-batches%'").fetchone()[0]==5)
 check('All 11 migrations recorded',c.execute('select count(*) from sys_migration').fetchone()[0]==11)
 tables=json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables'];check('19 business tables and 308 columns unchanged',len(tables)==19 and sum(len(c.execute('pragma table_info('+t+')').fetchall()) for t in tables)==308)
 check('104 business triggers retained',c.execute("select count(*) from sqlite_master where type='trigger'").fetchone()[0]==104)
 check('T6 work records explicitly test',c.execute("select count(*) from batches where record_type!='test'").fetchone()[0]==0)
for port in [18097,18098,19529]:
 with socket.socket() as s:s.settimeout(1);check('T6 local service stopped '+str(port),s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED)
check('Backend upstream tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin',text=True)=='')
ui_changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui',text=True).splitlines();check('Only two UI locale entrypoints modified',sorted(ui_changes)==['src/lang/en-US/index.ts','src/lang/zh-CN/index.ts'])
for repo in ['go-admin','go-admin-ui']:check(repo+' diff check',subprocess.run(['git','diff','--check'],cwd=R/'admin'/repo,capture_output=True).returncode==0)
for p in (rt/'db').glob('*.db'):p.chmod(0o600)
for p in rt.glob('*.yml'):p.chmod(0o600)
(rt/'test-artifacts/final-tests.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'PASS')
