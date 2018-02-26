#!/bin/sh
set -eu

DB_NAME=${1-tw_db}
DB_RECREATE="x"  # TODO: Command-line option
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
