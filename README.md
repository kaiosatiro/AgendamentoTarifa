<h1 align="center"> Agendador de Tarifas para o sistema *** </h1>

<p align="center">
<img src="https://img.shields.io/github/v/release/kaiosatiro/AgendamentoTarifa?label=version"/>
</p>
<p align="center">
<a href="https://www.codefactor.io/repository/github/kaiosatiro/agendamentotarifa">
<img src="https://www.codefactor.io/repository/github/kaiosatiro/agendamentotarifa/badge" alt="CodeFactor" /></a>
</p>


# <h2>Status</h2>

<h4 align="center"> 
    :construction: Em melhoria e desenvolvendo mais recursos :construction:
</h4>



# <h2>Índice </h2>

* [Descrição](#descrição)
* [Uso](#uso)
* [Tecnologias utilizadas](#tecnologias)
* [Atribuições](#licença)

# <h2>Descrição</h2>

Programa para automatizar o agendamento de mudança de tarifa no sistema ***

Foi pensado de forma a programar uma nova tarifa, de maneira SEGURA, no banco.
O agendamento da tarefa de execução é feita no sistema operacional, apontando o script gerado pelo programa.
Em caso de alguma falha durante o processo o programa desfará o processo (ROLLBACK) e retornará á configuração anterior.

# <h2>Uso</h2>
<b>*** Indico o programa ser salvo e executado na pasta "Raiz"\***\agendamento_tarifa ***</b>
1. Na garagem a ser agendado a tarifa, exporte os dados do tarifador e o carregue no computador que irá realizar as mudanças. Após configurado os futuros valores, executar o programa e escolher a opção <1>.
   <br> ![image](https://user-images.githubusercontent.com/87156189/192160425-f7d50660-bba6-4aee-b05e-8ccf3d52cee0.png)</br>
   O programa irá solicitar os dados de acesso ao servidor em três opções de detalhamento. 			
   Sendo a primeira opção para dados de acesso padrão em um localhost, a segunda para a digitação de TODOS os parâmetros, e a terceira para digitar apenas a senha em um localhost
   <br>![image](https://user-images.githubusercontent.com/87156189/192161455-804c7594-c676-46be-a9ce-92073bc5a24a.png)</br>
     Com os parâmetros irá criar uma tabela temporária, irá salvar os valores nela e irá realizar o DUMP a ser carregado no sistema da garagem.

2. No sistema do cliente (Windows Manager ou servidor Linux), salve o programa e o aquivo gerado por ele (TARIFA_NOVA), NO MESMO diretório.
   Execute o programa e escolha a opção (2).
   <br>  ![image](https://user-images.githubusercontent.com/87156189/192160899-5bd786d0-6832-476f-b69a-7c97afc5b515.png)</br>
   Após fonecer os parâmetros corretos, o programa irá carregar as novas configurações em uma tabela temporária e realizará um primeiro backup de segurança. 
   Após isso irá perguntar, para qual sistema operacional o Script deve ser gerado.
   <br>![image](https://user-images.githubusercontent.com/87156189/192161771-67bf7b1a-b8bf-4df8-aa6d-1eb58847626c.png)</br>
   Junto com o script do sistema escolhido, o programa irá gerar um segundo script de acordo com o sistema em que ele está sendo executado.             
   E por fim irá perguntar se o arquivo PGPASS, com a senha do servidor postgres, deve ser mantido salvo no sistema.
   <br>![image](https://user-images.githubusercontent.com/87156189/192162248-1060d27d-05d2-4983-95ca-369f7f547532.png)</br>

3.  Para atualizar a tarifa, escolha um dos dois scripts gerados pelo programa.

   1. O Script que tem o sistema operacional no final do nome, pode ser salvo em qualquer pasta e executado de forma independente, utilizando o agendandor de tarefas se for Windows ou o comando "at" no Linux. (No Linux tambem o crontab). Tambem não é necessário manter salvo o arquivo pgpass, pois o script utliza a varíavel de ambiente para se logar no banco. (Deve ser considerado a segurança de vizualização do password e o nivel de permissão de execução  no Linux)

      A vantagem desse método é simplicidade.

   2. O Script com nome simples "ScriptAtualizaTarifa", DEVE ser mantido no diretório em que foi gerado, JUNTO com o programa que o gerou. Este script acionará por linha de comando o programa TarifaAgendada, para que o mesmo faça a atualização da tarifa a partir da tabela temporária anteriormente preparada.

      ***<b>SE</b> for escolhido esse método, a etapa 2 <b>DEVE</b> ser feita no sistema operacional em que o Script será agendado. E o arquivo pgpass <b>DEVE</b> ser mantido no sistema.

      As vantagem desse método são:

      <ul>
          <li> Segurança do password. Considerando que o Script não guarda o password e depende do arquivo pgpass para acessar o banco. Tendo esse algum nível de segurança de acesso. (Ao menos no Linux)</li>
          <li> Segurança no procedimento. O programa ao ser acionado para atualizar a tarifa, realiza outro backup antes do procedimento, e faz uma checagem final da alteração, comparando o tamanho em kb da tabelas. 
          <b>SE</b> o backup falhar, a atualização não é feita. <b>SE</b> alguma parte do processo falhar, o backup é restaurado.</li>
          <li>Ao final do procedimento bem sucedido, o aquivo pgpass é deletado.</li>
      </ul>

      -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

      Todos os Scripts criam uma terceira tabela como tarifa_backup, para a possibilidade de "rollback" manual.

      Em Linux, deve se observar as permissões de execução do script. chmod.

      O procedimento de atualização só pode ser feito via execução de um script  ou linha de comando com os argumentos: 

      ​	--atualizar --host "host" --user "user" --port "port" --dbname "dbname"

      A terceira opção do menu inicial verifica se o ambiente tem as condições necessárias para o agendamento. Ou o teste tambem pode ser feito passando o argumento: 

      ​	--teste


# <h2>Tecnologias</h2>

<p align="left">
<img src="https://badges.aleen42.com/src/cli.svg"/>
</p>
<p align="left">
<img src="https://badges.aleen42.com/src/python.svg"/>
<ul>
  <li>subprocess</li>
  <li>argumentparser</li>
  <li>psycopg2</li>
  <li>pathlib</li>
</ul>
</p>
<p align="left">
<img src="https://camo.githubusercontent.com/281c069a2703e948b536500b9fd808cb4fb2496b3b66741db4013a2c89e91986/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f506f737467726553514c2d3331363139323f7374796c653d666f722d7468652d6261646765266c6f676f3d706f737467726573716c266c6f676f436f6c6f723d7768697465"/>
</p>
