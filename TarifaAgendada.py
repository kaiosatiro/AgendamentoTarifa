from subprocess import Popen, PIPE
from pathlib import Path, PurePath
from argparse import ArgumentParser
import psycopg2


def checkarquivo(nomecaminho):
    ...


def salvaScript(host, user, port, dbname):
    with open('atualizadorTarifa.bat', 'w') as bat:
        bat.write(f"""
@echo off
::---------------------------------------------------
::SCRIPT para rodar a atualização da tarifa
::---------------------------------------------------
python "%cd%\TarifaAgendada.py" --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
""")


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
        ORDER BY relation 
                    """)
    query = cursor.fetchall()
    agendamento_config_tarifa_size = int(query[0][1][:2])
    config_tarifa_size = int(query[1][1][:2])
    return config_tarifa_size == agendamento_config_tarifa_size


def criaTabelaAgendamento(connection, cursor):
    try:
        cursor.execute("CREATE TABLE agendamento_config_tarifa AS SELECT * FROM config_tarifa;")
    except psycopg2.errors.DuplicateTable:
        connection.rollback()
        cursor.execute("TRUNCATE agendamento_config_tarifa; INSERT INTO agendamento_config_tarifa SELECT * FROM config_tarifa;")
    finally:
        connection.commit()
        return True


def pg_dump(host, user, port, dbname, file, workdir):
    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', 'plain', '--verbose', '--file', str(file),
      '--table', 'public.agendamento_config_tarifa', dbname],
       cwd=workdir, shell=True, stdin=PIPE)
    proc.wait()


# TAREFA QUE REALIZA O DUMP DA TARIFA ALTERADA ==========================================
def preparaTarifaNova(opcao, file, workdir):
    if opcao == 1: 
        host, user, port, dbname, password = 'localhost', 'postgres', '5432', 'parkingplus', 'postgres'
    elif opcao == 2: 
        host, user, port, dbname, password = input('HOST: '), input('USER: '), input('PORT: '), input('BANCO: '), input('PASSWORD: ')
    elif opcao == 3: 
        host, user, port, dbname, password = 'localhost', 'postgres', '5432', 'parkingplus', input('PASSWORD: ')
    
    with pgpass.open(mode='a') as arq: arq.write(f'\n{host}:{port}:*:{user}:{password}')
    
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)
        validaSizeTables(connection, cursor)
        # connection.close()

    pg_dump(host, user, port, dbname, file, workdir)
    checkarquivo(file)


# TAREFA QUE SOBE A NOVA TARIFA NA TABELA === **IMPORTANTE** ============================
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


def atualizacaoTarifa(host, user, port, dbname, pgpass, workdir, backup):
    #Backup de segurança #chkarqbkp
    backupConfigTarifa(host, user, port, dbname, backup, workdir)
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        #Sobe a nova tarifa no banco e valida o tamanho da tabelas
        updateNovaTarifa(connection, cursor)
        validaSizeTables(connection, cursor)
        # connection.close()
    pgpass.unlink()


# TAREFA QUE PREPARA O AGENDAMENTO DA NOVA TARIFA =======================================
def  backupConfigTarifa(host, user, port, dbname, backupname, workdir):
    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', 'custom', '--verbose', '--file', str(backupname),
      '--table', 'public.config_tarifa', dbname],
       cwd=workdir, shell=True, stdin=PIPE)
    proc.wait()


def psqlRestoreAgendamento(host, user, dbname, port, file, workdir):
    # Truncate via psql
    truncate_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,
    '-c', 'TRUNCATE agendamento_config_tarifa'],
       cwd=workdir, shell=True, stdin=PIPE)
    truncate_proc.wait()

    psqlrestore_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(file)],
                            cwd=workdir, shell=True, stdin=PIPE)
    psqlrestore_proc.wait()


def preparaAgendamento(opcao, file, workdir, backupname):
    if opcao == 1: 
        host, user, port, dbname, password = 'localhost', 'postgres', '5432', 'parkingplus', 'postgres'
    elif opcao == 2: 
        host, user, port, dbname, password = input('HOST: '), input('USER: '), input('PORT: '), input('BANCO: '), input('PASSWORD: ')
    elif opcao == 3: 
        host, user, port, dbname, password = 'localhost', 'postgres', '5432', 'parkingplus', input('PASSWORD: ')
    
    with pgpass.open(mode='w') as arq: arq.write(f'\n{host}:{port}:*:{user}:{password}')
    #Backup de segurança 
    backupConfigTarifa(host, user, port, dbname, backupname, workdir)
    checkarquivo(backupname)
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)
        # connection.close()
    psqlRestoreAgendamento(host, user, dbname, port, file, workdir)
    
    salvaScript(host, user, port, dbname) # Salva o script a ser agendado


# INICIO DO PROGRAMA ==============
if __name__ == "__main__":

    # host = 'localhost'
    # user = 'postgres'
    # port = '5432'
    # dbname = 'parkingplus'
    # password = 'postgres'

    version = 8.4
    psqldir = Path(f"C:/Program Files (x86)/PostgreSQL/{version}/bin/")
    workdir = PurePath(psqldir)

    pgpass = Path.home()/'AppData'/'Roaming'/'postgresql'/'pgpass.conf'

    filename = 'TARIFA_NOVA'
    saveDir = Path(f"{Path.cwd()}/{filename}")
    file = PurePath(saveDir)

    backupname = 'BACKUP_SEGURANCA_TARIFA_ATUAL'
    backupSaveDir = Path(f"{Path.cwd()}/{backupname}")
    backup = PurePath(backupSaveDir)
    
#== Parseamento de Argumentos da linha de comando !
    parser = ArgumentParser(description='trigger')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--teste', '-T', action='store_true')
    group.add_argument('--atualizar', action='store_true')
    
    parser.add_argument('--host', '-H', default='localhost')
    parser.add_argument('--port', '-p', default='5432')
    parser.add_argument('--user', '-U', default='postgres')
    parser.add_argument('--dbname', '-db', default='parkingplus')
    # parser.add_argument('--pgpass', '-pgp', default=pgpass)
    # parser.add_argument('--workdir', '-wd', default=workdir)
    # parser.add_argument('--backup', '-bkp', default=backup)

    args = parser.parse_args()


    if args.atualizar: atualizacaoTarifa(args.host, args.user, args.port, args.dbname, pgpass, workdir, backup)
    elif args.teste: print('TESTADO !')
    
    else:
        print("==== ESCOLHA A TAREFA ===========")
        _a = int(input("    1 <---- Preparar Nova Tarifa\n    2 <---- Preparar Agendamento\n    3 <---- Testar\n----> "))

        if _a == 1:
            print("\n==== PREPARAR NOVA TARIFA ========")
            _b = int(input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> "))
            preparaTarifaNova(_b, file, workdir)

        elif _a == 2:
            print("\n==== PREPARAR AGENDAMENTO ========")
            _b = int(input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> "))
            preparaAgendamento(_b, file, workdir, backup)

        elif _a == 3:
            exit()        
    