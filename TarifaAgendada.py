from subprocess import Popen, PIPE
from pathlib import Path, PurePath
from argparse import ArgumentParser
from platform import system
from time import strftime
import psycopg2


#Script a ser executado pelo agendador de tarefas do sistema operacional
def salvaScript(host, user, port, dbname, password):
    windows = {
        'nome': 'atualizadorTarifa.bat',
        'script': f'''::Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
{SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
''' ,
        'nome2': 'atualizadorTarifaIndependente.bat',
        'script2': f'''::Esse Script PODE ser executado sozinho
set PGPASSWORD=postgres
cd {PGWORKDIR}
psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"
''' 
    }
    linux = {
        'nome': 'atualizadorTarifa.sh',
        'script': f'''#!/bin/sh -xe
#Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
python3 {SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
''',
        'nomeOS5': 'atualizadorTarifaIndependente.sh',
        'scriptOS5': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"
''',
        'nomeOS7': 'atualizadorTarifaIndependente.sh',
        'scriptOS7': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
docker exec -itd $(docker ps | grep db: | cut -d " " -f1) psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"
''' 
    }

    print("\n===== SALVAR SCRIPT PARA ==========")
    if OS == 'Windows':
        i = input("    1 <---- LINUX CentOS 7\n    2 <---- LINUX CentOS 5\n    3 <---- WINDOWS\n----> ")
        if i not in ('1', '2', '3'): input("Opção inválida!"), exit()
        input('No Linux, LEMBRE-SE de executar o CHMOD no script')
    elif OS == 'Linux':
        i = input("    1 <---- LINUX CentOS 7\n    2 <---- LINUX CentOS 5\n----> ")
        if i not in ('1', '2'): input("Opção inválida!"), exit()
        input('LEMBRE-SE de executar o CHMOD no script')

    if i == '1':
        nomearq = linux['nomeOS7']
        script = linux['scriptOS7']
    elif i == '2':
        nomearq == linux['nomeOS5']
        script == linux['scriptOS5']
    elif i == '3':
        nomearq = windows['nome2']
        script = windows['script2']

    if OS == 'Linux':
        nomearq2 = linux['nome']
        script2 = linux['script']
    elif OS == 'Windows':
        nomearq2 = windows['nome']
        script2 = windows['script']
    
    with open(nomearq, 'w') as arq: arq.write(script)
    with open(nomearq2, 'w') as arq2: arq2.write(script2)
    return True

#Função que compara os tamanhos das tabelas, como um dispositivo de segurança
def validaSizeTables(cursor):
    #SELECT relation, total_size FROM ( SELECT relname AS "relation", pg_size_pretty (pg_total_relation_size (C.oid)) AS "total_size" FROM pg_class C LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace) WHERE nspname NOT IN ('pg_catalog', 'information_schema') AND C.relkind <> 'i' AND nspname !~ '^pg_toast' ) AS tab WHERE relation LIKE '%config_tarifa%' ORDER BY relation
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
    agendamento_config_tarifa_Size = int(query[0][1][:2])
    config_tarifa_Size = int(query[1][1][:2])
    return config_tarifa_Size == agendamento_config_tarifa_Size


def criaTabelaAgendamento(connection, cursor):
    #psql -U postgres -d parkingplus -c "DROP TABLE IF EXISTS agendamento_config_tarifa;CREATE TABLE agendamento_config_tarifa AS SELECT * FROM config_tarifa;"
    try:
        cursor.execute("DROP TABLE IF EXISTS agendamento_config_tarifa;CREATE TABLE agendamento_config_tarifa AS SELECT * FROM config_tarifa;")
    except psycopg2.errors.DuplicateTable:
        connection.rollback()
        cursor.execute("TRUNCATE agendamento_config_tarifa; INSERT INTO agendamento_config_tarifa SELECT * FROM config_tarifa;")
    finally:
        connection.commit()
        return True


#Funcoes PG_DUMP
def dump(host, user, port, dbname, filename, type, tablename):
    shl = False if OS == 'Linux' else True
    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', type, '--verbose', '--file', str(filename),
      '--table', tablename, dbname],
       cwd=PGWORKDIR, shell=shl, stdin=PIPE)
    proc.wait()


#Funcoes de RESTORE
def restore(tipo, host, user, dbname, port, filename, table):
    shl = False if OS == 'Linux' else True
    if tipo == 'pg_restore':
        proc = Popen(['pg_restore', '--clean', '--host', host, '--port', port, 
        '--username', user, '--dbname', dbname, '--verbose', str(filename)],
                    cwd=PGWORKDIR, shell=shl, stdin=PIPE)
        proc.wait()
    elif tipo == 'psql':
        truncate = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,'-c', f'TRUNCATE {table}'],
                    cwd=PGWORKDIR, shell=shl, stdin=PIPE)
        truncate.wait()
        proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(filename)],
                    cwd=PGWORKDIR, shell=shl, stdin=PIPE)
        proc.wait()


# TAREFA QUE REALIZA O DUMP DA TARIFA ALTERADA ==========================================
def preparaTarifaNova(opcao):
    if _a not in ('1', '2', '3'): input("Opção inválida!"), exit()
    if opcao == '2':
        host = input('HOST: ')
        user = input('USER: ')
        port = input('PORT: ')
        dbname = input('BANCO: ')
        password = input('PASSWORD: ')
    else:
        host, user, port, dbname = 'localhost', 'postgres', '5432', 'parkingplus'
        if opcao == '1': password = 'postgres'
        else: password = input('PASSWORD: ')
    
    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG ***
    
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)# IMPORTANTE LOG ***
        validaSizeTables(cursor)# IMPORTANTE LOG ***

    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    dump(host, user, port, dbname, tarifanovaName, 'custom', 'public.agendamento_config_tarifa') # IMPORTANTE LOG ***



# TAREFA QUE PREPARA O AGENDAMENTO DA NOVA TARIFA =======================================
def preparaAgendamento(opcao):
    if _a not in ('1', '2', '3'): input("Opção inválida!"), exit()
    if opcao == '2':
        host = input('HOST: ')
        user = input('USER: ')
        port = input('PORT: ')
        dbname = input('BANCO: ')
        password = input('PASSWORD: ')
    else:
        host, user, port, dbname = 'localhost', 'postgres', '5432', 'parkingplus'
        if opcao == '1': password = 'postgres'
        else: password = input('PASSWORD: ')

    with PGPASS.open(mode='w') as arq: 
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG E TRATATIVA DE ERRO ***
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG E TRATATIVA DE ERRO ***
        
    #Backup de segurança
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')# IMPORTANTE LOG E TRATATIVA DE ERRO ***
    if not Path(backupname).is_file():
        return False

    #Criacao da tabela
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)

    #Coloca a nova tarifa na tabela de agendamento
    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    restore('pg_restore', host, user, dbname, port, tarifanovaName, 'agendamento_config_tarifa')# IMPORTANTE LOG E TRATATIVA DE ERRO ***
    #Salva o script a ser executado
    salvaScript(host, user, port, dbname, password)

    i = input('EXCLUIR o arquivo PGPASS ?? (Y)')
    if i in ('Y', 'y'):
        PGPASS.unlink()
    


# TAREFA QUE SOBE A NOVA TARIFA NA TABELA =============== **IMPORTANTE** ================
def atualizacaoTarifa(host, user, port, dbname):
    #Backup de segurança e checagem de arquivo
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')# IMPORTANTE LOG ***
    if not Path(backupname).is_file():
        return False
    #Atualizacao ta tarifa
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;")
        except psycopg2.errors.OperationalError:
            connection.rollback()
            return False
        except psycopg2.DatabaseError:
            connection.rollback()
            return False
        else:
            connection.commit()
            if not validaSizeTables(cursor):
                return False
            PGPASS.unlink()
            return True


def testesdeAmbiente():
    shl = False if OS == 'Linux' else True
    #Testes de Postgres
    try:
        psql = Popen(['psql', '-V'], cwd=PGWORKDIR, shell=shl)
        psql.wait()
        psql = psql.returncode == 0#Valida o teste
    except NotADirectoryError:
        psql = False
    try:
        pg_dump = Popen(['pg_dump', '-V'], cwd=PGWORKDIR, shell=shl)
        pg_dump.wait()
        pg_dump = pg_dump.returncode == 0#Valida o teste
    except NotADirectoryError:
        pg_dump = False
    try:
        pg_restore = Popen(['pg_restore', '-V'], cwd=PGWORKDIR, shell=shl)
        pg_restore.wait()
        pg_restore = pg_restore.returncode == 0#Valida o teste
    except NotADirectoryError:
        pgpass = False
    #Testes de gravação
    try:
        with PGPASS.open(mode='w') as arq: 
            arq.write(f'\n::*::')
            pgpass =  Path(PGPASS).is_file()#Valida o teste
        PGPASS.unlink()
    except PermissionError:
        pgpass = False#Valida o teste
    
    ok = '[ OK ]'
    errgrav = '[ ERRO ] > Erro na gravação do arquivo. Execute como Admnistrador'
    if OS == 'Linux':
        errpsql = "[ ERRO ] > binario não encontrado na pasta"
    elif OS == 'Windows':
        errpsql = "[ ERRO ] > binario não encontrado na pasta 'C:/Program Files (x86)/PostgreSQL/8.4/bin/'"

    print('\n=========== TESTES ================')
    print(f'Teste -- PSQL ------------ {ok if psql else errpsql}')
    print(f'Teste -- PG_DUMP --------- {ok if pg_dump else errpsql}')
    print(f'Teste -- PG_RESTORE------- {ok if pg_restore else errpsql}')
    print(f'Teste -- GRAVACAO -------- {ok if pgpass else errgrav}')


# INICIO DO PROGRAMA ==============
if __name__ == "__main__":

    OS = system()
    CWD = Path.cwd()
    DATE = strftime("%Y-%m-%d")
    SCRIPTDIR = Path( __file__ ).absolute()

    if OS == 'Linux':
        psqlUnixdir = Path(f"/bin/")
        PGWORKDIR = PurePath(psqlUnixdir)
        PGPASS = Path.home()/'.pgpass'

    elif OS == 'Windows':
        psqlWindir = Path(f"C:/Program Files (x86)/PostgreSQL/8.4/bin/")
        if not psqlWindir.is_dir():
            print('Diretorio do PostgreSQL não encontrado')
            input('C:/Program Files (x86)/PostgreSQL/8.4/bin/')
            exit()
        PGWORKDIR = PurePath(psqlWindir)
        PGPASS = Path.home()/'AppData'/'Roaming'/'postgresql'/'pgpass.conf'    

# Parseamento de Argumentos da linha de comando
    parser = ArgumentParser(description='trigger')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--teste', '-T', action='store_true')
    group.add_argument('--atualizar', action='store_true')
    
    parser.add_argument('--host', '-H', default='localhost')
    parser.add_argument('--port', '-p', default='5432')
    parser.add_argument('--user', '-U', default='postgres')
    parser.add_argument('--dbname', '-db', default='parkingplus')

    args = parser.parse_args()

    if args.atualizar:
        atualizacaoTarifa(args.host, args.user, args.port, args.dbname)
    elif args.teste:
        testesdeAmbiente()
    # elif OS == 'Windows':
    else:
        print("\n==== ESCOLHA A TAREFA ===========")
        _a = input("    1 <---- Preparar Nova Tarifa\n    2 <---- Preparar Agendamento\n    3 <---- Testar\n----> ")
        if _a not in ('1', '2', '3'): input("Opção inválida!")
        if _a == '1':
            print("\n==== PREPARAR NOVA TARIFA ========")
            _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
            preparaTarifaNova(_b)
        elif _a == '2':
            print("\n==== PREPARAR AGENDAMENTO ========")
            _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
            preparaAgendamento(_b)
        elif _a == '3':
            testesdeAmbiente()
