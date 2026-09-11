from helpers import *
import subprocess
src=rt/'db/passport-admin-t12.db'
def snapshot(p):
 with sqlite3.connect(p) as c:
  tables=[r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
  return {t:hashlib.sha256(json.dumps(sorted(c.execute('select * from "'+t+'"').fetchall(),key=repr),default=str).encode()).hexdigest() for t in tables}
before=snapshot(src)
with (rt/'logs/migrate-repeat.log').open('w') as out:subprocess.run([str(rt/'bin/go-admin'),'migrate','-c',str(rt/'settings.yml')],cwd=R/'admin/go-admin',stdout=out,stderr=subprocess.STDOUT,check=True)
check('Repeat Migration preserves all table rows',snapshot(src)==before)
with sqlite3.connect(src) as c:
 check('16 migrations applied',c.execute('select count(*) from sys_migration').fetchone()[0]==16)
 check('integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)])
 check('foreign_key_check empty',c.execute('pragma foreign_key_check').fetchall()==[])
 backup=rt/'backups/t12-working-backup.db';restored=rt/'db/t12-working-restored.db';started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with sqlite3.connect(backup) as dst:c.backup(dst)
backup.chmod(0o600)
with sqlite3.connect(backup) as srcdb,sqlite3.connect(restored) as dst:srcdb.backup(dst)
restored.chmod(0o600)
check('Working DB consistent backup matches source',snapshot(backup)==before)
check('Independent restored DB all tables match',snapshot(restored)==before)
with sqlite3.connect(restored) as c:
 check('Restored integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)])
 check('Restored FK clean',c.execute('pragma foreign_key_check').fetchall()==[])
(rt/'test-artifacts/migration-backup.json').write_text(json.dumps({'checks':checks,'method':'SQLite online backup API, not live file copy','started_at':started,'backup':str(backup),'backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'restored':str(restored),'table_hashes':before,'limitation':'Working-data checkpoint only; no Published versions yet. Does not satisfy final publication restore Gate.'},indent=2))
