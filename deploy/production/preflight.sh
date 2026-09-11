#!/bin/sh
# Read-only host inventory; no environment dumps, secrets, restarts or pruning.
set -eu
uname -sm
 df -h /opt
command -v docker >/dev/null || { echo 'Docker missing'; exit 1; }
docker version --format '{{.Server.Version}}'
docker compose version
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}'
docker network ls --format '{{.Name}}\t{{.Driver}}\t{{.Scope}}'
# Only metadata: never inspect container Env values.
for target in /opt/proxy/docker-compose.yml /opt/proxy/Caddyfile /opt/product-id /opt/passport-admin; do
  if test -e "$target"; then ls -ld "$target"; else echo "Missing: $target"; fi
done
echo 'Read the existing proxy configuration separately with secret values redacted. No configuration changes made.'
