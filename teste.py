from subprocess import Popen, PIPE
from pathlib import Path, PosixPath, PurePath

# cwd = Path.cwd()
# host = 'localhost'
# port = '5432'
# user = 'postgres'
# password = 'postgres'

# PGPASS = Path.home()/'.pgpass'

# with PGPASS.open(mode='w') as arq: 
#     arq.write(f'\n{host}:{port}:*:{user}:{password}')
#     Popen(['chmod', '0600', PGPASS])

Popen(['psql', '-U', 'postgres', '-d', 'parkingplus', '-h', 'locahost', '-p', '5432',
'-c', 'SELECT * FROM lor LIMIT 1;'],
    cwd='/bin/', shell=True, stdin=PIPE)