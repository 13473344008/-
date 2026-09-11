import json,sqlite3,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t4';db=rt/'db/fresh-rebuild.db';cfg=rt/'settings-fresh.yml';base=rt/'db/passport-admin-validated.db';checks=[]
assert not db.exists(),'Refuse unexpected existing fresh test database'
def migration(label):
 with (rt/'logs'/f'{label}.log').open('w') as f:subprocess.run([str(rt/'bin/go-admin-t4'),'migrate','-c',str(cfg)],cwd=R/'admin/go-admin',stdout=f,stderr=subprocess.STDOUT,check=True)
def state(p):
 with sqlite3.connect(p) as c:return {'schema':c.execute("select type,name,sql from sqlite_master where name not like 'sqlite_%' order by type,name").fetchall(),'versions':c.execute('select version from sys_migration order by version').fetchall(),'integrity':c.execute('pragma integrity_check').fetchall(),'fk':c.execute('pragma foreign_key_check').fetchall()}
cfg.write_text((rt/'settings.yml').read_text().replace(str(base),str(db)));cfg.chmod(0o600)
# Create then delete exactly this dedicated temporary DB, never the populated runtime DB.
c=sqlite3.connect(db);c.execute('create table t4_disposable(x integer)');c.commit();c.close();db.unlink();checks.append({'name':'Dedicated disposable fresh DB removed','status':'PASS'})
migration('fresh-first');a=state(db);b=state(base);assert a['schema']==b['schema'];assert a['versions']==b['versions'];checks.append({'name':'Fresh all migrations same 19 business and system schema','status':'PASS'})
migration('fresh-repeat');assert state(db)==a;checks.append({'name':'Repeat migration schema and versions unchanged','status':'PASS'})
assert a['integrity']==[('ok',)] and a['fk']==[];checks.append({'name':'Fresh integrity and foreign keys','status':'PASS'})
(rt/'evidence/fresh-tests.json').write_text(json.dumps({'checks':checks,'versions':a['versions'],'schema_object_count':len(a['schema'])},indent=2));print(checks)
