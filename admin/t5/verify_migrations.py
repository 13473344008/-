from pathlib import Path
import sqlite3,subprocess,json,hashlib,datetime
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t5';checks=[];tables=json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables']
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL','time':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 if not v:raise AssertionError(n)
def connect(p):return sqlite3.connect(p)
def snap(db):
 with connect(db) as c:return {t:hashlib.sha256(json.dumps(sorted(c.execute('select * from "'+t+'"').fetchall(),key=repr),ensure_ascii=False).encode()).hexdigest() for t in tables}
def structure(db):
 with connect(db) as c:return c.execute("select type,name,sql from sqlite_master where name not like 'sqlite_%' order by type,name").fetchall()
def migrate(db,name):
 cfg=rt/(name+'.yml');cfg.write_text((rt/'settings.yml').read_text().replace('passport-admin-t5.db',db.name));cfg.chmod(0o600)
 with (rt/'logs'/(name+'.log')).open('w') as log:subprocess.run([str(rt/'bin/go-admin'),'migrate','-c',str(cfg)],cwd=R/'admin/go-admin',stdout=log,stderr=subprocess.STDOUT,check=True)
up=rt/'db/upgrade-from-t4.db';fresh=rt/'db/fresh-acceptance.db'
assert not up.exists() and not fresh.exists(),'Preserve existing migration evidence; use new dedicated paths'
# T4 was stopped. Immutable read-only connection avoids touching its WAL/SHM/evidence.
a=sqlite3.connect('file:'+str(R/'runtime/t4/db/passport-admin-validated.db')+'?mode=ro&immutable=1',uri=True);b=connect(up);a.backup(b);a.close();b.close();before=snap(up)
migrate(up,'migrate-upgrade');check('T4 populated schema upgrades without losing 19-table data',snap(up)==before)
with connect(up) as c:
 check('T5 version recorded once',c.execute("select count(*) from sys_migration where version='1788825600000'").fetchone()[0]==1)
 check('Audit immutability retained after rebuild',c.execute("select count(*) from sqlite_master where type='trigger' and name like 'freeze_passport_audit_events_%'").fetchone()[0]==2)
 check('Upgrade integrity and FK',c.execute('pragma integrity_check').fetchall()==[('ok',)] and c.execute('pragma foreign_key_check').fetchall()==[])
state=structure(up);migrate(up,'migrate-upgrade-repeat');check('Upgrade repeat preserves data and schema',snap(up)==before and structure(up)==state)
# Actual deletion of a dedicated disposable DB, then migration from zero.
c=connect(fresh);c.execute('create table t5_disposable(id integer)');c.close();fresh.unlink();migrate(fresh,'migrate-fresh-acceptance');check('Fresh schema equals upgraded schema',structure(fresh)==state)
with connect(fresh) as c:
 check('Fresh business tables empty',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in tables));check('Fresh all 10 versions recorded',c.execute('select count(*) from sys_migration').fetchone()[0]==10);check('Fresh integrity and FK',c.execute('pragma integrity_check').fetchall()==[('ok',)] and c.execute('pragma foreign_key_check').fetchall()==[])
migrate(fresh,'migrate-fresh-repeat');check('Fresh repeat same schema',structure(fresh)==state)
(rt/'test-artifacts/migration-tests.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(len(checks),'PASS')
