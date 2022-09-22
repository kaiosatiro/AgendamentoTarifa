from subprocess import Popen, PIPE
from pathlib import Path, PurePath


def pg_restore():
    psqldir = Path(f"/")
    workdir = PurePath(psqldir)

    filename = 'BACKUP_TARIFA_NOVA'
    #saveDir = Path(f"/WPSBrasil/agendamento_tarifa/{filename}")
    saveDir = Path(f"{Path.cwd()}/{filename}")
    file = PurePath(saveDir)

    host = 'localhost'
    user = 'postgres'
    port = '5432'
    dbname = 'parkingplus'
    password = 'postgres'
    table = 'agendamento_config_tarifa'

    proc = Popen(['pg_restore', '--host', host, '--port', port, '--username', user, 
        '--dbname', dbname, '--verbose', str(file)], stdin=PIPE)
    proc.wait()

pg_restore()




