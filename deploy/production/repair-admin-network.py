#!/usr/bin/env python3
"""Guarded repair of the isolated test management gateway; never touches its DB."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
OLD_SHA = '130b9fe4d6a56dc328bde043768e79e155f0ae61c042dfc503f604100ce882bf'
PROJECT = 'passport-admin-test'
PRIVATE = PROJECT + '_admin_private'
ACCESS = PROJECT + '_admin_access'
TARGET = Path('/opt/passport-admin-test/docker-compose.yml')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', required=True)
    parser.add_argument('--apply', action='store_true', help='back up and repair only the test admin gateway')
    args = parser.parse_args()
    os.umask(0o077)
    env_path = Path(args.env).resolve(strict=True)
    release = runpy.run_path(str(HERE / 'release.py'))
    values = release['validate'](release['envfile'](env_path))
    for key, expected in {'ADMIN_PROJECT': PROJECT, 'ADMIN_ROOT': '/opt/passport-admin-test',
                          'PUBLIC_ROOT': '/opt/product-id-test', 'ADMIN_PORT': '18080'}.items():
        require(values.get(key) == expected, 'Unexpected test target: ' + key)
    environment = {**os.environ, **values}

    def run(command, capture=False):
        result = subprocess.run(command, check=True, stdin=subprocess.DEVNULL,
                                env=environment, text=True, stdout=subprocess.PIPE if capture else None)
        return result.stdout if capture else None

    def inspect(kind, name):
        return json.loads(run(['docker', 'inspect', '--type', kind, name], True))[0]

    def compose(file, *arguments):
        return ['docker', 'compose', '--env-file', str(env_path), '-f', str(file), '-p', PROJECT, *arguments]

    def container(service):
        obj = inspect('container', PROJECT + '-' + service + '-1')
        labels = obj['Config']['Labels']
        require(labels.get('com.docker.compose.project') == PROJECT and
                labels.get('com.docker.compose.service') == service, 'Container ownership mismatch')
        require(obj['State'].get('Health', {}).get('Status') == 'healthy', service + ' is not healthy')
        return obj

    require(TARGET.resolve() == TARGET and not TARGET.is_symlink(), 'Unexpected target symlink')
    old = TARGET.read_bytes()
    require(hashlib.sha256(old).hexdigest() == OLD_SHA, 'Installed Compose differs from the known original; no changes made')
    candidate = HERE / 'compose.admin.yml'
    run(compose(candidate, 'config', '--quiet'))
    before_backend = container('backend')
    admin = container('admin')
    requested = admin['HostConfig'].get('PortBindings', {}).get('8080/tcp')
    effective = admin['NetworkSettings'].get('Ports', {}).get('8080/tcp')
    print(json.dumps({'requested_8080': requested, 'effective_8080': effective,
                      'admin_networks': list(admin['NetworkSettings']['Networks'])}), flush=True)
    expected_binding = [{'HostIp': '127.0.0.1', 'HostPort': '18080'}]
    require(requested == expected_binding and not effective, 'Port state does not match the internal-network failure; no changes made')
    require(set(admin['NetworkSettings']['Networks']) == {PRIVATE}, 'Unexpected admin network membership')
    require(set(before_backend['NetworkSettings']['Networks']) == {PRIVATE}, 'Unexpected backend network membership')
    network = inspect('network', PRIVATE)
    require(network.get('Internal') is True and
            network.get('Labels', {}).get('com.docker.compose.project') == PROJECT, 'Unexpected private network')
    for service, obj, key in [('admin', admin, 'ADMIN_IMAGE'), ('backend', before_backend, 'BACKEND_IMAGE')]:
        require(inspect('image', values[key])['Id'] == obj['Image'], service + ' image differs from the running image')
    if not args.apply:
        print('MATCH: internal-only gateway with missing effective port. Re-run with --apply to repair.')
        return
    run(['sudo', '-v'])
    backup_dir = Path(tempfile.mkdtemp(prefix='admin-network.', dir=env_path.parent))
    backup = backup_dir / 'docker-compose.before.yml'
    backup.write_bytes(old)
    print('BACKUP=' + str(backup), flush=True)
    try:
        run(['sudo', 'install', '-m', '0644', '-o', '10001', '-g', '10001', str(candidate), str(TARGET)])
        run(compose(TARGET, 'up', '-d', '--no-build', '--pull', 'never', '--no-deps',
                    '--force-recreate', '--wait', '--wait-timeout', '120', 'admin'))
        after_backend = container('backend')
        require((after_backend['Id'], after_backend['State']['StartedAt']) ==
                (before_backend['Id'], before_backend['State']['StartedAt']), 'Backend identity/start time changed')
        after = container('admin')
        require(after['NetworkSettings']['Ports'].get('8080/tcp') == expected_binding, 'Effective loopback mapping is incorrect')
        require(set(after['NetworkSettings']['Networks']) == {PRIVATE, ACCESS}, 'Unexpected repaired gateway networks')
        access = inspect('network', ACCESS)
        require(not access['Internal'] and access.get('Labels', {}).get('com.docker.compose.project') == PROJECT,
                'Unexpected access network ownership')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:18080/api/v1/app-config', timeout=10) as response:
            require(response.status == 200 and json.load(response).get('code') == 200, 'Host API check failed')
        print('BACKEND_UNCHANGED\nTEST_ADMIN_READY', flush=True)
    except Exception:
        print('Repair incomplete. Preserve evidence; original Compose backup: ' + str(backup), flush=True)
        raise


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as error:
        raise SystemExit(str(error))
