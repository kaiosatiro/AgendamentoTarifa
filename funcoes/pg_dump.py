from subprocess import Popen, PIPE
from pathlib import Path, PurePath


def pg_dump():
    version = 8.4
    psqldir = Path(f"C:/Program Files (x86)/PostgreSQL/{version}/bin/")
    workdir = PurePath(psqldir)
    filename = 'agendamento_config_tarifa'
    #saveDir = Path(f"C:/Temp/{filename}")
    saveDir = Path(f"{Path.cwd()}/{filename}")
    file = PurePath(saveDir)

    host = 'localhost'
    user = 'postgres'
    port = '5432'
    dbname = 'parkingplus'
    password = 'postgres'

    proc = Popen(['pg_dump', '--host', host, '-U', user, '-W', '--port', port,
     '--format', 'plain', '--verbose', '--file', str(file),
      '--table', 'public.agendamento_config_tarifa', dbname],
       cwd=workdir, shell=True, stdin=PIPE)

    # proc.stdin.write('postgres\n')
    # return proc.communicate()
    proc.wait()

pg_dump()
# input()