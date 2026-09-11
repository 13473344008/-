#!/usr/bin/env python3
"""Consistent offline bundle. Stop ONLY this project's backend before running.
Restore always targets a NEW directory. Never changes current deployment pointers.
"""
import argparse, hashlib, json, os, shutil, sqlite3
from pathlib import Path

def regular_tree(root):
    for p in root.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise ValueError('symlink or special file in bundle')

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def inspect_db(path):
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
        if c.execute('pragma integrity_check').fetchone()[0]!='ok' or c.execute('pragma foreign_key_check').fetchall():
            raise ValueError('database integrity failure')
        if c.execute('select count(*) from batches where active_publish_record_id is not null').fetchone()[0]:
            raise ValueError('unresolved publication: reconcile before backup')
        heads=c.execute('select b.batch_code,p.version_number,p.payload_hash from batches b join passport_revisions p on p.id=b.current_passport_revision_id').fetchall()
        return heads

def verify(root):
    root=root.resolve();regular_tree(root)
    manifest=json.loads((root/'manifest.json').read_text())
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}
    if actual!=set(manifest['files']):raise ValueError('backup file set mismatch')
    for name,want in manifest['files'].items():
        p=root/name
        if not p.resolve().is_relative_to(root) or digest(p)!=want:raise ValueError('backup hash mismatch')
    heads=inspect_db(root/'database.db')
    for code,version,want in heads:
        for p in [root/'published'/'published'/f'{code}.json',root/'published'/'versions'/code/f'v{version}.json']:
            if digest(p)!=want:raise ValueError('database/public current mismatch')
        payload=json.loads((root/'published'/'published'/f'{code}.json').read_text())
        for asset in payload['assets']:
            p=root/'published'/asset['path']
            if not p.resolve().is_relative_to(root/'published') or digest(p)!=asset['sha256']:raise ValueError('asset mismatch')
    with sqlite3.connect((root/'database.db').as_uri()+'?mode=ro',uri=True) as c:
        versions=c.execute('select id,snapshot_path,payload_hash,release_identifier from passport_revisions where published_at is not null').fetchall()
    for revision_id,snapshot,want,release_id in versions:
        p=root/'published'/snapshot
        if not p.resolve().is_relative_to(root/'published') or digest(p)!=want:raise ValueError('historical snapshot mismatch')
        private=json.loads((root/'work'/'manifests'/f'{release_id}.json').read_text())
        if private.get('payload_hash')!=want or private.get('passport_revision_id')!=revision_id:raise ValueError('private manifest mismatch')
        for asset in json.loads(p.read_text())['assets']:
            p=root/'published'/asset['path']
            if not p.resolve().is_relative_to(root/'published') or digest(p)!=asset['sha256']:raise ValueError('historical asset mismatch')
    return len(heads)

def backup(db,media,work,published,out,offline):
    if not offline:raise ValueError('backend must be stopped; pass --offline-confirmed after checking exact Compose service')
    sources=[Path(x).absolute() for x in [db,media,work,published]];out=Path(out).absolute()
    if any(out==p or out.is_relative_to(p) or p.is_relative_to(out) for p in sources):raise ValueError('backup destination must be separate')
    if not sources[0].is_file() or any(not p.is_dir() for p in sources[1:]):raise ValueError('missing source')
    for p in sources:
        if p.is_symlink():raise ValueError('symlink source')
    inspect_db(sources[0]);out.mkdir(mode=0o700,exist_ok=False);os.chmod(out,0o700)
    with sqlite3.connect(sources[0].as_uri()+'?mode=rw',uri=True) as guard:
        guard.execute('BEGIN IMMEDIATE')
        with sqlite3.connect(sources[0].as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(out/'database.db') as dest:
            src.backup(dest)
            dest.execute('PRAGMA journal_mode=DELETE')
        for p,name in zip(sources[1:],['media','work','published']):
            regular_tree(p);shutil.copytree(p,out/name)
        guard.rollback()
    manifest={'format':1,'files':{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));verify(out)
    return out

def restore(source,out):
    source=Path(source).absolute();out=Path(out).absolute();verify(source)
    if out==source or out.is_relative_to(source):raise ValueError('restore target must be separate')
    shutil.copytree(source,out);os.chmod(out,0o700);verify(out);return out

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('backup')
    for k in ['db','media','work','published','out']:b.add_argument('--'+k,required=True)
    b.add_argument('--offline-confirmed',action='store_true')
    v=sub.add_parser('verify');v.add_argument('--source',required=True)
    r=sub.add_parser('restore');r.add_argument('--source',required=True);r.add_argument('--out',required=True)
    a=vars(p.parse_args());command=a.pop('command')
    if command=='verify':print('Verified current heads:',verify(Path(a['source'])))
    elif command=='backup':a['offline']=a.pop('offline_confirmed');print('Created:',backup(**a))
    else:print('Restored into new directory:',restore(**a))
