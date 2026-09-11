from pathlib import Path
import secrets,json,os
root=Path(__file__).resolve().parents[2];rt=root/'runtime/t4'
s=(root/'admin/go-admin/config/settings.yml').read_text()
s=s.replace('host: 0.0.0.0','host: 127.0.0.1').replace('port: 8000','port: 18094').replace('enabledp: false','enabledp: true').replace('path: temp/logs',f'path: {rt}/logs/backend').replace('level: trace','level: warn').replace('secret: go-admin','secret: '+secrets.token_hex(32)).replace('driver: mysql','driver: sqlite3').replace('source: user:password@tcp(127.0.0.1:3306)/dbname?charset=utf8&parseTime=True&loc=Local&timeout=1000ms',f'source: file:{rt}/db/passport-admin-validated.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL').replace('maxIdleConns: 20','maxIdleConns: 1').replace('maxOpenConns: 100','maxOpenConns: 1').replace('enableddb: false','enableddb: true')
# Avoid configured redis locker requiring an unrelated service.
s=s[:s.index('  locker:')]
p=rt/'settings.yml';p.write_text(s);p.chmod(0o600)
cred=rt/'credentials.json'
if not cred.exists():cred.write_text(json.dumps({'admin_username':'admin','admin_password':secrets.token_urlsafe(24),'test_username':'t4-reader','test_password':secrets.token_urlsafe(24)},indent=2));cred.chmod(0o600)
ui=root/'admin/go-admin-ui/.env.development.local';ui.write_text("VUE_APP_BASE_API='http://127.0.0.1:18094'\nVUE_APP_GA_ID=''\n")
print('Private local config created; backend 127.0.0.1:18094, UI planned 127.0.0.1:19527')
