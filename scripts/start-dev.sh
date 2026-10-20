#!/bin/sh
set -eu

# Compose waits for PostgreSQL's health check before starting this command.
python backend/manage.py migrate --noinput
case "${DEBUG:-}" in
  1|true|TRUE|yes|YES) python backend/manage.py seed_venues ;;
esac
exec python backend/manage.py runserver 0.0.0.0:8000
