#!/bin/sh
set -eu
umask 077
/app/passport-ops check-config --config /run/config/settings.yml
# config is rendered and validated by prepare.py; never generated from a development config.
case "${1:-server}" in
  migrate) exec /app/passport-admin migrate -c /run/config/settings.yml ;;
  bootstrap) exec /app/passport-ops bootstrap --db /data/db/passport.db --password-file /run/config/admin-password ;;
  check) exec /app/passport-ops check --db /data/db/passport.db ;;
  server)
    /app/passport-ops check --db /data/db/passport.db
    exec /app/passport-admin server -c /run/config/settings.yml ;;
  *) echo 'Only server, migrate, bootstrap or check are supported' >&2; exit 2 ;;
esac
