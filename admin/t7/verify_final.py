from pathlib import Path
import json,hashlib,sqlite3,socket,subprocess,errno
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t7';checks=[]
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
b=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];check('53 original hashes unchanged',len(b)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items()));check('7 site files unchanged',sum(p.startswith('site/') for p in b)==7 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items() if p.startswith('site/')))
old=json.loads((rt/'test-artifacts/protected-before.json').read_text());changed=[p for p,h in old.items() if not (R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('T4 T5 T6 protected evidence and migrations unchanged',not changed)
for repo,sha in [('go-admin','595c4a6be5b1aade8dc30fe2b90ea13dfba61b05'),('go-admin-ui','e106f68d362d3a7aaa43244eb74cede1a83f4da5')]:check(repo+' locked commit',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'admin'/repo,text=True).strip()==sha)
for p in sorted((rt/'db').glob('*.db')):
 with sqlite3.connect(p) as c:
  check(p.name+' integrity ok',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check(p.name+' foreign keys clean',c.execute('pragma foreign_key_check').fetchall()==[])
  for table,cols in [('custom_sections','product_revision_id,section_key'),('custom_sections','batch_id,section_key'),('custom_section_translations','custom_section_id,language_code')]:
   field=cols.split(',')[0];check(p.name+' UNIQUE '+cols,c.execute('select count(*) from (select '+cols+' from '+table+' where '+field+' is not null group by '+cols+' having count(*)>1)').fetchone()[0]==0)
  check(p.name+' section owner source valid',c.execute('select count(*) from custom_sections s left join product_revisions r on r.id=s.product_revision_id left join batches b on b.id=s.batch_id left join product_revisions br on br.id=b.base_product_revision_id where (s.product_revision_id is not null)+(s.batch_id is not null)!=1 or (s.product_revision_id is not null and (r.id is null or s.source_language!=r.source_language or s.operation!="add")) or (s.batch_id is not null and (b.id is null or s.source_language!=br.source_language))').fetchone()[0]==0)
  check(p.name+' no orphan translations',c.execute('select count(*) from custom_section_translations t left join custom_sections s on s.id=t.custom_section_id where s.id is null').fetchone()[0]==0)
  check(p.name+' valid override targets',c.execute("select count(*) from custom_sections s join batches b on b.id=s.batch_id left join custom_sections base on base.product_revision_id=b.base_product_revision_id and base.section_key=s.section_key where (s.operation='add' and base.id is not null) or (s.operation!='add' and base.id is null)").fetchone()[0]==0)
  check(p.name+' no active test fault trigger',c.execute("select count(*) from sqlite_master where type='trigger' and name like 't7_%'").fetchone()[0]==0)
with sqlite3.connect(rt/'db/passport-admin-t7.db') as c:
 tables=json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables'];check('19 business tables 309 columns',len(tables)==19 and sum(len(c.execute('pragma table_info('+t+')').fetchall()) for t in tables)==309)
 check('104 freeze and integrity triggers retained',c.execute("select count(*) from sqlite_master where type='trigger'").fetchone()[0]==104)
 check('14 T7 APIs',c.execute('select count(*) from sys_api where id between 9301 and 9314').fetchone()[0]==14)
 check('12 migration versions',c.execute('select count(*) from sys_migration').fetchone()[0]==12)
 check('No formal review publish or snapshots',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in ['passport_revisions','published_assets','publish_records']) and c.execute("select count(*) from batches where workflow_status!='draft' or submitted_at is not null or current_passport_revision_id is not null").fetchone()[0]==0)
 check('Batches explicitly TEST',c.execute("select count(*) from batches where record_type!='test'").fetchone()[0]==0)
for port in [18099,18100,19530,19531]:
 with socket.socket() as s:s.settimeout(1);check('Local stopped '+str(port),s.connect_ex(('127.0.0.1',port))==errno.ECONNREFUSED)
check('Backend tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin',text=True)=='')
changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui',text=True).splitlines();check('Only two existing UI locale tracked entries',sorted(changes)==['src/lang/en-US/index.ts','src/lang/zh-CN/index.ts'])
for repo in ['go-admin','go-admin-ui']:check(repo+' diff check',subprocess.run(['git','diff','--check'],cwd=R/'admin'/repo,capture_output=True).returncode==0)
(rt/'test-artifacts/final.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS; protected',len(old))
