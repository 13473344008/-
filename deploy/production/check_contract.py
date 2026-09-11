#!/usr/bin/env python3
"""Static contract only, not a substitute for Docker Compose or a running host."""
from pathlib import Path
import yaml
r=Path(__file__).resolve().parent
admin=yaml.safe_load((r/'compose.admin.yml').read_text());public=yaml.safe_load((r/'compose.public.yml').read_text())
s=public['services']['public']
assert 'ports' not in s and 'depends_on' not in s
assert public['networks']['edge']['external'] is True
assert admin['networks']['admin_private']['internal'] is True
assert not admin['services']['backend'].get('ports')
assert admin['services']['backend']['networks']==['admin_private']
assert set(admin['services']['admin']['networks'])=={'admin_private','admin_access'}
assert admin['networks']['admin_access']['internal'] is False
assert not admin['networks']['admin_access'].get('external')
assert all(p.startswith('127.0.0.1:') for p in admin['services']['admin']['ports'])
for doc in [admin,public]:
 for name,svc in doc['services'].items():
  assert svc['read_only'] and svc['cap_drop']==['ALL'] and svc['user']=='10001:10001'
  assert svc['mem_limit'] and svc['pids_limit'] and svc['cpus']>0 and svc['healthcheck']
  assert all(isinstance(x,str) and x.startswith('/tmp:') for x in svc['tmpfs'])
  for v in svc.get('volumes',[]):
   assert v['bind']['create_host_path'] is False
   assert not any(x in str(v) for x in ['docker.sock','/opt/proxy','directus'])
   if name=='public' and v['target']!='/var/log/passport':assert v['read_only'] is True
assert 'sqlite3,t4_schema' in (r/'Dockerfile.backend').read_text()
print('PASS: static deployment isolation, mounts, resources and build-tag contract')
