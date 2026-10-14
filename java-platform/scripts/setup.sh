#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ -f .env ]; then echo ".env already exists; kept existing secrets."; exit 0; fi
umask 077
{
  echo "DB_PASSWORD=$(openssl rand -hex 32)"
  echo "MYSQL_ROOT_PASSWORD=$(openssl rand -hex 32)"
  echo "RABBIT_PASSWORD=$(openssl rand -hex 32)"
  echo "JWT_SECRET=$(openssl rand -hex 32)"
  echo "ADMIN_USERNAME=admin"
  echo "ADMIN_PASSWORD=$(openssl rand -hex 32)"
  echo "SEED_DEMO=true"
} > .env
echo "Created .env with random secrets. Read admin credentials locally."

