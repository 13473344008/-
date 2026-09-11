from pathlib import Path
import secrets,json
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t10';rt.chmod(0o700)
p=rt/'settings.yml'
if not p.exists():
 s=(r/'admin/go-admin/config/settings.yml').read_text().replace('host: 0.0.0.0','host: 127.0.0.1').replace('port: 8000','port: 18105').replace('enabledp: false','enabledp: true').replace('path: temp/logs','path: '+str(rt/'logs/backend')).replace('level: trace','level: warn').replace('secret: go-admin','secret: '+secrets.token_hex(32)).replace('driver: mysql','driver: sqlite3').replace('source: user:password@tcp(127.0.0.1:3306)/dbname?charset=utf8&parseTime=True&loc=Local&timeout=1000ms',f'source: file:{rt}/db/passport-admin-t10.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL').replace('maxIdleConns: 20','maxIdleConns: 1').replace('maxOpenConns: 100','maxOpenConns: 1').replace('enableddb: false','enableddb: true');s=s[:s.index('  locker:')];p.write_text(s);p.chmod(0o600)
p=rt/'credentials.json'
if not p.exists():p.write_text(json.dumps({'admin_username':'admin','admin_password':secrets.token_urlsafe(24),'test_username':'t10-no-access','test_password':secrets.token_urlsafe(24)}));p.chmod(0o600)
# Separate Vite mode avoids overwriting T4's development config.
(r/'admin/go-admin-ui/.env.t10.local').write_text("VUE_APP_BASE_API='http://127.0.0.1:18105'\nVUE_APP_GA_ID=''\n")
