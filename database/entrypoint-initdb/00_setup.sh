#!/usr/bin/env bash

echo "shared_preload_libraries = 'pg_cron'" >> ${PGDATA}/postgresql.conf
echo "cron.database_name='${POSTGRES_DB}'" >> ${PGDATA}/postgresql.conf
pg_ctl restart
