#!/bin/sh -xe
export PGPASSWORD=test
USER='postgres'
BANCO='parkingplus'
SERVIDOR='localhost'
PORTA='5432'
docker exec -itd $(docker ps | grep db: | cut -d ' ' -f1) psql -U $USER -d $BANCO -h $SERVIDOR -p $PORTA -c "BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"
