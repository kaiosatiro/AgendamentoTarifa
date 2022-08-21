import psycopg2

host = 'localhost'
user = 'postgres'
port = '5432'
dbname = 'parkingplus'
password = 'postgres'

connection = psycopg2.connect(f'host={host} dbname={dbname} user={user} password={password} ')
cursor = connection.cursor()

try:
    cursor.execute("""
                    INSERT INTO agendamento_config_tarifa 
                        (tarifa, nometarifa, descontos)
                    VALUES (
                            (SELECT tarifa FROM config_tarifa),
                            (SELECT nometarifa FROM config_tarifa),
                            (SELECT descontos FROM config_tarifa)
                            )""")
except psycopg2.errors.OperationalError:
    connection.rollback()
    exit()
except psycopg2.DatabaseError:
    connection.rollback()
    exit()
else:
    connection.commit()