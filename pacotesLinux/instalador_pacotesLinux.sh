#!/bin/bash
#Instalador de pacotes no Linux CentOS 5 ou 7 para o agendamento de tarifa.
echo "Instalador de pactes para o agendamento de tarifa"

echo "Instalar pacotes 'python'? (y/n)"
read p
if [ "$p" = "y" ]; then
	yum install python3 python3-psycopg2
fi
echo "Python Pronto!"

echo "Instalar pacotes do 'postgres'? (y/n)"
read x
if [ "$x" = "y" ]; then
	yum install postgresql postgresql-libs postgresql-devel
fi
echo "Postgres Pronto!"

echo "Instalar agendador 'at'? (y/n)"
read a
if [ "$a" = "y" ]; then
	yum install at
fi
echo "at pronto!"
