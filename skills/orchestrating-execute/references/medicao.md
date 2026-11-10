# Medição que decide: cinco armadilhas

Referência da skill `orchestrating-execute`. Leia antes da medição do aceite final, do gate e do fecho.

## Prova ponta a ponta: o vermelho é na versão ANTIGA integrada

Neutralizar o fix no teste unitário prova a peça; não prova o fluxo. Quando o projeto tem
ambiente de homologação e cenário ponta a ponta, rode cada cenário do ciclo **duas vezes**: com a
versão anterior publicada lá (tem de falhar pela asserção do defeito, com a causa conferida) e
com o candidato (tem de passar). Só então publique em produção.

- O fluxo integrado acha o que a suíte não acha: um **segundo componente** que desfaz o fix
  depois dele, um teste unitário que **semeou** o estado que o fluxo real nunca produz, um
  caminho de dado que o teste isolado não percorre. Medido em 25/09/2026: quatro defeitos assim,
  todos com a suíte verde e o gate aprovado.
- Cenário que **não falha na versão antiga** não prova o fix. Refaça-o para exercitar o caminho
  do defeito; se o defeito depende de uma escolha do modelo que não se reproduz sob demanda,
  registre o cenário como regressão e diga que a prova é o teste unitário. Nunca o conte como
  vermelho/verde. No mesmo ciclo, 6 cenários não separavam as duas versões e foram refeitos, e
  outros 7 ficaram como regressão, com isso escrito no relatório.
- Cenário antigo que falha com o candidato por **exigir o comportamento que o ciclo removeu** é
  contrato velho: reescreva e renomeie (e registre por quê), nunca o apague nem o ignore.

## Medir com flag diferente da do gate é medir outra coisa

**A regra:** antes da medição que decide alguma coisa, **leia o comando exato que o gate roda** e
use ele. Não o comando que você lembra, não o do documento: o do script de publicação. Confira
também **qual recorte da suíte** ele roda.

Medido em 21/09/2026: a suíte completa, rodada com uma permissão a mais (herdada de uma sonda do
próprio coordenador), colheu 11 falhas em vez de 4. As extras eram todas de um teste que exige a
**ausência** daquela permissão. Um run inválido foi tratado como regressão por alguns minutos. No
mesmo ciclo, o gate de publicação rodava só um diretório, e as 4 falhas pré-existentes viviam
fora dele: o coordenador pediu ao usuário uma autorização que, medido, não era necessária.

## Medir nas dependências do checkout compartilhado é medir outra coisa

**A regra:** a medição que decide (a do aceite da onda e a do fecho) roda onde a publicação
instala, não onde você edita: uma cópia limpa do que está versionado, com as dependências
instaladas pelo arquivo de lock, recebendo os arquivos do candidato; a base e o candidato no
MESMO ambiente. Antes de chamar de regressão uma falha em arquivo que o ciclo não tocou, rode
esse arquivo na base e no candidato lado a lado. E não "conserte" a pasta de dependências
compartilhada sem pedir: outras sessões estão usando.

Medido em 24/09/2026, num frontend: a suíte completa no checkout deu 49 falhas contra 6 da base,
42 delas por tempo esgotado em arquivos que o ciclo não tocou. Parecia regressão. A pasta de
dependências do checkout compartilhado estava fora do lock (outra sessão tinha instalado sem
respeitá-lo), e a base tinha sido medida numa cópia limpa. Duas medições em ambientes
diferentes, uma falsa regressão.

**Arquivo ignorado é o mesmo verde emprestado, por outra porta.** O checkout de trabalho carrega
o que não vai para o commit: pastas ignoradas, saídas geradas, arquivos de outras sessões. Por
isso a medição que decide roda numa cópia montada só do versionado mais os arquivos do
candidato, **no aceite final, antes de subir o gate e antes do commit**, comparando por nome. A
lista do candidato sai do que vai ser commitado (o diff rastreado mais os arquivos novos não
ignorados), nunca de uma cópia da árvore. Medido em 02/10/2026: dados de calibração entregues aos
workers numa pasta ignorada, testes que os liam, suíte verde no checkout em todas as rodadas de
aceite; na cópia limpa, quatro arquivos de teste não carregavam. Quem achou foi o gate. Sintoma:
falha de carregamento por arquivo inexistente que só aparece na cópia limpa.

## Teste congelado tem de sobreviver à tarefa que vem depois

**A regra:** no aceite de um teste que vai ser congelado, leia-o contra o que a PRÓXIMA tarefa
vai mudar: simulação que responde por tabela e aplica os filtros (não por ordem de chamada),
entrada desconhecida devolvendo vazio, espera por condição ou com folga larga (não por contagem
justa de passos), e asserção só no que tem de sobreviver. O que precisar mudar muda antes do
congelamento, com o hash registrado.

Medido em 24/09/2026: o plano congelava um teste de caracterização que esperava a carga com um
número fixo de passos assíncronos, e a tarefa seguinte ia acrescentar buscas encadeadas, ou seja,
ia quebrá-lo sem mudar nenhum resultado. O coordenador percebeu na leitura do aceite e aumentou
a margem ANTES de congelar. Depois de congelado, a única saída seria a tarefa seguinte editar o
teste que existia para vigiá-la.

## Lista de publicação calculada por UM método é hipótese

**A regra:** quando o brief do gate pede uma lista fechada (o que publicar, arquivos a tocar,
chamadores a atualizar), peça-a **recalculada de forma independente** e escreva no brief que
**as duas têm de bater**. Divergência não é discordância de opinião: é um dos dois métodos com
ponto cego, e vale mais que a revisão de código que veio junto.

Medido em 21/09/2026: um script do coordenador calculou o fecho transitivo de quem importava um
módulo compartilhado alterado e devolveu 12 unidades a publicar. O gate, por conta própria, deu
13. O script não reconhecia importação dinâmica, e a unidade que sumia alcançava o módulo por
uma cadeia de sete saltos terminando numa delas. Publicar sem ela deixaria uma cópia velha do
módulo embutida em produção, em silêncio.
