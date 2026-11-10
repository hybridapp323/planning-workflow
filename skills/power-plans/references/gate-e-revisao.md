# Gate e revisão externa (Fase 3)

Referência da skill `power-plans`. Leia ao posicionar o gate e ao terminar o plano: a pergunta final e o que fazer com o relatório do revisor.

## Fase 3 — gates

Um gate não é uma revisão. Revisão acontece depois e informa; gate acontece antes e bloqueia.

**Um gate por plano**, sobre o candidato integrado, imediatamente **antes** do primeiro passo
irreversível: aplicar migration em produção, deployar, publicar. Migration aplicada não tem `git
revert`, e uma revisão que chega depois disso só documenta o estrago. Um segundo gate só quando há
um segundo passo irreversível com superfície própria (uma publicação de frontend separada do
deploy de backend), ou quando o plano decide ir à produção em etapas porque uma onda corrige algo
ao vivo e não pode esperar as outras: aí é um gate por produção, com a razão escrita. Nunca um
gate por onda: o que guarda a onda é o aceite do coordenador
(`orchestrating-execute`, seção *Dois mecanismos de qualidade*). Escala parcial ou mínima: sem
gate. Medido em 20 e 21/09/2026: quatro ondas com um gate por onda rodaram cinco gates e nove
tarefas de correção; seis tarefas com um gate rodaram um, corrigiram com teste e publicaram na
mesma noite.

Um gate é uma tarefa como as outras, com nível, dono e dependência. O passo do coordenador que
ele guarda só acontece depois de o gate ter rodado e de as correções aceitas passarem na suíte e
no E2E. **BLOQUEIA não pede segunda rodada; pede correção com teste**, e teste que reprova volta
para correção, nunca para o gate. Escreva isso no plano com essas
palavras: "C<z> não acontece sem a aprovação do gate" é a frase que faz o executor chamar o
revisor de novo até ouvir PASSA.

**O plano declara o modelo e orçamento do advisor, sem agendar consulta.** Use o mesmo modelo
e esforço da linha `Gate / Advisor`. Além de mecanismo/contrato, limite técnico de candidatas,
tentativas ou esforço e segunda reprovação da mesma família acionam consulta automática,
sem perguntar ao usuário se deve insistir.

Em §7, declare aceitação observável, limites técnicos, tokens totais/saída/caminho crítico e
saldo pago já autorizado. Mantenha fonte, último aceite, falha/família, tentativas, consumo,
evidência e próximo passo em um estado corrente único. Trocar SHA/worker/sessão não zera
contadores. O advisor define o rumo e a prova offline antes da campanha completa; não autoriza
requisito novo, residual, ação irreversível ou quota adicional. Detalhe em
`orchestrating-execute`, seção O advisor e `references/advisor.md`.

### Revisão externa da spec e do plano: o agente para e pergunta, o usuário decide

Uma revisão externa read-only da spec e do plano, por outro agente ou outro modelo, antes de
executar, é **recomendada e opcional**. Quem decide se ela acontece, e com qual modelo, é o
usuário: no pedido que abriu o ciclo ("use tal modelo para a revisão adversarial") ou na pergunta
que encerra o plano. A skill recomenda; não agenda.

Por que recomendar: quem escreveu o plano é o pior revisor dele. Medido em 2026-08-26, num plano
com evidência medida, contratos congelados e auto-revisão feita, **a auto-revisão achou zero furos
e a revisão externa achou sete**, cinco confirmados no código, um deles capaz de mandar dado a um
contato sem identidade nenhuma. Medido em 2026-09-12: quatro bloqueadores, três documentais e uma
decisão do usuário. Medido em 2026-09-21: oito bloqueadores, todos confirmados no código e no
banco antes de qualquer linha escrita. Não foi falta de rigor na forma; confirmação e verificação
parecem iguais por dentro.

**Plano escrito: pare e pergunte, sem commitar antes.** Uma pergunta, duas opções (modal nativo
do harness quando houver), a recomendada primeiro:

1. **Revisão externa** — *"recomendo porque <o que este plano tem de caro: dado de produção, N
   tarefas em paralelo, invariante que ele promete preservar>; diga o modelo"*. Feature pequena:
   diga que não paga e recomende a opção 2.
2. **Commit e push** — spec e plano entram na branch principal sem revisão.

Se o usuário já pediu a revisão (e nomeou o modelo) no pedido que abriu o ciclo, essa é a resposta:
não pergunte, rode. Nada além destas duas opções acontece sozinho: nenhum worker, nenhuma
implementação. Implementar exige pedido explícito do usuário, e a skill então é
`orchestrating-execute`.

**Depois da resposta, sem nova parada:**

- **Commit e push:** registre "não solicitada" no §0.1, commite spec e plano juntos com caminhos
  explícitos (nunca "adicione tudo") e dê push na branch principal, seguindo a convenção de git do
  projeto. Relate os caminhos e o commit, e pare.
- **Revisão externa:** rode pelo procedimento de `references/external-review.md`. Ao receber o
  relatório, o coordenador o analisa como abaixo, decide o que entra e o que é recusado, aplica,
  registra no §0.1, e commita e dá push na branch principal **sem pedir aval**. A única parada
  antes do commit é decisão de negócio nascida da revisão (sem resposta técnica): essa vai ao
  usuário numa rodada, e o commit vem logo depois da resposta.

**O modelo nomeado decide o mecanismo, nunca o contrário.** Se o harness em que você roda
oferece esse modelo como subagente, despache a revisão como subagente, sem orquestrador. Se não
oferece (outro fornecedor, outro CLI, um agente do catálogo do orquestrador), a revisão sobe por
orquestração multi-agente: com Orca, a skill `orchestration` (terminal no CLI daquele agente,
task, dispatch, espera por `worker_done`), e confira no TUI que o modelo que subiu é o pedido,
como em `orchestrating-execute`. Sem mecanismo que alcance o modelo, diga isso ao usuário e
pergunte; nunca troque pelo modelo mais próximo que o harness tem. Troca silenciosa entrega
outra revisão com o nome da que ele pediu.

**Agente fora do harness sobe SEMPRE pela skill `orchestration`, nunca em modo headless.**
`codex exec` (ou outro CLI) rodando em segundo plano pelo shell alcança o modelo, mas o usuário não
vê o agente trabalhar nem pode intervir. Terminal visível no orquestrador é o mecanismo, não uma
opção.

**A revisão nunca entra no grafo do plano.** Não existe tarefa `S0 — revisão do plano`, nem
"bloqueia a onda 1". O executor lê o grafo como lista de trabalho, e uma revisão ali dentro vira a
primeira coisa que ele despacha, tenha o usuário pedido ou não. Medido em 2026-09-22: um plano com
a revisão no grafo, executado sem pedido de revisão, abriu o ciclo com um revisor no ar e nenhum
worker. Gate (`S<n>`) é outra coisa: revisa código já escrito, antes de um passo irreversível, e
mora na seção acima.

Duas coisas fazem a revisão render, e as duas custam pouco:

- **Peça a refutação das suas afirmações de carga, nomeadas.** Não mande "revise o plano".
  Liste as três ou quatro afirmações que sustentam o desenho e peça para tentarem derrubar cada
  uma, com `arquivo:linha`. Cada afirmação chega com a consulta do falsificador já rodada e a
  contagem dela; o que você pede é o que essa consulta não viu, não a primeira execução dela.
  A pergunta mais produtiva, sempre a última: *"o que está faltando
  aqui que eu não teria como notar, porque fui eu que escrevi?"*
- **Diga o que o revisor NÃO tem.** Se ele não tem acesso ao banco, ele vai marcar como
  hipótese aquilo que você consegue medir em uma query. Resolva essas hipóteses você mesmo em
  vez de descartá-las: foi assim que duas "hipóteses não verificadas" viraram fatos decisivos
  em 2026-08-26, uma confirmando um bloqueador e outra derrubando um risco inventado.

O veredito da revisão entra no plano, com o que foi aceito, o que foi recusado e por quê. Plano
revisado sem registro da revisão obriga a próxima pessoa a refazer o mesmo trabalho. Registre
também o custo de cada bloqueador aceito: documental, decisão do usuário ou redesenho. É esse
número, não o veredito, que diz se a spec e o plano estavam sãos.

Procedimento, mandato read-only, e como verificar depois que o revisor realmente não escreveu: `references/external-review.md`.

**Ao receber o relatório, não valide os bloqueadores por deferência.** Verifique cada um você mesmo, separe o que é buraco real do que é decisão de negócio, decida você o que é técnico (aceitar, recusar, redimensionar, com o porquê no §0.1), aplique o aceito reescrevendo no lugar o critério, o contrato ou o passo que ele contradiz, nunca como anexo embaixo do texto antigo (`references/external-review.md`, passo 5), e leve só as decisões de negócio ao usuário com resumo e recomendação, **numa rodada de perguntas antes do commit**: plano não é entregue nem commitado com decisão do usuário em aberto, nem como "pendente" com recomendação ao lado. Medido em 13/10/2026: um plano saiu commitado com duas decisões nascidas da revisão externa, e o usuário o recusou como não fechado. Um revisor competente ainda erra de tamanho: superdimensiona o que não tem usuário e subdimensiona o que já está quebrado.

### A revisão externa roda UMA vez. Nova rodada só com autorização explícita do usuário

**Regra dura:** a revisão adversarial de spec e plano roda **uma vez** por pedido do usuário.
Depois de incorporar os achados, commite e dê push (seção acima) e, no relato depois do push,
diga o que mudou e que outra rodada só roda se ele pedir. A pergunta não segura o commit. Nunca
despache a rodada 2 por conta própria, nem que o veredito tenha sido BLOQUEADO,
nem que a mudança tenha sido grande, e nem que o próprio plano, escrito por você, diga "rodada 2
antes do C0". Isso inclui não escrever no plano um gate de revisão repetida que o usuário não
pediu. Um revisor bloqueando não autoriza nada; quem autoriza nova rodada é o usuário. Os gates
**de implementação** do plano (ex.: S1, antes de migração e deploy) são outra coisa: estão no
plano que o usuário aprovou e rodam uma vez cada, com a mesma regra para repetição.

Medido em 22/09/2026: o usuário pediu uma revisão
adversarial da spec e do plano. Ela veio BLOQUEADA com 4 achados reais, todos incorporados. Em
seguida o coordenador escreveu no plano "rodada 2 antes do C0" e despachou sozinho uma segunda
revisão no modelo mais caro. O usuário interrompeu: *"eu não pedi pra rodar outra revisão, não
era pra você ter rodado"*. O certo era incorporar, commitar e relatar *"os 4 achados entraram
assim; outra rodada só se você pedir"*.
