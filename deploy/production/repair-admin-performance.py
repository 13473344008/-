#!/usr/bin/env python3
"""Apply a backed-up config-only optimization to the existing isolated test admin."""
import argparse
import hashlib
import json
import os
import re
import gzip
from pathlib import Path
import runpy
import subprocess
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
PROJECT = 'passport-admin-test'
ROOT = Path('/opt/passport-admin-test')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    env_path = Path(args.env).resolve(strict=True)
    release = runpy.run_path(str(HERE / 'release.py'))
    values = release['validate'](release['envfile'](env_path))
    for key, expected in {'ADMIN_PROJECT': PROJECT, 'ADMIN_ROOT': str(ROOT), 'ADMIN_PORT': '18080',
                          'PUBLIC_ROOT': '/opt/product-id-test'}.items():
        if values.get(key) != expected:
            raise RuntimeError('Unexpected test target: ' + key)
    environment = {**os.environ, **values}

    def run(cmd, capture=False):
        return subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL, env=environment,
                              text=True, stdout=subprocess.PIPE if capture else None).stdout

    target = ROOT / 'docker-compose.yml'
    if target.resolve() != target:
        raise RuntimeError('Unexpected Compose symlink')
    old = target.read_text()
    # Accept precisely the reviewed two-network template, without local additions.
    if old != (HERE / 'compose.admin.yml').read_text():
        raise RuntimeError('Installed Compose differs from the reviewed template; no changes made')
    config = ROOT / 'nginx-performance.conf'
    if config.is_symlink() or (config.exists() and config.read_bytes() != (HERE / 'nginx-admin.conf').read_bytes()):
        raise RuntimeError('A different performance config exists; inspect the previous attempt')
    anchor = '    networks: [admin_private, admin_access]\n'
    if old.count(anchor) != 1:
        raise RuntimeError('Unexpected management network configuration')
    new = old.replace(anchor, anchor + '''    volumes:
      - type: bind
        source: ${ADMIN_ROOT:?}/nginx-performance.conf
        target: /etc/nginx/nginx.conf
        read_only: true
        bind: {create_host_path: false}
''')

    def compose(file, *args):
        return ['docker', 'compose', '--env-file', str(env_path), '-f', str(file), '-p', PROJECT, *args]

    def inspect(service):
        obj = json.loads(run(['docker', 'inspect', PROJECT + '-' + service + '-1'], True))[0]
        labels = obj['Config']['Labels']
        if labels.get('com.docker.compose.project') != PROJECT or labels.get('com.docker.compose.service') != service:
            raise RuntimeError('Container ownership mismatch')
        image = json.loads(run(['docker', 'image', 'inspect', values['BACKEND_IMAGE' if service == 'backend' else 'ADMIN_IMAGE']], True))[0]
        if image['Id'] != obj['Image']:
            raise RuntimeError('Fixed environment differs from the running image')
        return obj

    before_backend = inspect('backend')
    before_admin = inspect('admin')
    if set(before_backend['NetworkSettings']['Networks']) != {PROJECT + '_admin_private'}:
        raise RuntimeError('Unexpected backend networks')
    if before_admin['NetworkSettings']['Ports'].get('8080/tcp') != [{'HostIp': '127.0.0.1', 'HostPort': '18080'}]:
        raise RuntimeError('Unexpected management port')
    run(['sudo', '-n', 'true'])
    backup_dir = Path(tempfile.mkdtemp(prefix='admin-performance.', dir=env_path.parent))
    backup = backup_dir / 'docker-compose.before.yml'
    backup.write_text(old)
    candidate = backup_dir / 'docker-compose.candidate.yml'
    candidate.write_text(new)
    print('BACKUP=' + str(backup), flush=True)
    run(['sudo', 'install', '-m', '0644', '-o', '10001', '-g', '10001', str(HERE / 'nginx-admin.conf'), str(config)])
    before_doc = json.loads(run(compose(target, 'config', '--format', 'json'), True))
    after_doc = json.loads(run(compose(candidate, 'config', '--format', 'json'), True))
    volumes = after_doc['services']['admin'].pop('volumes')
    if before_doc != after_doc or len(volumes) != 1 or volumes[0]['source'] != str(config) or not volumes[0]['read_only']:
        raise RuntimeError('Unexpected candidate change; original Compose retained')
    run(compose(candidate, 'run', '--rm', '--no-deps', '--pull', 'never', '--interactive=false', '-T',
                '--entrypoint', 'nginx', 'admin', '-t'))
    changed = False
    try:
        run(['sudo', 'install', '-m', '0644', '-o', '10001', '-g', '10001', str(candidate), str(target)])
        changed = True
        run(compose(target, 'up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate',
                    '--wait', '--wait-timeout', '120', 'admin'))
        after_backend = inspect('backend')
        if (after_backend['Id'], after_backend['State']['StartedAt']) != (before_backend['Id'], before_backend['State']['StartedAt']):
            raise RuntimeError('Backend was unexpectedly changed')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:18080/api/v1/app-config', timeout=10) as response:
            if response.status != 200 or json.load(response).get('code') != 200 or 'no-store' not in ','.join(response.headers.get_all('Cache-Control', [])).lower().replace(' ', '').split(','):
                raise RuntimeError('API verification failed')
        with opener.open('http://127.0.0.1:18080/', timeout=10) as response:
            if 'no-store' not in ','.join(response.headers.get_all('Cache-Control', [])).lower().replace(' ', '').split(','):
                raise RuntimeError('HTML must remain uncacheable')
            html = response.read().decode()
        asset = re.search(r'src="(/js/[^" ]+\.js)"', html)
        if not asset:
            raise RuntimeError('Entry asset not found')
        url = 'http://127.0.0.1:18080' + asset.group(1)
        with opener.open(url, timeout=10) as response:
            plain = response.read()
        request = urllib.request.Request(url, headers={'Accept-Encoding': 'gzip'})
        with opener.open(request, timeout=10) as response:
            compressed = response.read()
            if response.headers.get('Content-Encoding') != 'gzip' or 'immutable' not in response.headers.get('Cache-Control', ''):
                raise RuntimeError('Asset compression/cache check failed')
            if gzip.decompress(compressed) != plain:
                raise RuntimeError('Compressed asset content mismatch')
        print('ASSET_BYTES=%s GZIP_BYTES=%s' % (len(plain), len(compressed)), flush=True)
        (backup_dir / 'applied.json').write_text(json.dumps({'backend_unchanged': True,
            'nginx_config_sha256': hashlib.sha256(config.read_bytes()).hexdigest()}, indent=2))
        print('BACKEND_UNCHANGED\nADMIN_PERFORMANCE_APPLIED', flush=True)
    except Exception:
        if changed:
            print('Restoring original management Compose', flush=True)
            run(['sudo', 'install', '-m', '0644', '-o', '10001', '-g', '10001', str(backup), str(target)])
            run(compose(target, 'up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate',
                        '--wait', '--wait-timeout', '120', 'admin'))
        raise


if __name__ == '__main__':
    main()
