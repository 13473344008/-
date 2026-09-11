from pathlib import Path
import sqlite3,subprocess,json,hashlib,re,os
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t10';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
source=R/'runtime/t9/db/passport-admin-t9.db';up=rt/'db/upgrade-from-t9.db';fresh=rt/'fresh/db/fresh-acceptance.db';service=rt/'db/service-test.db'
for d in ['db','logs','publish','releases','private-media','test-artifacts']: (rt/'fresh'/d).mkdir(parents=True,exist_ok=True)
(rt/'fresh/credentials.json').write_bytes((rt/'credentials.json').read_bytes());(rt/'fresh/credentials.json').chmod(0o600)
with sqlite3.connect('file:'+str(source)+'?mode=ro&immutable=1',uri=True) as src:
 tables=[r[0] for r in src.execute("select name from sqlite_master where type='table' and name in ('products','product_revisions','product_revision_translations','batches','review_records','passport_revisions','publish_records','published_assets','passport_audit_events','asset_links','media_assets','custom_sections','custom_section_translations','batch_overrides','batch_override_translations','inspection_items','inspection_item_translations','certifications','certification_translations','certification_links')")]
 columns={t:[r[1] for r in src.execute('pragma table_info('+t+')')] for t in tables}
 with sqlite3.connect(up) as dst:src.backup(dst)
def snap(db):
 with sqlite3.connect(db) as c:return {t:hashlib.sha256(json.dumps(sorted(c.execute('select '+','.join('"'+k+'"' for k in columns[t])+' from '+t).fetchall(),key=repr)).encode()).hexdigest() for t in tables}
def canonical_sql(sql):
 if sql and ',CONSTRAINT ' in sql:
  parts=sql[:-1].split(',CONSTRAINT ');return parts[0]+',CONSTRAINT '+',CONSTRAINT '.join(sorted(parts[1:]))+')'
 return sql
def structure(db):
 with sqlite3.connect(db) as c:return [(k,n,canonical_sql(sql)) for k,n,sql in c.execute("select type,name,sql from sqlite_master where name not like 'sqlite_%' order by type,name")]
def migrate(db,name,port=18105):
 cfg=rt/(name+'.yml');cfg.write_text((rt/'settings.yml').read_text().replace(str(rt/'db/passport-admin-t10.db'),str(db)).replace('port: 18105','port: '+str(port)));cfg.chmod(0o600)
 with (rt/'logs'/('migration-'+name+'.log')).open('w') as out:subprocess.run([str(rt/'bin/go-admin'),'migrate','-c',str(cfg)],cwd=R/'admin/go-admin',stdout=out,stderr=subprocess.STDOUT,check=True)
 return cfg
before=snap(up);migrate(up,'upgrade');check('T9 all original business columns preserved',snap(up)==before);state=structure(up);migrate(up,'upgrade-repeat');check('Upgrade repeated safe',structure(up)==state and snap(up)==before)
cfg=migrate(fresh,'fresh',18106);check('Fresh equals upgrade schema',structure(fresh)==state);migrate(fresh,'fresh-repeat',18106);check('Fresh repeat schema stable',structure(fresh)==state)
with sqlite3.connect(fresh) as c:check('Fresh has fifteen migrations',c.execute('select count(*) from sys_migration').fetchone()[0]==15);check('Fresh business starts empty',all(c.execute('select count(*) from '+t).fetchone()[0]==0 for t in tables))
migrate(service,'service');check('Service DB starts from zero',structure(service)==state)
for dbpath in [up,fresh,service]:
 with sqlite3.connect(dbpath) as c:check(dbpath.name+' integrity and FK',c.execute('pragma integrity_check').fetchall()==[('ok',)] and c.execute('pragma foreign_key_check').fetchall()==[])
(rt/'test-artifacts/migrations.json').write_text(json.dumps(checks,indent=2));print(len(checks),'PASS')
