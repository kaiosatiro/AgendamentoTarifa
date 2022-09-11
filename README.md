Script para automatizar o agendamento de mudança de tarifa no sistema parkingplus da WPS.

É pensado para programar a nova tarifa de forma SEGURA, via banco.
O agendamento da tarefa de execução é feita no sistema operacional, apontando-o com os parâmetros corretos.
Em caso de alguma falha durante o processo o script desfará o processo (ROLLBACK) e retornará a configuração anterior.