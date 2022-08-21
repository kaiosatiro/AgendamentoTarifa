from subprocess import Popen, PIPE
from pathlib import Path, PurePath
import psycopg2


def criaTabelaAgendamento(connection, cursor):
    try:
        cursor.execute("""
        CREATE TABLE public.agendamento_config_tarifa
            (
            tarifa bytea,
            nometarifa bytea,
            descontos bytea,
            empresa bigint,
            garagem bigint
            )
        WITH (OIDS=FALSE);
        ALTER TABLE public.agendamento_config_tarifa OWNER TO postgres;""")
    except psycopg2.errors.DuplicateTable:
        connection.rollback()
        cursor.execute('TRUNCATE agendamento_config_tarifa')
    finally:
        connection.commit()
        return True


def psqlRestoreAgendamento(host, user, dbname, port, password, file, workdir):
    #Redundância Truncate via psql
    # truncate_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,
    # '-c', 'TRUNCATE agendamento_config_tarifa'],
    #    cwd=workdir, shell=True, stdin=PIPE)
    # truncate_proc.wait()

    psqlrestore_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(file)],
                            cwd=workdir, shell=True, stdin=PIPE)
    psqlrestore_proc.wait()


def updateNovaTarifa(connection, cursor):
    try:        
        cursor.execute("""
        UPDATE config_tarifa 
        SET
            tarifa = (SELECT tarifa FROM agendamento_config_tarifa),
            nometarifa = (SELECT nometarifa FROM agendamento_config_tarifa),
            descontos = (SELECT descontos FROM agendamento_config_tarifa)""")
    except psycopg2.errors.OperationalError:
        connection.rollback()
        return False
    except psycopg2.DatabaseError:
        connection.rollback()
        return False
    else:
        connection.commit()
        return True


def validaSizeTables(connection, cursor):
    cursor.execute("""
    SELECT relation, total_size FROM 
        (SELECT relname AS "relation",
                pg_size_pretty (pg_total_relation_size (C .oid)) AS "total_size"
        FROM pg_class C
        LEFT JOIN pg_namespace N ON (N.oid = C .relnamespace)
        WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND C .relkind <> 'i' AND nspname !~ '^pg_toast')
        AS tab 
            WHERE relation LIKE '%config_tarifa%'
        ORDER BY relation""")
    query = cursor.fetchall()
    agendamento_config_tarifa_size = int(query[0][1][:2])
    config_tarifa_size = int(query[1][1][:2])
    return config_tarifa_size == agendamento_config_tarifa_size


def atualizacaoParaTarifaNova(host, user, port, dbname, password, file, workdir):
    connection = psycopg2.connect(f'host={host} dbname={dbname} user={user} password={password}')
    cursor = connection.cursor()

    criaTabelaAgendamento(connection, cursor)
    #Restore
    psqlRestoreAgendamento(host, user, dbname, port, password, file, workdir)

    updateNovaTarifa(connection, cursor)
    validaSizeTables(connection, cursor)
    connection.close()


host = 'localhost'
user = 'postgres'
port = '5432'
dbname = 'parkingplus'
password = 'postgres'

version = 8.4
psqldir = Path(f"C:/Program Files (x86)/PostgreSQL/{version}/bin/")
workdir = PurePath(psqldir)
filename = 'TARIFA_NOVA'
saveDir = Path(f"{Path.cwd()}/{filename}")
file = PurePath(saveDir)

atualizacaoParaTarifaNova(host, user, port, dbname, password, file, workdir)