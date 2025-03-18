#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

export PGPASSWORD=$POSTGRES_PASSWORD

until psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd 