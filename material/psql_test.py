from subprocess import Popen, PIPE
from pathlib import Path, PurePath


def psql_test():
   host = 'localhost'
   user = 'postgres'
   port = '5432'
   dbname = 'parkingplus'
   password = '14bourbonsp'
   table = 'lot'
   psqldir = Path(f"/WPSBrasil/agendamento_tarifa")
   workdir = PurePath(psqldir)

   proc = Popen(['psql', '-U', user, '-d', dbname, '-h', host, '-p', port,'-c', f'SELECT * FROM {table} LIMIT 1;'],
                    stdin=PIPE)   
   proc.wait()


psql_test()