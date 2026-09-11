from pathlib import Path
import sqlite3,json,hashlib,datetime,shutil
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t12-fix';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
def snapshot(p):
 with sqlite3.connect(p) as c:
  c.text_factory=lambda b:b.decode('utf-8','surrogateescape')
  tables=[x[0] for x in c.execute("select name from sqlite_master where type='table' order by name")]
  return {t:{'rows':c.execute('select count(*) from "'+t+'"').fetchone()[0],'sha256':hashlib.sha256(json.dumps(sorted(c.execute('select * from "'+t+'"').fetchall(),key=repr),default=str).encode()).hexdigest()} for t in tables}
def hashes(p):return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file()}
started=datetime.datetime.now(datetime.timezone.utc).isoformat();source=rt/'db/passport-admin-t12-fix.db';backup=rt/'backups/t12-fix-final.db';restored=rt/'db/restored.db';before=snapshot(source)
with sqlite3.connect(source) as src,sqlite3.connect(backup) as dst:src.backup(dst)
with sqlite3.connect(backup) as src,sqlite3.connect(restored) as dst:src.backup(dst)
for p in [backup,restored]:p.chmod(0o600)
check('Final DB Backup all tables identical',snapshot(backup)==before);check('Independent restored.db all tables identical',snapshot(restored)==before)
with sqlite3.connect(restored) as c:check('Restore integrity and FK',c.execute('pragma integrity_check').fetchall()==[('ok',)] and c.execute('pragma foreign_key_check').fetchall()==[])
for name,src in [('publish',rt/'publish'),('private-releases',rt/'releases'),('private-media',rt/'private-media'),('public-site',R/'public-site')]:
 dest=rt/'backups'/('final-'+name);shutil.copytree(src,dest);check('Backup bytes '+name,hashes(src)==hashes(dest))
 if True:
  restore=rt/'backups'/('restored-'+name);shutil.copytree(dest,restore);check('Restored bytes '+name,hashes(src)==hashes(restore))
conf=(rt/'nginx/nginx.conf').read_text().replace(str(rt/'publish'),str(rt/'backups/restored-publish')).replace(str(R/'public-site'),str(rt/'backups/restored-public-site'));(rt/'nginx/restored.conf').write_text(conf)
(rt/'test-artifacts/backup-restore.json').write_text(json.dumps({'checks':checks,'method':'SQLite online backup API; services stopped and no writer; all table row hashes compared','started_at':started,'backup':str(backup),'backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'restored':str(restored),'tables':before,'static_files':hashes(rt/'backups/final-publish'),'private_manifests':hashes(rt/'backups/final-private-releases'),'asset_count':sum(1 for p in (rt/'publish/assets').rglob('*.png')),'private_media':hashes(rt/'backups/final-private-media')},indent=2))
