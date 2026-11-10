# Aceite, gate e correção pós-gate

Referência da skill `orchestrating-execute`. Leia antes de subir o gate e ao receber o veredito.

## Dois mecanismos de qualidade, e só um deles é o gate

**Aceite do coordenador** é contínuo, barato e sem orçamento. Todo `worker_done` passa por
você antes de contar como entregue: leia o diff, rode o `Pronto quando` com casos SEUS (nunca só
os do worker), confira a prova de neutralização. Não passou no rigor: devolva ao mesmo worker, no
mesmo terminal, com o que falta, quantas vezes precisar. Aceitou: confira a task e feche o
terminal na hora (*O que fazer a cada `worker_done`*, acima). Isso é coordenar, não é gate.
Medido em 20/09/2026: uma tarefa complexa aceita na terceira devolução custou duas devoluções ao
mesmo worker e nenhuma rodada de revisor.

**Aceite não herda o alcance declarado pelo teste.** Confira quais peças ele simula e
se alguma delas é justamente a fronteira sob risco. Etapas assíncronas executadas juntas
podem esconder uma corrida; iniciar do zero pode esconder defeito ao retornar com estado
preservado. Execute a primeira prova integrada prevista no plano com essas peças reais.
Registre candidato, cenário, resultado e limite: teste lógico aprovado e validação visual
pendente são estados diferentes. Sem a prova exigida para aquela etapa, a entrega é
parcial, não aceita; prova atribuída a uma etapa posterior permanece pendente nela.

**Gate** é uma cartada: um revisor read-only, em outro modelo, **uma vez**, sobre o candidato
integrado, imediatamente antes do passo irreversível que ele guarda (migration em produção,
deploy, publicação). Devolve PASSA ou BLOQUEIA, com a lista de achados provados. Decidido pelo
usuário em 12/09/2026 e reafirmado em 22/09/2026.

    ondas -> aceite por tarefa -> gate (uma vez) -> PASSA:    passo do coordenador
                                                 -> BLOQUEIA: triagem -> correções com teste -> aceite -> suíte + E2E -> verdes: passo do coordenador
                                                                                                                 -> falhou: correção -> suíte + E2E

- **PASSA:** rode o passo do coordenador.
- **BLOQUEIA:** primeiro a triagem (abaixo). Cada achado que ela confirma como bloqueio vira
  correção com dono e com o teste que fica vermelho ao neutralizar; você aceita cada correção com
  casos seus; suíte por nome e E2E (a prova ponta a ponta do plano, se o projeto tem) verdes: rode
  o passo do coordenador. **O gate não roda de novo, e você não precisa de um PASSA dele para
  seguir.** Corrigir o que o gate listou nunca reabre o gate, e o revisor não é chamado para
  conferir a própria lista.
- **Teste falhou é correção, não revisão.** Suíte ou E2E reprovando depois das correções volta
  para correção, em `systematic-debugging` (causa raiz, um conserto), e de novo para suíte e E2E;
  nunca para o gate. Três consertos falhados no mesmo teste viram questão de arquitetura, como
  aquela skill já manda.

**Triagem: você confirma cada achado no código antes de despachar.** O revisor leu o candidato
isolado; você tem o plano, as decisões do usuário e os riscos já aceitos. Uma linha por achado no
documento do ciclo:

| achado | reproduzido como (`arquivo:linha`, teste ou consulta) | veredito | dono |
| --- | --- | --- | --- |

O veredito é um de três. **Bloqueio real:** vira correção antes do passo irreversível. **Real,
não bloqueia:** residual com dono na watchlist, e o usuário vê. **Refutado:** com a evidência que o
derruba. Refutar exige a mesma prova que o gate teve de dar; descartar sem ela é como um aviso da
rodada 1 voltou como defeito duas rodadas depois (seção *O advisor*). Achado que contradiz decisão
do usuário registrada no plano não é bloqueio, é a decisão; vai ao usuário só se trouxer fato novo.

**Segunda rodada, só com autorização explícita do usuário.** Você só a propõe quando entrou
mudança grande que o plano não previa e que não nasceu de achado do gate (tarefa nova, escopo
novo, mudança de arquitetura), com o delta em uma linha; autorizada, a rodada é só sobre o delta.
**Correção de achado nunca é superfície nova**, mesmo quando cria módulo, muda contrato ou passa
por arquivo que o gate não leu: foi o gate que a pediu, e quem a prova é o teste e o E2E. Esse era
o furo da regra anterior, que aceitava "módulo novo" ou "contrato alterado" como motivo: a
correção estrutural que esta skill exige (um ponto de estrangulamento) quase sempre cria um ou
outro. Relatado pelo usuário em 27/09/2026: 8 rodadas extras de gate, e o tempo delas, pelo laço
gate → correção → gate.

Quantos gates: **um por plano**, antes do primeiro passo irreversível, sobre tudo que foi
integrado até ali. Um segundo só quando existe um segundo passo irreversível com superfície
própria (uma publicação de frontend separada do deploy de backend, por exemplo), ou numa produção
em etapas que o plano decidiu, um por produção. Nunca um por onda: quem guarda a onda é o aceite do coordenador. Plano de escala parcial ou mínima não tem
gate; aceite mais suíte.

Medido em 20 e 21/09/2026, três planos no mesmo repositório: quatro ondas com um gate por onda
rodaram **cinco** gates (um deles repetido "sobre o delta") e nove tarefas de correção; doze
tarefas com três gates planejados rodaram dois deles, uma vez cada, e o terceiro nem rodou
porque a tarefa que ele guardava foi cancelada; seis tarefas com **um gate, uma rodada** acharam
quatro críticos, corrigiram com teste, e publicaram na mesma noite. Nos dois últimos, ninguém
chamou o revisor de novo depois da correção, e nada disso voltou como defeito. Antes disso,
12/09 (três gates, nove rodadas) e 14/09 (sete rodadas, quem parou foi o usuário). O gate acha
muito na primeira rodada e cada vez menos nas seguintes; o que não converge é o laço, não a
revisão.

Nunca rode o passo irreversível "enquanto o gate roda". O ganho é minutos; a perda é migration
aplicada em produção sem `git revert`, ou deploy que republica módulo compartilhado de uma branch
atrasada. Revisão que volta com achados **não autoriza você a corrigir por conta própria**:
sintetize, decida quem é o dono da correção, e despache. Decisão de negócio vai ao usuário, com
resumo e recomendação.

O que protege o passo irreversível nesse desenho é a forma da correção: estrutural, num ponto de
estrangulamento, com o teste que trava o defeito. Remendo por call site sem teste era o que fazia
o gate ser chamado de novo. Como despachar essa correção: seção seguinte.

## Como despachar a correção pós-gate

Uma linha por lição. O caso que pagou cada uma, com a medição, está em
`references/correcao-pos-gate.md`; leia antes de escrever o primeiro brief de correção.

- **Mesma família de achado em arquivos diferentes:** proíba o remendo por call site e exija um
  ponto de estrangulamento. Sintoma: você escreve "e este caminho também precisa propagar X" pela
  terceira vez.
- **Contraexemplos no brief são piso, não teto:** o worker entrega a vizinhança adversarial dele
  e os testes dela, e a sua verificação usa casos que não são os dele.
- **O revisor acusou o INSTRUMENTO** (o teste não consegue observar a classe do defeito): a onda
  seguinte é arreio, do coordenador, não correção. Arreio executa o artefato de produção e é
  provado por neutralização antes de ser usado.
- **Teste negativo sem controle positivo não prova nada.**
- **Contrato "exatamente um de A ou B" com todo teste passando A e B:** a cardinalidade não está
  testada.
- **Mudou enum, campo de contrato ou estado:** o entregável inclui o inventário dos consumidores
  por `grep`, com decisão por consumidor; rótulo novo não muda comportamento.
- **Requisito de FORMA marcado bloqueante** (avaliar uma vez, persistir antes de enviar) vem com
  o teste que fica vermelho quando ele é desfeito.
- **Toda afirmação sua no documento do ciclo sobre entrega alheia** carrega o comando que a
  provou; sem ele é `[SUPOSTO:]`.
- **Freio técnico ou reprovação repetida:** consulte o advisor no mesmo modelo/esforço do gate
  e prove a recuperação offline antes de outro candidato. Contagem sozinha não vira pergunta
  ao usuário para insistir nem decisão de aceitar residuais.
