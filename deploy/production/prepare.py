#!/usr/bin/env python3
"""Create a NEW private configuration bundle; never overwrite a deployment."""
import argparse, json, os, secrets
from pathlib import Path
from urllib.parse import urlsplit

def prepare(destination, public_base):
    u = urlsplit(public_base)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('public base must be an HTTPS origin')
    destination = Path(destination).absolute()
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    os.chmod(destination, 0o700)
    for name in ('config', 'db', 'media', 'logs', 'geo', 'published', 'work'):
        (destination/name).mkdir(mode=0o700)
    secret = secrets.token_hex(32)
    config = f'''settings:
  application:
    mode: prod
    host: 0.0.0.0
    name: passport-admin
    port: 8000
    readtimeout: 60
    writertimeout: 120
    enabledp: true
  logger:
    path: /data/logs
    stdout: default
    level: warn
    enableddb: false
  jwt:
    secret: {secret}
    timeout: 3600
  database:
    driver: sqlite3
    source: file:/data/db/passport.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL
    maxIdleConns: 1
    maxOpenConns: 1
    connMaxIdleTime: 300
    connMaxLifeTime: 3600
  gen:
    dbname: passport
    frontpath: /nonexistent
'''
    for name, value in [('settings.yml', config), ('admin-password', secrets.token_urlsafe(24)+'\n')]:
        p=destination/'config'/name
        fd=os.open(p, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as f:f.write(value)
    (destination/'bundle.json').write_text(json.dumps({'public_base':public_base.rstrip('/'),'mode':'prod','generated':True,'deployed':False},indent=2))
    return destination

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);p.add_argument('--public-base',required=True)
    args=p.parse_args();out=prepare(args.destination,args.public_base)
    print(f'Private configuration generated in {out}; passwords were not printed. No services started.')
