---
name: orchestrating-execute
description: >-
  Executa um plano de implementação multi-agente já escrito: pergunta ao usuário
  qual modelo vai em cada nível de complexidade, roda os passos que só o
  coordenador pode rodar, sobe os workers onda por onda respeitando o grafo,
  aceita cada entrega com casos próprios e para no gate antes de qualquer passo
  irreversível. Use quando existir um plano pronto e o usuário disser "vamos
  executar", "executa o plano", "sobe os workers", "dispara os agentes",
  "começa a onda 1", "roda isso em paralelo", "toca o plano X". Usa a skill
  `orchestration` do Orca para a mecânica. Se o plano ainda não existe, a skill
  é `power-plans`. Mudança delimitada que um agente faz sozinho não passa por
  aqui. Nunca é continuação automática de `power-plans`: só roda com pedido
  explícito do usuário.
---

# Executar um plano multi-agente

**Só com pedido explícito.** Plano escrito, revisado ou commitado não é pedido de implementação.

**Este arquivo é o roteiro; o detalhe de cada fase mora em `references/`.** Ao entrar numa fase,
leia a referência dela. Depois de uma compactação de contexto só o começo deste arquivo volta
sozinho: releia a referência da fase em que você está antes de continuar.

| Fase | Leia |
| --- | --- |
| 1. Preflight | `references/preflight-e-controle.md` |
| 2. Atribuição de modelo | `references/atribuicao-de-modelo.md` |
| 3. Despacho | `references/despacho.md`, índice de `references/orca-traps.md` |
| 4. Ondas e aceite | `references/aceite.md`, `references/ondas-em-worktrees.md` |
| 5. Gate, correção e advisor | `references/gate.md`, `references/correcao-pos-gate.md`, `references/advisor-regra.md`, `references/advisor.md` |
| 6. Medição que decide | `references/medicao.md` |
| 7. Fecho | `references/fecho.md` |

## Regras que valem a execução inteira

1. **O time é do usuário.** Modelo e esforço atribuídos por nível valem até o fim, reparos
   inclusive. Nunca introduza modelo que ele não listou: faltou cobrir um caso, pergunte.
2. **O irreversível é seu.** Git, mudança de schema, deploy e publicação são passos do
   coordenador. Worker não roda git.
3. **Toda entrega passa pelo seu aceite, com casos seus.** Teste verde do worker não é aceite, e o
   aceite não herda o alcance que o teste declara.
4. **Tela se aceita por comparação, não por ausência de defeito.** Tarefa que entrega interface
   com referência visual aprovada só é aceita com o arquivo de comparação lado a lado, e o front
   só é integrado ou publicado com esse arquivo presente para cada tarefa de tela. Aprovação do
   usuário sobre outra coisa (as artes, o backend) não é aceite de tela.
5. **Um gate, uma rodada.** BLOQUEIA vira triagem e correção com teste; o gate não roda de novo
   sem autorização explícita do usuário.
6. **Rumo:** decisão de negócio vai ao usuário, com resumo e recomendação. Freio técnico (segunda
   reprovação da mesma família, limite de candidatas ou de tentativas) vai ao advisor, no modelo
   do gate, com registro `ADV-n`. Contagem sozinha não vira pergunta ao usuário.
7. **Espera longa é visível.** Ao armar uma espera que pode passar de 15 minutos, diga ao usuário
   em uma linha o que espera, de quem, e quando olha de novo; e adiante o que não depende dela (a
   próxima etapa paralela, um aceite pendente, o registro). Coordenador em silêncio parece
   coordenador parado.
8. **Sonda de fato externo não se adia em silêncio.** Se o plano manda medir uma API ou um modelo
   de terceiro antes do código e o usuário adia, registre no documento do ciclo o que fica sem
   prova e marque `[SUPOSTO:]` nas tarefas que dependiam; a primeira chamada real vira o primeiro
   passo delas.
9. **Reparo é do modelo da tarefa.** Você conserta no aceite só o trivial, sem decisão de
   comportamento (um texto, uma linha), e registra. O resto volta ao worker, no mesmo terminal.
10. **Worker escala, não improvisa.** E você trata escalação na hora: worker escalando está parado.

## 1. Preflight

- Leia o plano inteiro. Ele precisa ter nível por tarefa, matriz de ownership, contratos escritos
  literal, grafo com os passos do coordenador e um `Pronto quando` por tarefa, copiado da spec.
  Faltou um deles: pare e volte para `power-plans`. Você não escreve critério de pronto de cabeça.
- **Rode de novo o `plan-lint.py` da skill `power-plans`.** O código andou desde que o plano foi
  escrito; erro novo é âncora deslocada, e se conserta no plano antes do primeiro despacho.
- Saiba quais arquivos modificados na árvore não são deste trabalho.
- Tarefa do grafo que revisa o próprio plano não é passo de execução: pule e diga que pulou.
- **Controle de avanço:** registre o comportamento observável de aceitação, os limites de
  candidatas e tentativas, a estimativa de tokens e o saldo pago já autorizado, num estado
  corrente único. Trocar SHA, worker ou sessão não zera tentativas.
- Lote com modelo estocástico não fecha em 100% por amostra: classifique cada vermelho (defeito
  que repete, ou variação) antes de abrir candidata. E verde não é aceite: leia as respostas.

## 2. Atribuição de modelo

- **Antes de criar qualquer terminal**, pergunte só o MODELO de Complexa, Média, Baixa,
  Gate / Advisor e, com ondas em worktrees, Coordenador de onda. Nunca assuma nem herde de outro
  plano. Atribuição por tarefa em vez de por nível: aceite. **Esforço não se pergunta** (regra do
  usuário, 10/11/2026): você decide pela regra abaixo, salvo o que ele nomear.
- Esforço nomeado pelo usuário vale para o ciclo inteiro, e esforço que ele fixou para um modelo
  (configuração, memória) também é nomeado. Sem isso, você escolhe por tarefa entre `medium` e
  `xhigh`: baixa e média em `medium` (`high` se a média produz contrato); complexa em `high`,
  `xhigh` só quando ela carrega o que o plano não pôde resolver. Gate e advisor: o nomeado; sem nome, o mais alto do CLI.
- **Smoke de cada modelo antes do primeiro terminal:** uma chamada de uma linha, no mesmo CLI do
  worker. Confira também a cota, quando o CLI a informa: cota no fim vira aviso ao usuário antes
  da onda, não troca de modelo no meio dela.
- **`--model` vai dentro do `--command`, e você confere** modelo e esforço no rodapé do TUI antes
  de despachar. Subiu errado: feche e recrie. Descobriu tarde: pare o worker, salve o diff,
  restaure os arquivos e refaça no modelo certo.

## 3. Despacho

- A mecânica (run, task com dependências, terminal, espera) é da skill `orchestration`: não a
  redocumente. Antes da primeira onda, leia o índice e a lista "leia sempre" de
  `references/orca-traps.md`; abra a armadilha quando o sintoma aparecer. Sem Orca, execute com o
  mecanismo de subagente que houver, mantendo ownership, ordem e gates.
- **Portão de capacidade:** nunca escreva no brief que o worker não pode algo sem ter provado.
  Rode o comando, leia a configuração do agente **do worker**, e escreva no brief a capacidade e o
  comando exato. Executou pelo worker o mesmo tipo de comando duas vezes: conserte o acesso dele.
- Ferramenta que você entrega ao worker lê só o segredo de que precisa.
- **Todo dispatch leva:** os caminhos da spec e do plano; a tarefa, pelo identificador; os
  arquivos dela, listados, e "nenhum fora desta lista"; os contratos que ela consome, colados
  literal; o que o projeto proíbe delegar; quem roda a verificação pesada; "escale em vez de
  improvisar"; e o `Pronto quando`, copiado do plano.
- Dado que um teste vai ler entra versionado antes do despacho.
- **A prova de neutralização só toca arquivo que o worker possui.** Se o alvo é de outro dono, a
  prova é sua, numa cópia isolada. Worker que morreu deixa a árvore suja até prova em contrário.

## 4. Ondas e aceite

- Suba no mesmo momento todos os workers cuja dependência já foi aceita. Uma tarefa sobe assim que
  o que ela espera foi aceito, sem aguardar as vizinhas.
- **A cada `worker_done`, sem esperar que peçam:** (1) leia o relatório e o diff, conferindo antes
  o **escopo**: arquivos alterados contra a lista do brief, e arquivo fora da lista é devolução;
  (2) aceite com casos seus e confira a prova de neutralização; (3) confira a task; (4) feche o
  terminal e a aba; (5) confirme na lista que o terminal sumiu. Não passou: task nova (`T<n>b`)
  no mesmo terminal, que só fecha no aceite da última.
- **Tela, em cada tarefa de interface com referência aprovada:** uma linha por estado que a
  tarefa toca (carregando, vazio, erro, resultado; computador e celular; o que se mexe, gravado),
  com a captura da implementação ao lado da prancha. Confira composição, não só defeito: onde a
  tela vive, navegação e item atual, imagens e exemplos, ordem e textos. Cada divergência vira
  correção ou adaptação aceita **pelo usuário**, por escrito. Grave tudo num arquivo de comparação
  por tarefa, na pasta do plano; o passo de integração do front começa conferindo que esses
  arquivos existem, e para se faltar um.
- Rode você mesmo os passos do coordenador de cada onda, e verifique antes de abrir a próxima.
- Com ondas em worktrees: você é o principal; só você integra, publica, roda ponta a ponta, migra
  e escreve em dado. O coordenador de onda entrega o branch local já em rebase, sem PR.

## 5. Gate, correção e advisor

- **Aceite** é contínuo e sem orçamento. **Gate** é uma cartada: um revisor só de leitura, em
  outro modelo, uma vez, sobre o candidato integrado, imediatamente antes do passo irreversível.
- **PASSA:** rode o passo. **BLOQUEIA:** triagem primeiro. Confirme cada achado no código e dê um
  de três vereditos: bloqueio real, real que não bloqueia (residual com dono, o usuário vê), ou
  refutado com a mesma prova que o gate teve de dar. Cada bloqueio vira correção com dono e com o
  teste que fica vermelho ao neutralizar; suíte e ponta a ponta verdes, rode o passo.
- O gate não roda de novo, e você não precisa de um PASSA dele para seguir. Teste que reprova
  depois da correção volta para correção, por `systematic-debugging`, nunca para o gate.
- Nunca rode o passo irreversível "enquanto o gate roda".
- **Correção pós-gate** (`references/correcao-pos-gate.md`): mesma família em arquivos diferentes
  pede um ponto de estrangulamento, não remendo por call site; contraexemplos do brief são piso,
  não teto; revisor que acusa o instrumento do teste pede arreio, não correção; teste negativo
  precisa de controle positivo; mudou enum, campo ou estado, o entregável inclui o inventário dos
  consumidores; toda afirmação sua sobre entrega alheia leva o comando que a provou.
- **Advisor**, só em três pontos: a correção pretendida muda o mecanismo; um achado ou uma
  escalação contradiz contrato congelado ou afirmação de carga; ou um freio técnico disparou. Uma
  consulta por veredito ou episódio, como task `ADV-n`, com o brief dizendo a direção que você
  pretende. Registre no documento do ciclo o que ele recomendou, o que você decidiu e a
  divergência, e mostre toda divergência ao usuário. A palavra final é sua; sem rastro, não.

## 6. Medição que decide

- **Vermelho na versão antiga integrada, verde no candidato.** Cenário que não falha na versão
  antiga não prova o fix; registre-o como regressão, nunca como vermelho e verde.
- Use o comando exato e o recorte de suíte que o gate ou o script de publicação roda: leia o
  script, não a memória.
- Meça onde o deploy instala: cópia limpa só do versionado mais os arquivos do candidato, com as
  dependências pelo lock, base e candidato no mesmo ambiente. Arquivo ignorado dá verde emprestado.
- Teste que vai ser congelado se lê contra o que a próxima tarefa vai mudar, antes de congelar.
- Lista fechada (o que publicar, quem chama) se recalcula por um segundo método independente, e
  as duas têm de bater.

## 7. Fecho

- Identificador de ordem escolhido no plano (versão de migração, número de sequência) envelhece:
  leia o último aplicado no destino antes do passo irreversível e renomeie se ficou atrás.
- Estage caminho por caminho e confira o que está estagiado. Nunca "adicione tudo".
- **Cron de verificação: nunca pendente.** Ele entra agendado no mesmo commit do fecho, com a
  prova de que a janela abre na data. Mudança que envia algo a pessoas reais leva também a leitura
  curta de 7 dias; se o plano não trouxe, acrescente e diga.
- **No fecho:** lint e testes você mesmo; mover plano e spec pelo tipo de entrega declarado;
  commit; responder os portões de entrega do projeto; documentação exigida no mesmo commit; fechar
  tasks e terminais; conferir que toda `ADV-n` tem registro; dizer o que ficou de fora.
- **Preencha a parte de execução do `## Registro do ciclo` do plano** (o bloco e as regras estão
  nas referências da skill `power-plans`, arquivo `registro-do-ciclo.md`): emendas de contrato, escalações, veredito e achados do gate,
  comparação de tela, sonda externa, tokens. Desconhecido é `nd`. Sem ele ninguém consegue medir
  se o processo melhorou.
- Depois de entregue, quem atender uma rodada de correção pedida pelo usuário soma em
  `depois_de_entregue` no mesmo bloco.
- Uma linha por skill do ciclo: o que entra em qual arquivo, ou "nada entra, porque X".

## Documentação viva

Esta skill melhora com o uso, quando a execução pagou na marra um furo **dela**.

- **Este arquivo tem teto.** `scripts/check-skills.sh`, na raiz do plugin, recusa `SKILL.md` acima
  de 19 mil caracteres, porque o que passa disso some depois de uma compactação. Regra nova entra
  em uma linha aqui e o caso medido vai para `references/`. Melhore antes de acrescentar.
- Armadilha nova do orquestrador ou de um CLI vai para `references/orca-traps.md`, com a linha
  dela no índice por sintoma. Armadilha de um projeto vai para o `AGENTS.md` do projeto.
- **Conceito, não caso:** leia o `AGENTS.md` da raiz do plugin antes de escrever.
- **Escreva no clone git do plugin:** a pasta desta skill, se ela for um repositório git; senão o
  caminho gravado em `~/.config/planning-workflow/clone`. Sem nenhum dos dois, deixe o texto
  proposto no relatório.
- **Commit e push no mesmo trabalho:** rode `scripts/check-skills.sh`, commite só os caminhos que
  mudou, dê push na branch principal e rode `scripts/sync-harnesses.sh` se existir. Diga ao
  usuário o commit em uma linha. O histórico do git é o backup: desfazer é um `git revert`.
