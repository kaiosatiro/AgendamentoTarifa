from subprocess import Popen, PIPE
from pathlib import Path, PurePath


def pg_dump():
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
    tipo = 'custom'

    proc = Popen(['pg_dump', '--host', host, '-U', user, '-W', '--port', port,
     '--format', tipo, '--verbose', '--file', str(file),
      '--table', f'public.{table}', dbname], stdin=PIPE)
    proc.wait()


pg_dump()
