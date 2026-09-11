from pathlib import Path
import sqlite3,subprocess,json,hashlib,re
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t8';checks=[];tables=json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables']
def check(n,v):
 checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
def snap(db,original=False):
 with sqlite3.connect(db) as c:
  return {t:hashlib.sha256(json.dumps(sorted(c.execute('select '+(','.join('"'+x[1]+'"' for x in c.execute('pragma table_info('+t+')') if x[1]!='current_review_record_id') if original else '*')+' from '+t).fetchall(),key=repr)).encode()).hexdigest() for t in tables}
def structure(db):
 with sqlite3.connect(db) as c:return [(kind,name, re.sub(r",CONSTRAINT .*", "",sql) if name=='sys_menu_api_rule' else sql) for kind,name,sql in c.execute("select type,name,sql from sqlite_master where name not like 'sqlite_%' order by type,name").fetchall()]
def migrate(db,name,port=18101):
 cfg=rt/(name+'.yml');cfg.write_text((rt/'settings.yml').read_text().replace('passport-admin-t8.db',db.name).replace('port: 18101','port: '+str(port)));cfg.chmod(0o600)
 with (rt/'logs'/(name+'.log')).open('w') as log:subprocess.run([str(rt/'bin/go-admin'),'migrate','-c',str(cfg)],cwd=R/'admin/go-admin',stdout=log,stderr=subprocess.STDOUT,check=True)
up=rt/'db/upgrade-from-t7.db';fresh=rt/'db/fresh-acceptance.db';service=rt/'db/service-test.db'
# Resume only disposable T8 test DBs after failed attempts.
if up.exists(): up.unlink()
for target in [fresh,service]:
 if target.exists(): target.unlink()
a=sqlite3.connect('file:'+str(R/'runtime/t7/db/passport-admin-t7.db')+'?mode=ro&immutable=1',uri=True);b=sqlite3.connect(up);a.backup(b);a.close();b.close();before=snap(up,True)
migrate(up,'migrate-upgrade');check('T7 upgrade preserves every historical business field',snap(up,True)==before)
with sqlite3.connect(up) as c:
 check('Review pointer initially null',c.execute('select count(*) from batches where current_review_record_id is not null').fetchone()[0]==0)
 check('T8 recorded once',c.execute("select count(*) from sys_migration where version='1789084800000'").fetchone()[0]==1)
 check('Audit freeze retained',c.execute("select count(*) from sqlite_master where type='trigger' and name like 'freeze_passport_audit_events_%'").fetchone()[0]==2)
 check('Upgrade integrity and foreign keys',c.execute('pragma integrity_check').fetchall()==[('ok',)] and c.execute('pragma foreign_key_check').fetchall()==[])
state=structure(up);migrate(up,'migrate-upgrade-repeat');check('Upgrade repeat preserves data/schema',snap(up,True)==before and structure(up)==state)
migrate(fresh,'fresh',18102);check('Fresh schema equals upgrade',structure(fresh)==state)
with sqlite3.connect(fresh) as c:
 check('Fresh business empty',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in tables));check('Thirteen migrations',c.execute('select count(*) from sys_migration').fetchone()[0]==13)
migrate(fresh,'fresh',18102);check('Fresh migration repeat',structure(fresh)==state)
migrate(service,'service');check('Separate service DB from zero',structure(service)==state)
(rt/'test-artifacts/migrations.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS')
