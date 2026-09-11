from pathlib import Path
import json,hashlib,sqlite3,socket,subprocess,datetime,uuid
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t5';checks=[]
def check(name,v):
 checks.append({'name':name,'status':'PASS' if v else 'FAIL','time':datetime.datetime.now(datetime.timezone.utc).isoformat()});assert v,name
b=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];check('Original 53 baseline hashes unchanged',len(b)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items()));check('All 7 site files unchanged',sum(p.startswith('site/') for p in b)==7 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in b.items() if p.startswith('site/')))
old=json.loads((rt/'test-artifacts/t4-before.json').read_text());check('T4 protected runtime evidence and migrations unchanged',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in old.items()))
for repo,sha in [('go-admin','595c4a6be5b1aade8dc30fe2b90ea13dfba61b05'),('go-admin-ui','e106f68d362d3a7aaa43244eb74cede1a83f4da5')]:check(repo+' commit remains locked',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'admin'/repo,text=True).strip()==sha)
with sqlite3.connect(rt/'db/passport-admin-t5.db') as c:
 check('Final integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check('Final foreign_key_check empty',c.execute('pragma foreign_key_check').fetchall()==[])
 for table,cols in [('products','product_code'),('product_revisions','product_id,revision_number'),('product_revision_translations','product_revision_id,language_code')]:check('No duplicate keys '+table,len(c.execute('select '+cols+',count(*) from '+table+' group by '+cols+' having count(*)>1').fetchall())==0)
 check('No Batch or Passport development data',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in ['batches','passport_revisions','published_assets','publish_records','inspection_items']))
 check('12 business APIs registered',c.execute("select count(*) from sys_api where path like '/api/v1/passport-products%'").fetchone()[0]==12)
with sqlite3.connect(rt/'db/passport-admin-t5.db') as c:
 c.execute('PRAGMA foreign_keys=ON');cols=[x[1] for x in c.execute('pragma table_info(product_revision_translations)')];row=list(c.execute("select t.* from product_revision_translations t join product_revisions r on r.id=t.product_revision_id where r.revision_status='draft' limit 1").fetchone());row[cols.index('id')]=str(uuid.uuid4());c.execute('SAVEPOINT duplicate_check');ok=False
 try:c.execute('insert into product_revision_translations('+','.join(cols)+') values('+','.join('?' for _ in cols)+')',row)
 except sqlite3.IntegrityError as e:ok='UNIQUE constraint failed: product_revision_translations.product_revision_id, product_revision_translations.language_code' in str(e)
 finally:c.execute('ROLLBACK TO duplicate_check');c.execute('RELEASE duplicate_check')
 check('Direct SQL duplicate language rejected on draft revision',ok)
for port in [18095,18096,19528]:
 with socket.socket() as s:s.settimeout(1);check('T5 service stopped '+str(port),s.connect_ex(('127.0.0.1',port))!=0)
check('Backend tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin',text=True)=='')
ui_changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui',text=True).splitlines();check('Only two UI locale entrypoints modified',sorted(ui_changes)==['src/lang/en-US/index.ts','src/lang/zh-CN/index.ts'])
for p in (rt/'db').glob('*.db'):p.chmod(0o600)
(rt/'test-artifacts/final-tests.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'PASS')
