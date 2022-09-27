from subprocess import Popen, PIPE
from pathlib import Path, PurePath
from argparse import ArgumentParser
from platform import system
from time import strftime
import psycopg2


#Script a ser executado pelo agendador de tarefas do sistema operacional
def salvaScript(host, user, port, dbname, password):
    #Scripts para windows
    windows = {
        'nome': 'ScriptAtualizaTarifa.bat',
        'script': f'''::Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
{SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
''' ,
        'nome2': 'ScriptAtualizaTarifaWINDOWS.bat',
        'script2': f'''::Esse Script PODE ser executado sozinho
set PGPASSWORD={password}
set cwd=%~dp0
cd {PGWORKDIR}
psql -U {user} -d {dbname} -h {host} -p {port} -c "DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;" >> %cwd%\ScriptAtualizaTarifaLOG.log 2>&1
''' 
    }
    #Scripts para Linux
    linux = {
        'nome': 'ScriptAtualizaTarifa.sh',
        'script': f'''#!/bin/sh -xe
#Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
python3 {SCRIPTDIR} --atualizar --host {host} --user {user} --port {port} --dbname {dbname}
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

    print("\n===== SALVAR SCRIPT PARA ==========")
    #Fonece as opções de acordo com o sistema operacional
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
    shl = False if OS == 'Linux' else True

    proc = Popen(['pg_dump', '--host', host, '-U', user, '--port', port,
     '--format', type, '--verbose', '--file', str(filename),
      '--table', tablename, dbname],
       cwd=PGWORKDIR, shell=False, stdin=PIPE)
    proc.wait()
    return proc.returncode == 0


#Funcoes de RESTORE
def restore(tipo, host, user, dbname, port, filename, table):
    shl = False if OS == 'Linux' else True

    if tipo == 'pg_restore':
        proc = Popen(['pg_restore', '--clean', '--host', host, '--port', port, 
        '--username', user, '--dbname', dbname, '--verbose', str(filename)],
                    cwd=PGWORKDIR, shell=False, stdin=PIPE)
        proc.wait()
    elif tipo == 'psql':
        truncate = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,'-c', f'TRUNCATE {table}'],
                    cwd=PGWORKDIR, shell=False, stdin=PIPE)
        truncate.wait()
        proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port, '<', str(filename)],
                    cwd=PGWORKDIR, shell=False, stdin=PIPE)
        proc.wait()
    return proc.returncode == 0


# TAREFA QUE REALIZA O DUMP DA TARIFA ALTERADA ==========================================
def preparaTarifaNova(opcao):
    #Recebe os parametros do Banco
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
    
    #Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG ***
    
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

    #Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq: 
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
        if OS == 'Linux': Popen(['chmod', '0600', PGPASS])# IMPORTANTE LOG  ***

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

    #Atualizacao ta tarifa
    with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
        cursor = connection.cursor()
        try:
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
        PGPASS.unlink()
        return True, 'Atualização concluida com SUCESSO!'


def testesdeAmbiente():
    shl = False if OS == 'Linux' else True
    #Testes de Postgres
    try:
        psql = Popen(['psql', '-V'], cwd=PGWORKDIR, shell=False)
        psql.wait()
        psql = psql.returncode == 0#Valida o teste
    except NotADirectoryError:
        psql = False
    try:
        pg_dump = Popen(['pg_dump', '-V'], cwd=PGWORKDIR, shell=False)
        pg_dump.wait()
        pg_dump = pg_dump.returncode == 0#Valida o teste
    except NotADirectoryError:
        pg_dump = False
    try:
        pg_restore = Popen(['pg_restore', '-V'], cwd=PGWORKDIR, shell=False)
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


#=== INICIO DO PROGRAMA ==============
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
        print("\n==== ESCOLHA A TAREFA ===========")
        _a = input("    1 <---- Preparar Nova Tarifa\n    2 <---- Preparar Agendamento\n    3 <---- Testar\n----> ")
        if _a not in ('1', '2', '3'): input("Opção inválida!")
        if _a == '1':
            print("\n==== PREPARAR NOVA TARIFA ========")
            _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
            retorno = preparaTarifaNova(_b)
            input(retorno[1])
        elif _a == '2':
            print("\n==== PREPARAR AGENDAMENTO ========")
            _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
            retorno = preparaAgendamento(_b)
            input[retorno[1]]
        elif _a == '3':
            testesdeAmbiente()
