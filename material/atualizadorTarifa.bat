::Esse Script PODE ser executado sozinho
set PGPASSWORD=postgres
set cwd=%~dp0
cd {PGWORKDIR}
psql -U {user} -d {dbname} -h {host} --echo-errors-p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;" >> %cwd%\ScriptAtualizaTarifaLOG.log 2>&1


::Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
{SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}