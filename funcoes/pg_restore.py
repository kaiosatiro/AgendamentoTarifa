from subprocess import Popen, PIPE
from pathlib import Path, PurePath

def pg_restore():
    version = 8.4
    psqldir = Path(f"C:/Program Files (x86)/PostgreSQL/{version}/bin/")
    workdir = PurePath(psqldir)
    filename = 'agendamento_config_tarifa'
    saveDir = Path(f"C:/Temp/{filename}")
    file = PurePath(saveDir)

    host = 'localhost'
    user = 'postgres'
    port = '5432'
    dbname = 'parkingplus'
    password = 'postgres'

    proc = Popen(['pg_restore', '--host', host, '--port', port, '--username', user, 
        '--dbname', dbname, '--verbose', str(file)],
       cwd=workdir, shell=True, stdin=PIPE)

    # proc.stdin.write(f'{password}\n')
    # return proc.communicate(bytes(password))
    proc.wait()

pg_restore()
# input()



