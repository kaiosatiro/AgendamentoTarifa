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
                    UPDATE config_tarifa 
                    SET
                        tarifa = (SELECT tarifa FROM agendamento_config_tarifa),
			            nometarifa = (SELECT nometarifa FROM agendamento_config_tarifa),
			            descontos = (SELECT descontos FROM agendamento_config_tarifa)
                    """)
except psycopg2.errors.OperationalError:
    connection.rollback()
    exit()
except psycopg2.DatabaseError:
    connection.rollback()
    exit()
else:
    connection.commit()
    