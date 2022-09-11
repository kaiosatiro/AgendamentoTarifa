from subprocess import Popen, PIPE
from pathlib import Path, PurePath
from argparse import ArgumentParser
from platform import system
from time import strftime
import psycopg2


#Script a ser executado pelo agendador de tarefas do sistema operacional
def salvaScript(host, user, port, dbname):
    if OS == 'Linux':
        arquivo = 'atualizadorTarifa.sh'
        linha = f'#!/bin/sh -xe\npython3 {SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}'
    elif OS == 'Windows':
        arquivo = 'atualizadorTarifa.bat'
        linha = f"python {SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}"

    with open(arquivo, 'w') as script: script.write(linha)


#função que compara os tamanhos das tabelas, como um dispositivo de segurança
def validaSizeTables(cursor):
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
    try:
        cursor.execute("CREATE TABLE agendamento_config_tarifa AS SELECT * FROM config_tarifa;")
    except psycopg2.errors.DuplicateTable:
        connection.rollback()
        cursor.execute("TRUNCATE agendamento_config_tarifa; INSERT INTO agendamento_config_tarifa SELECT * FROM config_tarifa;")
    finally:
        connection.commit()
        return True


#Funcoes PG_DUMP
def dump(host, user, port, dbname, filename, type, tablename):
    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', type, '--verbose', '--file', str(filename),
      '--table', tablename, dbname],
       cwd=PGWORKDIR, shell=True, stdin=PIPE)
    proc.wait()


#Funcoes de RESTORE
def restore(tipo, host, user, dbname, port, filename, table):
    pg_restore = ['pg_restore', '--host', host, '--port', port, '--username', 
                    user, '--dbname', dbname, '--verbose', str(filename)]
    psql = ['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(filename)]

    truncate = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,'-c', f'TRUNCATE {table}'],
                    cwd=PGWORKDIR, shell=True, stdin=PIPE)
    truncate.wait()

    if tipo == 'pg_restore':
        proc = Popen(pg_restore, cwd=PGWORKDIR, shell=True, stdin=PIPE)
        proc.wait()
    elif tipo == 'psql':
        proc = Popen(psql, cwd=PGWORKDIR, shell=True, stdin=PIPE)
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
        arq.write(f'\n{host}:{port}:*:{user}:{password}')
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])
    
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)
        validaSizeTables(cursor)

    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    dump(host, user, port, dbname, tarifanovaName, 'plain', 'public.agendamento_config_tarifa')
    if not Path(tarifanovaName).is_file():
        return print('FALSE')
    return print('True')


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
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE TRATATIVA DE ERRO ***
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])# IMPORTANTE TRATATIVA DE ERRO ***
        
    #Backup de segurança
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')
    if not Path(backupname).is_file():
        return False
    #Criacao da tabela
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        criaTabelaAgendamento(connection, cursor)

    #Coloca a nova tarifa na tabela de agendamento
    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    restore('psql', host, user, dbname, port, tarifanovaName, 'agendamento_config_tarifa')
    salvaScript(host, user, port, dbname) # Salva o script a ser executado


# TAREFA QUE SOBE A NOVA TARIFA NA TABELA =============== **IMPORTANTE** ================
def atualizacaoTarifa(host, user, port, dbname):
    #Backup de segurança e checagem de arquivo
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')
    if not Path(backupname).is_file():
        return False
    #Atualizacao ta tarifa
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("TRUNCATE config_tarifa; INSERT INTO config_tarifa SELECT * FROM agendamento_config_tarifa;")
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
        print('TESTE (Em desenvolvimento) !')
    
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
            print('Função em desenvolvimento!')    
        