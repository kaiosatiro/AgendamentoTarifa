from subprocess import Popen, PIPE
from pathlib import Path, PurePath

def psql_restore():
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

    truncate_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,
    '-c', 'TRUNCATE agendamento_config_tarifa'],
       cwd=workdir, shell=True, stdin=PIPE)
    truncate_proc.wait()

    psqlrestore_proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,
    '<', str(file)],
       cwd=workdir, shell=True, stdin=PIPE)
    psqlrestore_proc.wait()
    
    #return proc.communicate(bytes(password))
    

psql_restore()
# input()



