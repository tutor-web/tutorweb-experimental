#!/bin/sh
set -eu


[ "${1-}" = "--recreate" ] && { DB_RECREATE="x"; shift; } || DB_RECREATE=""
DB_NAME=${1-tw_db}
PSQL="psql -X --set ON_ERROR_STOP=1 --set AUTOCOMMIT=off"

if ${PSQL} -l | grep -q "${DB_NAME}"; then
    if [ -n "${DB_RECREATE}" ]; then
        echo "DROP DATABASE ${DB_NAME}" | ${PSQL} postgres
        createdb "${DB_NAME}"
    fi
else
    createdb "${DB_NAME}"
fi

for s in "$(dirname $0)"/*.sql; do
    echo "=============== $s"
    ${PSQL} -a -f "$s" "${DB_NAME}"
done
