from subprocess import Popen
from pathlib import Path, PurePath
from argparse import ArgumentParser
from time import strftime
from glob import glob
import psycopg2


# Script a ser executado pelo agendador de tarefas do sistema operacional
def salvaScript(host, user, port, dbname, password):
    query = '"DROP TABLE IF EXISTS tarifa_backup;CREATE TABLE tarifa_backup AS SELECT * FROM config_tarifa;BEGIN TRANSACTION;TRUNCATE config_tarifa;INSERT INTO config_tarifa  SELECT * FROM agendamento_config_tarifa;COMMIT;"'
    # Scripts para windows
    windows = {
        'nomeTeste': 'ScriptAtualizaTarifaTESTE.bat',
        'scriptTESTE': f'''::Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
C:/WPSBrasil/agendamento_tarifa/TarifAgendada.exe --teste >> %cwd%\ScriptAtualizaTarifaTESTELOG.log 2>&1
pause
''' ,
        'nome': 'ScriptAtualizaTarifa.bat',
        'script': f'''::Esse Script DEVE ser executado dentro da mesma pasta em que está o programa que o gerou.
C:/WPSBrasil/agendamento_tarifa/TarifAgendada.exe --atualizar --host {host} --user {user} --port {port} --dbname {dbname} >> %cwd%\ScriptAtualizaTarifaLOG.log 2>&1
''' ,
        'nome2': 'ScriptAtualizaTarifaWINDOWS.bat',
        'script2': f'''::Esse Script PODE ser executado sozinho
set PGPASSWORD={password}
set cwd=%~dp0
cd {PGWORKDIR}
psql -U {user} -d {dbname} -h {host} -p {port} -c {query} >> %cwd%\ScriptAtualizaTarifaLOG.log 2>&1
''' 
    }
    # Scripts para Linux
    linux = {
        'nomeOS5': 'ScriptAtualizaTarifaCentOS5.sh',
        'scriptOS5': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
psql -U {user} -d {dbname} -h {host} -p {port} -c {query} >> /WPSBrasil/agendamento_tarifa/ScriptAtualizaTarifaLOG.log 2>&1
''',
        'nomeOS7': 'ScriptAtualizaTarifaCentOS7.sh',
        'scriptOS7': f'''#!/bin/sh -xe
#Esse Script PODE ser executado sozinho
export PGPASSWORD={password}
docker exec -itd $(docker ps | grep db: | cut -d " " -f1) psql -U {user} -d {dbname} -h {host} -p {port} -c {query} >> /WPSBrasil/agendamento_tarifa/ScriptAtualizaTarifaLOG.log 2>&1
''' 
    }

    # Fonece as opções de sistema operacional
    while True:
        print("\n===== SALVAR SCRIPT PARA ==========")
        i = input("    1 <---- LINUX CentOS 7\n    2 <---- LINUX CentOS 5\n    3 <---- WINDOWS\n----> ")
        if i not in ('1', '2', '3'):
            input("Opção inválida!")
            continue
        if i in ('1', '2'):
            input('No Linux, LEMBRE-SE de executar o CHMOD no script')
        break

    if i == '1':
        nomearq = linux['nomeOS7']
        script = linux['scriptOS7']
    elif i == '2':
        nomearq == linux['nomeOS5']
        script == linux['scriptOS5']
    elif i == '3':
        nomearq = windows['nome2']
        script = windows['script2']

    nomearq2 = windows['nome']
    script2 = windows['script']
    nomeTeste = windows['nomeTeste']
    scriptTeste = windows['scriptTESTE']

    # Grava os scripts
    with open(nomearq, 'w') as arq: arq.write(script)
    with open(nomearq2, 'w') as arq2: arq2.write(script2)
    with open(nomeTeste, 'w') as arqT: arqT.write(scriptTeste)
    
    return True


# Função que compara os tamanhos das tabelas, como um dispositivo de segurança
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
        return True, 'OK'


# Funcoes PG_DUMP
def dump(host, user, port, dbname, filename, type, tablename):
    proc = Popen([PGWORKDIR/'pg_dump.exe', '--host', host, '-U', user, '--port', port,
            '--format', type, '--verbose', '--file', str(filename), '--table', tablename, dbname])
    proc.wait()
    return proc.returncode == 0


# Funcoes de RESTORE
def restore(tipo, host, user, dbname, port, filename, table):
    if tipo == 'pg_restore':
        proc = Popen([PGWORKDIR/'pg_restore.exe', '--clean', '--host', host, '--port', port, 
                    '--username', user, '--dbname', dbname, '--verbose', str(filename)])
        proc.wait()
    elif tipo == 'psql':
        truncate = Popen([PGWORKDIR/'psql.exe', '-U', user, '-d', dbname, '-h', host,
                            '-p', port,'-c', f'TRUNCATE {table}'])
        truncate.wait()
        proc = Popen([PGWORKDIR/'psql.exe', '-U', user, '-d', dbname, '-h', host,
                        '-p', port, '<', str(filename)])
        proc.wait()
    return proc.returncode == 0


# FUNCAO que coleta os parametros para acessar o banco
def parametrosBanco(op):
    if op not in ('1', '2', '3'):
        return False, "Opção inválida!"
    if op == '2':
        host = input('HOST: ')
        user = input('USER: ')
        port = input('PORT: ')
        dbname = input('BANCO: ')
        password = input('PASSWORD: ')
    else:
        host, user, port, dbname = 'localhost', 'postgres', '5432', 'parkingplus'
        if op == '1': password = 'postgres'
        else: password = input('PASSWORD: ')
    
    return host, user, port, dbname, password


# TAREFA QUE REALIZA O DUMP DA TARIFA ATUAL ======================================================
def baixaTarifaAtual(opcao):
    # Recebe os parametros do Banco
    parametros = parametrosBanco(opcao)
    if not parametros:
        return False, "Opção inválida!"
    else:
        host, user, port, dbname, password = parametros

    # Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}') # IMPORTANTE LOG ***

    # Realiza o DUMP da tarifa direto da config_tarifa
    tarifaAtual = PurePath(f"{CWD}/Tarifa_ATUAL")
    retorno = dump(host, user, port, dbname, tarifaAtual, 'custom', 'public.config_tarifa') # IMPORTANTE LOG ***
    PGPASS.unlink()
    if not retorno:
        return False, 'ERRO no dump da tabela'
    return True, 'Concluido'


# TAREFA QUE REALIZA O RESTORE DA TARIFA DIRETO NO BANCO ======================================================
def carregaTarifaDireto(opcao):
    # Recebe os parametros do Banco
    parametros = parametrosBanco(opcao)
    if not parametros:
        return False, "Opção inválida!"
    else:
        host, user, port, dbname, password = parametros

    # Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}') # IMPORTANTE LOG ***

    # Realiza o DUMP da tarifa direto da config_tarifa
    tarifaAtual = PurePath(f"{CWD}/Tarifa_ATUAL")
    retorno = restore('pg_restore', host, user, dbname, port, tarifaAtual, 'config_tarifa') # IMPORTANTE LOG ***
    PGPASS.unlink()
    if not retorno:
        return False, 'ERRO no carregamento da tarifa!'   # IMPORTANTE LOG ***
    return True, 'Concluido'
 

# TAREFA QUE REALIZA O DUMP DA TARIFA PARA SER AGENDADA ==========================================
def preparaTarifaNova(opcao):
    # Recebe os parametros do Banco
    parametros = parametrosBanco(opcao)
    if not parametros:
        return False, "Opção inválida!"
    else:
        host, user, port, dbname, password = parametros
    
    #Escreve o arquivo pgpass

    with PGPASS.open(mode='w') as arq:
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***
    
    #Cria a tabela agendamento e verifica a igualdade dos tamanhos
    try: 
        with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
            cursor = connection.cursor()
            retorno = criaTabelaAgendamento(connection, cursor)# IMPORTANTE LOG ***
            if not retorno[0]:
                return retorno
    except psycopg2.OperationalError:
        return False, 'Erro Operacional, provavel erro de SENHA'

    #Realiza o DUMP da tarifa a ser carregada no cliente
    tarifanovaName = PurePath(f"{CWD}/TARIFA_NOVA")
    retorno = dump(host, user, port, dbname, tarifanovaName, 'custom', 'public.agendamento_config_tarifa') # IMPORTANTE LOG ***
    if not retorno:
        return False, 'ERRO no dump da tabela'
    return True, 'Concluido'


# TAREFA QUE PREPARA O AGENDAMENTO DA NOVA TARIFA =======================================
def preparaAgendamento(opcao):
    #Recebe os parametros do Banco
    parametros = parametrosBanco(opcao)
    if not parametros:
        return False, "Opção inválida!"
    else:
        host, user, port, dbname, password = parametros

    #Escreve o arquivo pgpass
    with PGPASS.open(mode='w') as arq: 
        arq.write(f'\n{host}:{port}:*:{user}:{password}')# IMPORTANTE LOG ***

    #Backup de segurança
    backupname = PurePath(f"{CWD}/BACKUP_SEGURANCA_TARIFA_{DATE}")
    retorno = dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa')# IMPORTANTE LOG ***
    if not retorno:
        return False, 'ERRO no dump do BACKUP'

    #Criacao da tabela
    try:
        with psycopg2.connect(f'host={host} dbname={dbname} user={user}') as connection:
            cursor = connection.cursor()
            retorno = criaTabelaAgendamento(connection, cursor)
            if not retorno[0]:
                return retorno
    except psycopg2.OperationalError:
        return False, 'Erro Operacional, provavel erro de Senha'

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
    retorno = dump(host, user, port, dbname, backupname, 'custom', 'public.config_tarifa') # IMPORTANTE LOG ***
    if not retorno:
        return False, 'FALHA no dump do backup'
    if not Path(backupname).is_file():
        return False, 'FALHA, backup não encontrado antes da tarefa'

    #Atualizacao da tarifa
    print('Conectando ao banco para atualizar')
    try:
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
    except psycopg2.OperationalError:
        return False, 'Erro Operacional, provavel erro de Senha'

def testesdeAmbiente():
    #Testes de Postgres
    try:
        psql = Popen([PGWORKDIR/'psql.exe', '-V'])
        psql.wait()
        psql = psql.returncode == 0 #Valida o teste
    except NotADirectoryError:
        psql = False
    try:
        pg_dump = Popen([PGWORKDIR/'pg_dump.exe', '-V'])
        pg_dump.wait()
        pg_dump = pg_dump.returncode == 0 #Valida o teste
    except NotADirectoryError:
        pg_dump = False
    try:
        pg_restore = Popen([PGWORKDIR/'pg_restore.exe', '-V'])
        pg_restore.wait()
        pg_restore = pg_restore.returncode == 0 #Valida o teste
    except NotADirectoryError:
        pgpass = False
    #Testes de gravação
    try:
        with PGPASSTESTE.open(mode='w') as arq: 
            arq.write(f'\n::*::')
            pgpass = Path(PGPASSTESTE).is_file() #Valida o teste
        PGPASSTESTE.unlink()
    except PermissionError:
        pgpass = False #Valida o teste
    
    ok = '[ OK ]'
    errgrav = '[ ERRO ] > Erro na gravação do arquivo. Execute como Admnistrador'
    errpsql = "[ ERRO ] > binario não encontrado na pasta 'C:/Program Files (x86)/PostgreSQL/8.4/bin/'"

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
    PGPASS = Path.home()/'AppData'/'Roaming'/'postgresql'/'pgpass.conf'
    PGPASSTESTE = Path.home()/'AppData'/'Roaming'/'postgresql'/'pgpassteste.conf'

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
        else:
            print('Apagando o arquivo de script')
            scriptdir = Path('C:/WPSBrasil/agendamento_tarifa/TarifAgendada.exe')
            scriptdir.unlink()
    #Testes via linha de comando
    elif args.teste:
        testesdeAmbiente()

    #Opções em menu shell
    else:
        #Pesquisa do diretório do Postgres
        try:
            dir = r'C:\*Program*\PostgreSQL\???\bin\psql.*'
            psqldir = glob(dir, recursive=True)[0]
            pgworkdir = Path(psqldir).parent
        except IndexError:
            print()
            print('Diretorio do PostgreSQL não encontrado')
            print('Indique o diretório do binário psql.exe:')
            print('Exemplo: C:/Program Files (x86)/PostgreSQL/8.4/bin')
            psqldir = input('>')
            pgworkdir = Path(psqldir)
        #Diretorio dos binários do Postgres
        PGWORKDIR = PurePath(pgworkdir)
        print()
        print('* Realize os testes primeiro *')
        print('** O programa DEVE ser executado do diretório:')
        print('C:/WPSBrasil/agendamento_tarifa/')
        while True:
            _a = input("""
======= ESCOLHA A TAREFA ===========")
1 <---- Baixar a tarifa Atual
2 <---- Carregar tarifa
---
3 <---- Baixar tarifa NOVA para agendamento
4 <---- Preparar Agendamento
---
T <---- Testes!
Q <---- Sair...
---->"""
).upper()
            if _a not in ('1', '2', '3', '4', 'T', 'Q'):
                input("Opção inválida!")
            elif _a == '1': 
                print("\n======= BAIXAR A TARIFA ATUAL ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = baixaTarifaAtual(_b)
                input(retorno[1])
            elif _a == '2': 
                print("\n======= CARREGAR TARIFA ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = carregaTarifaDireto(_b)
                input(retorno[1])
            elif _a == '3':
                print("\n======= BAIXAR NOVA TARIFA A SER AGENDADA ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = preparaTarifaNova(_b)
                input(retorno[1])
            elif _a == '4':
                print("\n======= PREPARAR AGENDAMENTO ========")
                _b = input("    1 <---- Acesso Padrão\n    2 <---- Digitar\n    3 <---- Apenas Senha\n----> ")
                retorno = preparaAgendamento(_b)
                input(retorno[1])
            elif _a == 'T':
                testesdeAmbiente()
            elif _a == 'Q':
                break
