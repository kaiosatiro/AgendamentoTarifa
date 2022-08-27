
@echo off
::---------------------------------------------------
::SCRIPT para rodar a atualização da tarifa
::---------------------------------------------------
python "C:\Users\WPS0996\Documents\repositorio\TarifaAgendada\TarifaAgendada.py" --atualizar --host localhost --user postgres --port 5432 --dbname parkingplus
pause
