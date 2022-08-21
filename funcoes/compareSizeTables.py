import psycopg2

host = 'localhost'
user = 'postgres'
port = '5432'
dbname = 'parkingplus'
password = 'postgres'

connection = psycopg2.connect(f'host={host} dbname={dbname} user={user} password={password} ')
cursor = connection.cursor()

cursor.execute("""
                SELECT relation, total_size FROM 
                    (SELECT relname AS "relation",
                            pg_size_pretty (pg_total_relation_size (C .oid)) AS "total_size"
                    FROM pg_class C
                    LEFT JOIN pg_namespace N ON (N.oid = C .relnamespace)
                    WHERE nspname NOT IN ('pg_catalog', 'information_schema')
                        AND C .relkind <> 'i' AND nspname !~ '^pg_toast')
                    AS tab 
                        WHERE relation LIKE '%config_tarifa%'
                    ORDER BY relation 
                """)
query = cursor.fetchall()

agendamento_config_tarifa_size = int(query[0][1][:2])
config_tarifa_size = int(query[1][1][:2])
print(config_tarifa_size == agendamento_config_tarifa_size)
