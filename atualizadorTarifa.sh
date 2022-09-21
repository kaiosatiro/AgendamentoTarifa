#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
docker exec -itd $(docker ps | grep db: | cut -d " " -f1) psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"

#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"

#!/bin/sh -xe
#Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
python3 {SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
