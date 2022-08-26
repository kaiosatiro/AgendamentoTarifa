from datetime import datetime
from subprocess import Popen, PIPE
from pathlib import Path, PurePath
from argparse import ArgumentParser
import psycopg2


def  backupConfigTarifa(host, user, port, dbname, backup, workdir):
    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', 'custom', '--verbose', '--file', str(backup),
      '--table', 'public.config_tarifa', dbname],
       cwd=workdir, shell=True, stdin=PIPE)
    # proc.stdin.write('postgres\n')
    # return proc.communicate(bytes(password))
    proc.wait()


def criaTabelaAgendamento(connection, cursor):
    try:
        cursor.execute("CREATE TABLE agendamento_config_tarifa AS SELECT * FROM config_tarifa; TRUNCATE agendamento_config_tarifa")
    except psycopg2.errors.DuplicateTable:
        connection.rollback()
        cursor.execute("TRUNCATE agendamento_config_tarifa")
    finally:
        connection.commit()
        return True


def psqlRestoreAgendamento(host, user, dbname, port, file, workdir):
    #Truncate via psql
    # truncate_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,
    # '-c', 'TRUNCATE agendamento_config_tarifa'],
    #    cwd=workdir, shell=True, stdin=PIPE)
    # truncate_proc.wait()

    psqlrestore_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(file)],
                            cwd=workdir, shell=True, stdin=PIPE)
    psqlrestore_proc.wait()


def updateNovaTarifa(connection, cursor):
    try:
        cursor.execute("TRUNCATE config_tarifa; INSERT INTO config_tarifa SELECT * FROM agendamento_config_tarifa;")
        # cursor.execute("""UPDATE config_tarifa 
        #     SET tarifa = (SELECT tarifa FROM agendamento_config_tarifa),
        #     nometarifa = (SELECT nometarifa FROM agendamento_config_tarifa),
        #     descontos = (SELECT descontos FROM agendamento_config_tarifa)""")
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


def atualizacaoParaTarifaNova(host, user, port, dbname, file, workdir, backup):
    #Backup de segurança
    #chkarqbkp
    backupConfigTarifa(host, user, port, dbname, backup, workdir)
    #Inicio do processo
    connection = psycopg2.connect(f'host={host} dbname={dbname} user={user}')
    cursor = connection.cursor()
    criaTabelaAgendamento(connection, cursor)
    #Restore
    psqlRestoreAgendamento(host, user, dbname, port, file, workdir)
    #Sobe a nova tarifa no banco e valida o tamanho da tabelas
    updateNovaTarifa(connection, cursor)
    validaSizeTables(connection, cursor)
    connection.close()


# INICIO DO PROGRAMA
if __name__ == "__main__":

    # host = 'localhost'
    # user = 'postgres'
    # port = '5432'
    # dbname = 'parkingplus'
    # password = 'postgres'
    version = 8.4
    psqldir = Path(f"C:/Program Files (x86)/PostgreSQL/{version}/bin/")
    workdir = PurePath(psqldir)

    filename = 'TARIFA_NOVA'
    saveDir = Path(f"{Path.cwd()}/{filename}")
    file = PurePath(saveDir)

    backupname = 'BACKUP_SEGURANCA_TARIFA_ATUAL'
    backupSaveDir = Path(f"{Path.cwd()}/{backupname}")
    backup = PurePath(backupSaveDir)

    pgpass = Path.home()/'AppData'/'Roaming'/'postgresql'/'pgpass.conf'

    parser = ArgumentParser(description='trigger')
    parser.add_argument('--atualizar', '-a', default=False)
    args = parser.parse_args()

    if args.atualizar: atualizacaoParaTarifaNova(host, user, port, dbname, password, file, workdir, backup)
    
    else:
        # host = 'localhost'
        # user = 'postgres'
        # port = '5432'
        # dbname = 'parkingplus'
        # password = 'postgres'
        opcao = "1 <<<< Preparar Nova Tarifa\n2 <<<< Preparar Agendamento\n3 <<<< Testar"
        if opcao == 1: ...
        elif opcao == 2: ...
        elif opcao == 3: ...        
        
        with pgpass.open(mode='w') as arq:
            arq.write(f'localhost:5432:*:postgres:{password}')

        atualizacaoParaTarifaNova(host, user, port, dbname, password, file, workdir, backup)

        pgpass.unlink()


        # host = input('HOST: ')    
        # user = input('USER: ')
        # port = '5432'
        # dbname = input('BANCO: ')
        # password = 'postgres' 