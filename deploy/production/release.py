#!/usr/bin/env python3
"""Validate/build a candidate. Does not start containers or modify proxy services."""
import argparse, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def envfile(path):
    out={}
    for raw in Path(path).read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        k,sep,v=line.partition('=')
        if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*',k) or k in out:raise ValueError('invalid or duplicate environment key')
        out[k]=v
    return out

def validate(e):
    for key in ['ADMIN_PROJECT','PUBLIC_PROJECT','PUBLIC_UPSTREAM','PROXY_NETWORK']:
        if not re.fullmatch(r'[a-z][a-z0-9_-]{2,62}',e.get(key,'')):raise ValueError(f'{key} requires an inspected explicit value')
    if e['ADMIN_PROJECT']==e['PUBLIC_PROJECT'] or any(x in ('proxy','directus','caddy') for x in [e['ADMIN_PROJECT'],e['PUBLIC_PROJECT']]):raise ValueError('projects must be independent')
    for key in ['ADMIN_ROOT','PUBLIC_ROOT']:
        p=Path(e.get(key,''))
        if not p.is_absolute() or '..' in p.parts or str(p) in ('/','/opt') or p.is_relative_to('/opt/proxy'):raise ValueError('unsafe deployment root')
    a,p=Path(e['ADMIN_ROOT']),Path(e['PUBLIC_ROOT'])
    if a==p or a.is_relative_to(p) or p.is_relative_to(a):raise ValueError('roots must be separate')
    if not e.get('ADMIN_PORT','').isdigit() or not 1024<=int(e['ADMIN_PORT'])<=65535:raise ValueError('invalid loopback port')
    for key in ['GO_IMAGE','NODE_IMAGE','RUNTIME_IMAGE','NGINX_IMAGE']:
        if not re.fullmatch(r'[a-z0-9./:_-]+@sha256:[a-f0-9]{64}',e.get(key,'')):raise ValueError(f'{key} must be digest-pinned')
    for key in ['BACKEND_IMAGE','ADMIN_IMAGE']:
        if not re.fullmatch(r'[a-z0-9./:_-]+',e.get(key,'')) or 'latest' in e[key]:raise ValueError('use an explicit release image tag')
    if e.get('PUBLIC_BASE_URL') not in ['https://id.potahub.com','https://id-test.potahub.com']:raise ValueError('use an approved public origin')
    return e

def run(cmd,env):
    subprocess.run(cmd,check=True,cwd=ROOT,env={**os.environ,**env})

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['validate','build']);p.add_argument('--env',required=True);p.add_argument('--platform',choices=['linux/amd64','linux/arm64']);p.add_argument('--manifest')
    args=p.parse_args();e=validate(envfile(args.env))
    if not shutil.which('docker'):raise SystemExit('Docker is required for actual Compose/image validation; nothing deployed')
    for f in ['compose.admin.yml','compose.public.yml']:
        run(['docker','compose','--env-file',str(Path(args.env).resolve()),'-f',str(ROOT/'deploy/production'/f),'config','--quiet'],e)
    if args.action=='build':
        if not args.platform or not args.manifest:raise SystemExit('build requires verified target --platform and a new --manifest path')
        manifest=Path(args.manifest)
        if manifest.exists():raise SystemExit('refusing to overwrite release manifest')
        for f,key in [('Dockerfile.backend','BACKEND_IMAGE'),('Dockerfile.web','ADMIN_IMAGE')]:
            cmd=['docker','build','--platform',args.platform,'--file',str(ROOT/'deploy/production'/f),'--tag',e[key]]
            for name in ['GO_IMAGE','NODE_IMAGE','RUNTIME_IMAGE','NGINX_IMAGE','PUBLIC_BASE_URL']:
                arg='PUBLIC_BASE_URL' if name=='PUBLIC_BASE_URL' else name
                cmd+=['--build-arg',f'{arg}={e[name]}']
            cmd+=['.'];run(cmd,e)
        ids={k:subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',e[k]],text=True).strip() for k in ['BACKEND_IMAGE','ADMIN_IMAGE']}
        files={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for base in ['deploy/production','public-site'] for f in (ROOT/base).rglob('*') if f.is_file() and '__pycache__' not in f.parts}
        manifest.write_text(json.dumps({'platform':args.platform,'base_images':{k:e[k] for k in ['GO_IMAGE','NODE_IMAGE','RUNTIME_IMAGE','NGINX_IMAGE']},'image_ids':ids,'files':files,'deployed':False},indent=2))
    print('Candidate validation finished; no containers started.')
if __name__=='__main__':main()
