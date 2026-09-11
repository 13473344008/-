#!/usr/bin/env python3
"""Rebuild repaired images only. Never changes deployment files or initializes a DB."""
import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--env', required=True)
    p.add_argument('--builder', default='product-id-build-cd8641f')
    args = p.parse_args()
    os.umask(0o077)
    os.chdir(ROOT)
    envpath = Path(args.env).resolve()
    m = runpy.run_path(str(ROOT / 'deploy/production/release.py'))
    e = m['validate'](m['envfile'](envpath))
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
        raise SystemExit('Source has local changes; refusing ambiguous build')
    node = 'buildx_buildkit_' + args.builder + '0'
    obj = json.loads(subprocess.check_output(['docker', 'inspect', '--type', 'container', node], text=True))[0]
    h = obj['HostConfig']
    if not obj['State']['Running'] or (h['Memory'], h['MemorySwap'], h['CpuPeriod'], h['CpuQuota'], h['NetworkMode']) != (1610612736, 1610612736, 100000, 100000, 'bridge'):
        raise SystemExit('Expected running restricted builder not found')
    out = Path(tempfile.mkdtemp(prefix='permissions-build.', dir=envpath.parent))
    print('BUILD_DIR=' + str(out), flush=True)
    images = {}
    jobs = [('backend', 'BACKEND_IMAGE', ['GO_IMAGE', 'RUNTIME_IMAGE']), ('web', 'ADMIN_IMAGE', ['NODE_IMAGE', 'NGINX_IMAGE', 'PUBLIC_BASE_URL'])]
    for kind, key, names in jobs:
        tag = e[key] + '-fix' + revision[:7]
        cmd = ['docker', 'buildx', 'build', '--builder', args.builder, '--platform', 'linux/amd64', '--load', '--progress', 'plain', '-f', str(ROOT / 'deploy/production' / ('Dockerfile.' + kind)), '-t', tag, '--metadata-file', str(out / (kind + '-metadata.json'))]
        for name in names:
            cmd += ['--build-arg', name + '=' + e[name]]
        print('BUILDING=' + tag, flush=True)
        with (out / (kind + '.log')).open('x') as log:
            proc = subprocess.Popen(cmd + ['.'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            result = proc.wait()
        if result:
            raise SystemExit('Build failed; preserve logs in ' + str(out))
        info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', tag], text=True))[0]
        if (info['Os'], info['Architecture'], info['Config']['User']) != ('linux', 'amd64', '10001:10001'):
            raise SystemExit('Unexpected image platform/runtime user')
        images[key] = {'tag': tag, 'id': info['Id']}
        print('IMAGE_OK=' + tag + ' ' + info['Id'], flush=True)
    fixed = dict(e)
    for key in images:
        fixed[key] = images[key]['id']
    fixedpath = out / 'release.env'
    with fixedpath.open('x') as f:
        f.write(''.join(k + '=' + v + '\n' for k, v in fixed.items()))
    (out / 'manifest.json').write_text(json.dumps({'source_commit': revision, 'builder': args.builder, 'buildkit_image_id': obj['Image'], 'images': images, 'original_env': str(envpath), 'deployed': False}, indent=2) + '\n')
    print('FIXED_ENV=' + str(fixedpath), flush=True)
    print('IMAGES_OK; existing database and credentials untouched', flush=True)

if __name__ == '__main__':
    main()
