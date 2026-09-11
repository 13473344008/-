"""Consistent SQLite Backup API and isolated restore; never copies live db bytes."""
import sqlite3,json,hashlib,datetime,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t4';db=rt/'db/passport-admin-validated.db';backup=rt/'backups/t4-consistent.db';restore=rt/'db/restored.db';ev=rt/'evidence/backup-restore.json'
def connect(p):
 c=sqlite3.connect(p);c.execute('PRAGMA foreign_keys=ON');return c
def snapshot(c):
 out={}
 for (t,) in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"):
  rows=c.execute('SELECT * FROM "'+t+'"').fetchall();raw=json.dumps(sorted(rows,key=repr),ensure_ascii=False,default=str);out[t]={'rows':len(rows),'logical_sha256':hashlib.sha256(raw.encode()).hexdigest()}
 return out
if sys.argv[1]=='backup':
 if backup.exists():raise RuntimeError('Refuse overwrite evidence backup')
 c=connect(db);b=connect(backup);c.backup(b);snap=snapshot(b);b.close();data={'method':'Python sqlite3.Connection.backup SQLite Backup API','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backup_file':str(backup),'backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'snapshot':snap,'checks':[]};data['checks'].append({'name':'Consistent backup created','status':'PASS'})
 c.execute("update sys_user set remark='T4 AFTER BACKUP MUTATION' where username='t4-reader'");c.commit();assert snapshot(c)['sys_user']!=snap['sys_user'];c.close();data['checks'].append({'name':'Original changed after backup','status':'PASS'});ev.write_text(json.dumps(data,indent=2))
else:
 data=json.loads(ev.read_text());assert not restore.exists();b=connect(backup);r=connect(restore);b.backup(r);b.close();same=snapshot(r)==data['snapshot'];assert same;data['checks'].append({'name':'Restore all table rows and logical hashes match backup','status':'PASS'});assert r.execute('pragma integrity_check').fetchall()==[('ok',)];assert r.execute('pragma foreign_key_check').fetchall()==[];data['checks'] += [{'name':'Restore integrity_check','status':'PASS'},{'name':'Restore foreign_key_check','status':'PASS'}];data['restore_file']=str(restore);r.close();ev.write_text(json.dumps(data,indent=2))
print(sys.argv[1], 'PASS')
