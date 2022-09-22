#!/bin/bash
#Instalador de pacotes no Linux CentOS 5 ou 7 para o agendamento de tarifa.

echo "Instalador de pactes para o agendamento de tarifa"
echo "Instalando pacotes python3"
yum install python3 python3-psycopg2

echo "Instalar pacotes do postgres? (y/n)"
read x

if [ "$x" = "y" ]; then
	yum install postgresql postgresql-libs postgresql-devel
fi
echo "Pronto!"

