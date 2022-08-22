import psycopg2


host = 'localhost'
user = 'postgres'
port = '5432'
dbname = 'parkingplus'
password = 'postgres'
#password={password}
connection = psycopg2.connect(f'host={host} dbname={dbname} user={user}')
cursor = connection.cursor()

try:
    cursor.execute("""
                    CREATE TABLE public.agendamento_config_tarifa
                        (
                        tarifa bytea,
                        nometarifa bytea,
                        descontos bytea,
                        empresa bigint,
                        garagem bigint
                        )
                    WITH (OIDS=FALSE);
                    ALTER TABLE public.agendamento_config_tarifa OWNER TO postgres;""")
except psycopg2.errors.DuplicateTable:
    connection.rollback()
    cursor.execute('TRUNCATE agendamento_config_tarifa')
finally:
    connection.commit()
