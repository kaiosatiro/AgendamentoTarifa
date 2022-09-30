#!/usr/bin/python3
from subprocess import Popen
from pathlib import Path, PurePath
from argparse import ArgumentParser
from time import strftime
from os import system as sys
import psycopg2


#Script a ser executado pelo agendador de tarefas do sistema operacional
def salvaScript(host, user, port, dbname, password):
    #Scripts para Linux
    linux = {
        'nome': 'ScriptAtualizaTarifa.sh',
        'script': f'''#!/bin/sh -xe
#Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
{FILEDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
''',
        'nomeOS5': 'ScriptAtualizaTarifaCentOS5.sh',
        'scriptOS5': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;" >> /WPSBrasil/agendamento_tarifa/ScriptAtualizaTarifaLOG.log 2>&1
''',
        'nomeOS7': 'ScriptAtualizaTarifaCentOS7.sh',
        'scriptOS7': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
docker exec -itd $(docker ps | grep db: | cut -d " " -f1) psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;" >> /WPSBrasil/agendamento_tarifa/ScriptAtualizaTarifaLOG.log 2>&1
''' 
    }

    #Fonece as opções de sistema operacional
    while True:
        print("\n===== SALVAR SCRIPT PARA ==========")
        i = input("    1 <---- LINUX CentOS 7\n    2 <---- LINUX CentOS 5\n----> ")
        if i not in ('1', '2'):
            input("Opção inválida!")
            sys('clear')
            continue
        input('LEMBRE-SE de executar o CHMOD no script')
        break

    if i == '1':
        nomearq = linux['nomeOS7']
        script = linux['scriptOS7']
    elif i == '2':
        nomearq == linux['nomeOS5']
        script == linux['scriptOS5']

    nomearq2 = linux['nome']
    script2 = linux['script']
    
    #Grava os scripts
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
    except psycopg2.errors.OperationalError:
        connection.rollback()
        return False, 'Psycopg ERRO Operacional na criação da tabela'
    except psycopg2.DatabaseError:
        connection.rollback()
        return False, 'Psycopg ERRO Banco de Dados na criação da tabela'
    else:
        connection.commit()
        if not validaSizeTables(cursor):
            return False, 'ERRO, desigualdade na comparação do tamanho das tabelas'
        return True, 'OK'



#Funcoes PG_DUMP
def dump(host, user, port, dbname, filename, type, tablename):
    proc = Popen(['pg_dump',
                    '--host', host, '-U', user, '--port', port,
                    '--format', type, '--verbose', '--file', str(filename),
                    '--table', tablename, dbname])
    proc.wait()
    return proc.returncode == 0


#Funcoes de RESTORE
def restore(tipo, host, user, dbname, port, filename, table):
    if tipo == 'pg_restore':
        proc = Popen(['pg_restore',
                        '--clean', '--host', host, '--port', port, 
                        '--username', user, '--dbname', dbname, 
                        '--verbose', str(filename)])
        proc.wait()
    elif tipo == 'psql':
        truncate = Popen(['psql',
                            '-U', user, '-d', dbname, '-h', host,
                            '-p', port,'-c', f'TRUNCATE {table}'])
        truncate.wait()
        proc = Popen(['psql',
                        '-U', user, '-d', dbname, '-h', host,
                        '-p', port, '<', str(filename)])
        proc.wait()
    return proc.returncode == 0


# TAREFA QUE REALIZA O DUMP DA TARIFA ALTERADA ==========================================
def preparaTarifaNova(opcao):
    #Recebe os parametros do Banco
    if opcao not in ('1', '2', '3'):
        return False, "Opção inválida!"
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
    
    #Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
        Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG ***
    
    #Cria a tabela agendamento e verifica a igualdade dos tamanhos
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        retorno = criaTabelaAgendamento(connection, cursor)# IMPORTANTE LOG ***
        if not retorno[0]:
            return retorno

    #Realiza o DUMP da tarifa a ser carregada no cliente
    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    retorno = dump(host, user, port, dbname, tarifanovaName, 'custom', 'public.agendamento_config_tarifa') # IMPORTANTE LOG ***
    if not retorno:
        return False, 'ERRO no dump da tabela'
    return True, 'Concluido'


# TAREFA QUE PREPARA O AGENDAMENTO DA NOVA TARIFA =======================================
def preparaAgendamento(opcao):
    #Recebe os parametros do Banco
    if opcao not in ('1', '2', '3'): 
        return False, "Opção inválida!"
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

    #Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq: 
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
        Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG  ***

    #Backup de segurança
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    retorno = dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')# IMPORTANTE LOG ***
    if not retorno:
        return False, 'ERRO no dump do BACKUP'

    #Criacao da tabela
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        retorno = criaTabelaAgendamento(connection, cursor)
        if not retorno[0]:
            return retorno

    #Carrega a nova tarifa na tabela de agendamento
    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    retorno = restore('pg_restore', host, user, dbname, port, tarifanovaName, 'agendamento_config_tarifa')# IMPORTANTE LOG ***
    if not retorno:
        return False, 'ERRO no carregamento da tarifa nova!' 
   
    #Salva o script a ser executado
    salvaScript(host, user, port, dbname, password)

    i = input('MANTER o arquivo PGPASS ?? (Y/y)\n>>>')
    if i not in ('Y', 'y'):
        PGPASS.unlink()
        print('PGPASS Excluído!')

    return True, 'Carregamento da nova tarifa Concluido!'


# TAREFA QUE SOBE A NOVA TARIFA NA TABELA =============== **IMPORTANTE** ================
def atualizacaoTarifa(host, user, port, dbname):
    #Backup de segurança e checagem da arquivo de backup
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    retorno = dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')# IMPORTANTE LOG ***
    if not retorno:
        return False, 'FALHA no dump do backup'
    if not Path(backupname).is_file():
        return False, 'FALHA, backup não encontrado antes da tarefa'

    #Atualizacao da tarifa
    print('Conectando ao banco para atualizar')
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        try:
            print('Atualizando')
            cursor.execute("DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;")
        except psycopg2.errors.OperationalError:
            connection.rollback()
            return False, backupname, 'FALHA Psycopg, ERRO operacional durante a atualização'
        except psycopg2.DatabaseError:
            connection.rollback()
            return False, backupname, 'FALHA Psycopg, Erro no banco de dados durante a atualização'
        else:
            connection.commit()
            if not validaSizeTables(cursor):
                return False, backupname, 'ERRO, desigualdade na comparação do tamanho das tabelas'
        print('Concluido')
        print('Removendo pgpass')
        PGPASS.unlink()
        print('Removido')
        return True, 'Atualização concluida com SUCESSO!'


def testesdeAmbiente():
    #Testes de Postgres
    try:
        psql = Popen(['psql', '-V'])
        psql.wait()
        psql = psql.returncode == 0 #Valida o teste
    except NotADirectoryError:
        psql = False
    try:
        pg_dump = Popen(['pg_dump', '-V'])
        pg_dump.wait()
        pg_dump = pg_dump.returncode == 0 #Valida o teste
    except NotADirectoryError:
        pg_dump = False
    try:
        pg_restore = Popen(['pg_restore', '-V'])
        pg_restore.wait()
        pg_restore = pg_restore.returncode == 0 #Valida o teste
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
    errgrav = '[ ERRO ] > Erro na gravação do arquivo. Verifique a permissão de execução (chmod)'
    errpsql = "[ ERRO ] > binario não encontrado "
    
    print('\n=========== TESTES ================')
    print(f'Teste -- PSQL ------------ {ok if psql else errpsql}')
    print(f'Teste -- PG_DUMP --------- {ok if pg_dump else errpsql}')
    print(f'Teste -- PG_RESTORE------- {ok if pg_restore else errpsql}')
    print(f'Teste -- GRAVACAO -------- {ok if pgpass else errgrav}')
    input('Concluidos!')

#=== INICIO DO PROGRAMA ==============
if __name__ == "__main__":

    CWD = Path.cwd()
    DATE = strftime("%Y-%m-%d")
    PGPASS = Path.home()/'.pgpass'
    FILEDIR = Path( __file__ ).absolute()

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

#======= Linha de Seleção de tarefas do programa ================
    #Atualização via linha de comando
    if args.atualizar:
        retorno = atualizacaoTarifa(args.host, args.user, args.port, args.dbname)
        if not retorno[0]:
            print(retorno[2])
            print('Restore de emergencia')
            res = restore('custom', args.host, args.user, args.dbname, args.port, retorno[1], 'config_tarifa')
            if not res:
                print('FALHA restore emergencial')# IMPORTANTE LOG ***
                exit()
            print('Realizado restore emergencial')

    #Testes via linha de comando
    elif args.teste:
        testesdeAmbiente()

    #Opções em menu shell
    else:      
        print('\n*** Realize os testes primeiro ***')
        print('** Recomenda-se que o programa seja executado do diretório:')
        print('/WPSBrasil/agendamento_tarifa')
        while True:
            print("\n==== ESCOLHA A TAREFA ===========")
            _a = input("    1 <---- Preparar Nova Tarifa\n    2 <---- Preparar Agendamento\n    3 <---- Testes!\n    Q <---- Sair...\n----> ").upper()
            if _a not in ('1', '2', '3', 'Q'):
                input("Opção inválida!")
            if _a == '1':
                print("\n==== PREPARAR NOVA TARIFA ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = preparaTarifaNova(_b)
                input(retorno[1])
            elif _a == '2':
                print("\n==== PREPARAR AGENDAMENTO ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = preparaAgendamento(_b)
                input(retorno[1])
            elif _a == '3':
                testesdeAmbiente()
            elif _a == 'Q':
                break
            sys('clear')
