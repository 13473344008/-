import sqlite3,json,hashlib,subprocess,sys,socket
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t4';c=sqlite3.connect(rt/'db/passport-admin-validated.db');checks=[]
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL'})
 if not v:raise AssertionError(n)
baseline=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];changed=[p for p,h in baseline.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('All 53 frozen baseline hashes match',len(baseline)==53 and not changed);check('All 7 site baseline hashes match',sum(p.startswith('site/') for p in baseline)==7 and not any(p.startswith('site/') for p in changed))
cat=json.loads((R/'admin/t4/schema_catalog.json').read_text());check('All 19 table column lists match T3 catalog',all([x[1] for x in c.execute('pragma table_info('+t+')')]==cols for t,cols in cat['tables'].items()))
check('Final main integrity_check',c.execute('pragma integrity_check').fetchall()==[('ok',)]);check('Final main foreign_key_check',c.execute('pragma foreign_key_check').fetchall()==[])
check('Backend upstream tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin')==b'');check('UI upstream tracked files unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui')==b'')
for port in [18094,19527]:
 with socket.socket() as s:s.settimeout(1);check('Local service stopped port '+str(port),s.connect_ex(('127.0.0.1',port))!=0)
versions=[x[0] for x in c.execute('select version from sys_migration order by version')];system=[x[0] for x in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'") if x[0] not in cat['tables']];data={'checks':checks,'baseline_count':len(baseline),'changed_baseline':changed,'business_tables':19,'business_columns':sum(map(len,cat['tables'].values())),'triggers':c.execute("select count(*) from sqlite_master where type='trigger'").fetchone()[0],'migration_versions':versions,'system_tables':system,'python_sqlite':sqlite3.sqlite_version,'python':sys.version.split()[0]};(rt/'evidence/final-tests.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
