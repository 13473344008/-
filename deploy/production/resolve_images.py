#!/usr/bin/env python3
"""Read official Docker Hub manifests and record digest pins; no daemon or deployment."""
import argparse, hashlib, json, urllib.request, urllib.parse
from pathlib import Path
IMAGES={'GO_IMAGE':('golang','1.26.5-bookworm'),'NODE_IMAGE':('node','24.18.0-bookworm-slim'),'RUNTIME_IMAGE':('debian','bookworm-slim'),'NGINX_IMAGE':('nginx','1.30.4-alpine')}
def resolve(repo,tag):
    query=urllib.parse.urlencode({'service':'registry.docker.io','scope':f'repository:library/{repo}:pull'})
    with urllib.request.urlopen('https://auth.docker.io/token?'+query,timeout=20) as r:token=json.load(r)['token']
    request=urllib.request.Request(f'https://registry-1.docker.io/v2/library/{repo}/manifests/{tag}',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json'})
    with urllib.request.urlopen(request,timeout=30) as r:
        raw=r.read();digest=r.headers['Docker-Content-Digest']
    if digest!='sha256:'+hashlib.sha256(raw).hexdigest():raise ValueError('registry digest mismatch')
    doc=json.loads(raw);platforms={m.get('platform',{}).get('architecture') for m in doc.get('manifests',[]) if m.get('platform',{}).get('os')=='linux'}
    if not {'amd64','arm64'}<=platforms:raise ValueError('required target platforms missing')
    return {'tag':f'{repo}:{tag}','image':f'{repo}@{digest}','platforms':sorted(platforms)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
    if out.exists():raise SystemExit('refusing to overwrite image lock')
    images={key:resolve(*value) for key,value in IMAGES.items()}
    out.write_text(json.dumps(images,indent=2));print('Resolved official image digests:',', '.join(images))
