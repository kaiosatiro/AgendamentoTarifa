from argparse import ArgumentParser

parser = ArgumentParser(description='trigger')
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument('--atualizar', action='store_true')
group.add_argument('--teste', '-T', action='store_true')
parser.add_argument('--host', '-H', default='localhost')
parser.add_argument('--port', '-p', default='5432')
parser.add_argument('--user', '-U', default='postgres')
parser.add_argument('--dbname', '-db', default='parkingplus')
# parser.add_argument('--pgpass', '-pgp', default=pgpass)
# parser.add_argument('--workdir', '-wd', default=workdir)
# parser.add_argument('--backup', '-bkp', default=backup)

args = parser.parse_args()

if args.atualizar:
    print('Atualizou')
    print(args.atualizar)
    print(args._get_kwargs())
elif args.teste:
    print('Testou')
    print(args.teste)
    print(args._get_kwargs())
else:
    print('menu')

# host, user, port, dbname, pgpass, workdir, backup