from helpers import *
import subprocess
source=R/'runtime/t12/db/passport-admin-t12.db';target=rt/'db/t12-historical-upgrade-copy.db'
def rows(p):
 with sqlite3.connect(p) as c:
  c.text_factory=lambda b:b.decode('utf-8','surrogateescape')
  return {t:hashlib.sha256(json.dumps(sorted(c.execute('select * from "'+t+'"').fetchall(),key=repr),default=str).encode()).hexdigest() for (t,) in c.execute("select name from sqlite_master where type='table'") if t not in ['sqlite_sequence','sys_migration','sys_menu','sys_api','sys_menu_api_rule','sys_role_menu','casbin_rule']}
try:
 before=rows(source)
 with sqlite3.connect(source) as src,sqlite3.connect(target) as dst:src.backup(dst)
 target.chmod(0o600);config=rt/'upgrade-settings.yml';config.write_text((rt/'settings.yml').read_text().replace(str(rt/'db/passport-admin-t12-fix.db'),str(target)));config.chmod(0o600)
 with (rt/'logs/historical-upgrade.log').open('w') as out:subprocess.run([str(rt/'bin/go-admin'),'migrate','-c',str(config)],cwd=R/'admin/go-admin',stdout=out,stderr=subprocess.STDOUT,check=True)
 check('Historical T12 copy upgrade preserves business table hashes',rows(target)==before);check('Original T12 database unchanged',rows(source)==before)
 with sqlite3.connect(target) as c:check('Upgrade applies 17 migrations',c.execute('select count(*) from sys_migration').fetchone()[0]==17);check('Upgrade integrity FK clean',c.execute('pragma integrity_check').fetchone()[0]=='ok' and not c.execute('pragma foreign_key_check').fetchall())
finally:(rt/'test-artifacts/upgrade-check.json').write_text(json.dumps(checks,indent=2))
