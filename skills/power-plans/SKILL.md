---
name: power-plans
description: >-
  Escreve o plano de implementação de uma feature já especificada quando o
  trabalho tem vários donos, contrato entre tarefas ou passo irreversível:
  níveis de complexidade, um dono por arquivo, contratos congelados, grafo de
  ondas e um gate antes do irreversível, na medida do risco (mínimo, parcial ou
  completo). Use quando a spec ou o design estiver fechado e o próximo passo for
  planejar, e ao ouvir "escreve o plano", "plano de implementação", "como a
  gente paraleliza isso", "divide entre os agentes", "prepara isso pra
  multi-agente". NÃO use para mudança delimitada que um agente faz sozinho, nem
  para protótipo, investigação ou pergunta: isso se faz direto, sem arquivo de
  plano. É o estado terminal de `spec-interview`. Escreve o plano, roda o
  pré-voo, para e pergunta: revisão externa ou commit e push. Quem sobe worker é
  `orchestrating-execute`, só a pedido explícito do usuário.
---

# Plano de implementação

## O que sai daqui

Um plano na medida do risco, e nada mais: nenhuma linha de código, nenhuma migração, nenhum worker
no ar. O plano não cita orquestrador e não nomeia modelo. Escreva no idioma do usuário.

**Este arquivo é o roteiro; o detalhe de cada fase mora em `references/`.** Ao entrar numa fase,
leia a referência dela. Depois de uma compactação de contexto só o começo deste arquivo volta
sozinho: releia a referência da fase em que você está antes de continuar.

| Fase | Leia |
| --- | --- |
| 1. Escala | `references/escala.md` |
| 2. Evidência | `references/evidencia.md`, `references/classes-de-erro.md` |
| 3. Decompor | `references/decompor.md`, `references/complexity-rubric.md` |
| 4. Grafo | `references/grafo.md` |
| 5. Gate e advisor | `references/gate-e-revisao.md` |
| 6. Fecho e registro | `references/fecho.md`, `references/registro-do-ciclo.md` |
| 7. Pré-voo | `references/pre-voo.md`, `references/auto-revisao.md` |
| 8. Revisão externa ou commit | `references/gate-e-revisao.md`, `references/external-review.md` |
| Esqueleto do plano | `references/plan-template.md` |

## 1. Escala: o menor aparato que ainda prova

Decida antes de escrever, e diga ao usuário qual escolheu e por quê.

| Escala | Quando | O que fazer |
| --- | --- | --- |
| **Direta** | Mudança delimitada, um dono: você lista os arquivos e a prova antes de começar, e ela se desfaz com um revert | Não é plano. Faça. Se ajudar, cinco linhas no chat |
| **Mínima** | Um defeito ou uma família, um dono da decisão, nenhum contrato novo entre tarefas. Pode ter migração ou deploy **se o projeto já tem portão próprio para isso** | Plano mínimo de uma tela. Sem ondas, sem gate, sem revisão externa |
| **Parcial** | Duas ou mais tarefas com donos diferentes, **ou** um contrato que uma tarefa produz e outra consome | Níveis, ownership e `Pronto quando` por tarefa. Sem ondas nem gate |
| **Completa** | Passo irreversível **sem** portão próprio do projeto, **ou** invariante de segurança, permissão ou isolamento entre clientes, **ou** trabalho de verdade paralelo, de vários agentes em arquivos disjuntos | Fases 2 a 8, com um gate antes do passo irreversível |

- **O critério é o risco, não a superfície.** Publicar se desfaz republicando. Migração ou deploy
  que já passa por um portão do projeto (roteiro com aval, script que recusa suíte vermelha) não
  sobe a escala sozinho: cite o portão no plano.
- **Na dúvida entre duas escalas, a menor.** Suba quando o motivo aparecer (um segundo dono, um
  contrato novo, um dado que não volta atrás) e diga que subiu. Escolher a maior "por segurança"
  é o erro mais comum desta skill: custa spec, plano, revisão e gate para uma mudança de um arquivo.
- **Teto de tamanho.** Plano mínimo cabe numa tela (umas 40 linhas); parcial, em umas 200. Em
  qualquer escala, plano mais evidência maior que o diff que ele planeja é sinal de duas famílias
  ou de sonda arquivada: recorte antes de entregar.
- **Um plano por família** (mesma causa, mesmo dono da decisão). Relatório com vários achados é
  recortado antes de escrever. Mais de uns dez requisitos, ou trilhas que a spec chama de
  independentes: recorte, ou pergunte ao usuário antes de escrever ("tudo junto" decide a
  entrega, não o número de planos).
- **Protótipo, investigação e pergunta de viabilidade não são plano.** Responda ou construa.

O **plano mínimo**, cada item com `arquivo:linha` ou consulta: (1) causa, com a evidência que a
mostra; (2) arquivos que mudam; (3) quem mais lê ou emite isto; (4) teste que falha com o fix
neutralizado; (5) camada de prova, a mais barata que exercita o consumidor real; (6) publicação e
rollback, citando o portão do projeto. Precisou de dois donos ou de contrato novo para escrever o
item 3: suba.

## 2. Evidência: do problema e da solução

- Leia a spec inteira, abra os arquivos que ela promete tocar e consulte o estado real do dado
  (schema, policy, **contagem**). Guarde o snapshot fora do repositório. Só é evidência o que outra
  pessoa refaz: a consulta, os parâmetros, o SHA e o resultado cru. Sonda exploratória não é.
- Bloqueador que você não reproduziu no código ou no dado é hipótese: escreva como hipótese.
- **Valide a spec para execução paralela:** contrato ausente, matriz de consumidores nas duas
  direções (quem lê e quem emite), decisão sem a alternativa descartada. Faltou, conserte a spec
  e diga ao usuário o que mudou. Conserto que define ou aperta o que o usuário vê (um termo de
  comportamento sem definição, dois requisitos que se contradizem) é pergunta a ele, não aviso.
- **Cenário de vários passos se percorre no código de hoje antes de virar tarefa** (classe 13):
  o estado em cada passo, e quem é dono da passagem entre o passo que emite e o que trata.
- **Todo fato do plano leva etiqueta:** `[MEDIDO: comando → resultado]`, `[LIDO: arquivo:linha]`
  ou `[SUPOSTO: o que o falsifica]`. Fato de que uma tarefa depende não fica suposto: meça agora,
  ou ele vira o primeiro passo da tarefa com "se der diferente, PARE e escale".
- Fato que sustenta uma decisão levada ao usuário mede-se **antes** de perguntar.
- Norma citada não é fato: regra de documentação que decide uma tarefa vira `[MEDIDO:]` contra o
  código antes de entrar no plano.
- **Afirmações de carga** (as que derrubam o desenho se forem falsas, quase sempre um "nunca", um
  "só" ou um "continua garantido") vão para a tabela do §0.1 com o falsificador em uma frase, a
  consulta que **conta** o falsificador no universo inteiro e o número, mesmo zero. Citação que
  confirma não fecha a linha, e amostra escolhida pelo defeito não refuta um "nunca".
- **Confira as classes de erro pelo nome** (`references/classes-de-erro.md`): semântica de campo;
  fix que é no-op; caso prometido que não dispara o critério; caminho ou comando que não existe;
  invariante prometida; emissores do que se remove; receita copiada; passo novo em pipeline; ação
  com vários executores; gatilhos do módulo substituído; peça nova em hospedeiro; "mesma função"
  sem paridade; fixture que o produtor não emite; log com leitor por tempo; escritor único;
  template global copiado no provisionamento; detector de texto; alvo único; privilégio herdado.
- O que não se decide no plano (escolha do modelo, interação entre peças que ainda não existem,
  corrida de tempo real) vai para a **watchlist**, com o método de verificação.
- Cenário escrito e não executado é hipótese. Vermelho e verde só contam com a causa inspecionada.
- **Fato externo é sonda, e sonda não se adia em silêncio.** Resposta de API de terceiro ou
  comportamento de modelo de que o desenho depende vira uma chamada real **antes** da primeira
  tarefa de código que o consome, como passo do coordenador. Adiar é decisão do usuário e fica
  escrita no plano: o que fica sem prova, e quais tarefas passam a carregar `[SUPOSTO:]`.

## 3. Decompor

- **Nível por tarefa** (complexa, média, baixa) pelo custo do erro somado à profundidade de
  raciocínio, nunca pelo tamanho. Na dúvida entre dois níveis, suba. O plano escreve
  `<MODELO_COMPLEXA>`, `<MODELO_MEDIA>`, `<MODELO_BAIXA>` e `<MODELO_GATE>`; quem atribui é o usuário.
- **Um arquivo, um dono.** Duas tarefas no mesmo arquivo: junte, parta o arquivo ou serialize.
  "Depois concilia" não é saída. Arquivo que todos só leem não é conflito: diga isso.
- **A matriz sai do traçado (§3.1), não da memória:** uma linha por requisito, uma coluna por
  salto (onde nasce, quem transporta, quem decide, quem emite, efeito observável), `arquivo:linha`
  em cada célula. Célula vazia é salto sem dono. A última coluna, quando é algo que uma pessoa vê,
  leva o arquivo que renderiza e o dono dele, não uma frase.
- **Entram na matriz:** o teste existente que afirma o comportamento que muda (reescrever e
  renomear, nunca apagar); a **fonte** de todo arquivo gerado, com o comando que regenera; e todo
  arquivo novo, com o irmão existente e a configuração que o descobre.
- Releia as descrições procurando a mesma responsabilidade em duas tarefas.
- **Contratos congelados antes da onda 1**, escritos literal em bloco de código, pelo coordenador:
  tipos, request e response, chaves, props de fronteira, fixture. Ordem de eventos também é
  contrato (estados, identidade da execução, quem confirma). Campo derivado tem tabela por origem.
  O contrato não é mais restrito que o requisito que implementa.
- **Leia cada regra do contrato contra as outras:** ação exigida sob uma condição que já não vale;
  duas exigências sobre o mesmo campo; comportamento de API externa "documentado" sem a
  documentação dizer; ação de código escondida numa tabela de riscos. Worker obediente não resolve
  contradição, escala.
- **`Pronto quando` é o cenário de aceitação do requisito, copiado da spec**, com a camada de prova
  mais barata que exercita o consumidor real e preserva o mecanismo sob risco (liste as peças reais
  e as simuladas). Tarefas em tabela compacta carregam as colunas `FR` e `Pronto quando`.
- Risco de ordem de eventos ou de integração: a primeira prova do percurso crítico roda na
  integração real assim que as dependências existem, antes de ampliar variantes.
- **Tela.** Tarefa que entrega interface com referência visual aprovada (spec §8.3) leva no
  `Pronto quando` a comparação lado a lado com a referência, estado a estado. O plano põe um passo
  do coordenador "comparação de tela" **antes** do passo que integra ou publica o front, e esse
  passo só roda com o arquivo de comparação de cada tarefa de tela presente. Spec com interface e
  sem referência visual nem dispensa registrada: volte à spec antes de planejar.

## 4. Grafo

- **Ondas são trilhas, não camadas.** Trilha é um grupo de tarefas ligadas por dependência, com
  poucas arestas para os outros grupos. A onda termina onde o coordenador precisa agir (git,
  migração, deploy, publicação).
- Trilha com mais de uma tarefa vira onda paralela com worktree e coordenador secundário, sempre
  que for seguro; quando não é, o §2.1 diz "Ondas paralelas: não, porque …". Dependência cruzada
  se resolve congelando em C0, com ponto de integração, ou movendo a consumidora. Não funda trilhas.
- Escreva sempre: o grafo em ASCII, o que roda junto, o que **não** roda junto com a razão de cada
  par, e o caminho crítico.
- **Estimativa em tokens, nunca em dias:** totais, de saída, e relógio ≈ saída do caminho crítico
  ÷ vazão do modelo, mais as esperas fixas. Sem teto fixo de workers.
- **Ordene por dependência de comportamento:** primeiro o aditivo e inerte, depois o que entrega,
  por último a chave que liga, reversível em uma linha. Passo de validação com item que você já
  sabe que vai falhar por causa de tarefa posterior: reordene.
- Com worktrees: tabela de papéis (só o principal integra, publica, roda ponta a ponta, migra e
  escreve em dado), arquivos que duas ondas tocam com o trecho de cada, ordem de integração, e o
  que a worktree nova precisa para nascer.

## 5. Gate e advisor

- **Um gate por plano**, sobre o candidato integrado, imediatamente antes do primeiro passo
  irreversível. Segundo gate só com segundo passo irreversível de superfície própria, ou produção
  em etapas decidida no plano. Nunca um por onda. Escala mínima e parcial: sem gate.
- Gate é tarefa com nível, dono e "bloqueia C<z>" no título. BLOQUEIA pede correção com teste, não
  segunda rodada.
- Declare o modelo e o orçamento do advisor na linha `Gate / Advisor`. No §7: aceitação
  observável, limites técnicos, tokens e saldo pago já autorizado, num estado corrente único.
- Revisão da spec ou do plano nunca é tarefa do grafo: nenhum `S0`, nenhum "bloqueia a onda 1".

## 6. Fecho do plano

- Passos do coordenador entre as ondas e depois da última, em ordem, com o comando. Termine com os
  portões de entrega do projeto e a documentação que acompanha a mudança no mesmo commit.
- **Saída de "em validação":** tipo de entrega (só interface, ou com backend), prazo (14 ou 30
  dias) e cron de verificação com os sinais de funcionamento e de bug. Mudança que envia algo a
  pessoas reais leva também uma leitura curta de 7 dias.
- **Registro do ciclo.** O plano termina com o bloco `## Registro do ciclo`
  (`references/registro-do-ciclo.md`), com a parte da spec e a do plano preenchidas agora. É o que
  permite medir depois se o processo melhorou; número que você não sabe é `nd`, nunca chute.
- Onde salvar: a convenção do projeto. Com pastas por estado, o plano nasce em "a fazer".

## 7. Pré-voo: antes de mostrar o plano a alguém

Quem escreveu o plano é o pior revisor dele, e pergunta de julgamento aprova o próprio texto. Por
isso a conferência é mecânica e de olhos novos, nesta ordem (`references/pre-voo.md`):

1. **`scripts/plan-lint.py <plano> --spec <spec>`**, na pasta desta skill. Erro se conserta, não se
   explica. Escala mínima com arquivo de plano para aqui.
2. **Verificador de contexto limpo** (parcial e completa): um agente que não escreveu o plano relê
   cada linha citada, roda de novo cada consulta de falsificador e faz o grep de quem lê e de quem
   emite o que muda. O brief está pronto na referência.
3. **Corrija no lugar.** Correção substitui o texto contradito, nunca é anexada embaixo dele.
   Anote os dois números no registro do ciclo.
4. A lista de julgamento que sobra está em `references/auto-revisao.md`.

## 8. Pare e pergunte: revisão externa ou commit e push

- Plano escrito, pré-voo limpo e nenhuma decisão do usuário em aberto: **pare, sem commitar.** Uma
  pergunta, duas opções, a recomendada primeiro.
- **Escala completa:** recomende a revisão externa, dizendo o que este plano tem de caro, e peça o
  modelo. **Mínima e parcial:** recomende commit e push; revisão externa só se o usuário pedir.
- Usuário já nomeou o modelo no pedido: rode sem perguntar. O modelo nomeado decide o mecanismo:
  subagente do harness, ou orquestração com terminal visível. Nunca headless, nunca troca
  silenciosa de modelo.
- **A revisão roda uma vez.** Nova rodada só com autorização explícita do usuário. Peça a refutação
  das afirmações de carga, nomeadas, e as regressões prováveis por tarefa; diga o que o revisor
  não tem.
- **Ao receber o relatório:** confira cada bloqueador você mesmo (recusar com prova também é
  triagem; aceitar tudo por deferência não é), separe o técnico da decisão de negócio, leve as
  decisões de negócio ao usuário numa rodada **antes** do commit, registre aceitos, recusados e o
  custo de cada um (documental, decisão, redesenho), e commite e dê push sem novo aval.
- Nenhum worker sobe daqui: implementar exige pedido explícito, e a skill é `orchestrating-execute`.

## Regras do projeto: de onde saem

Esta skill é genérica de propósito. Leia `CLAUDE.md` e `AGENTS.md` do projeto e
`.claude/plan-profile.md` se existir, procurando: o que subagente não pode rodar; se branch e
worktree só entram a pedido; como mudança de schema é aplicada e o que a torna irreversível; quais
são os portões de entrega (são eles que tiram um passo irreversível da escala completa); que
documentação acompanha a mudança; convenções de idioma, commit e nomeação. Sem esses arquivos,
pergunte ao usuário antes de escrever: essas respostas mudam o grafo.

## Documentação viva

Esta skill melhora com o uso, quando o ciclo mostrou um furo **dela** que custou e vai custar de novo.

- **Verificação antes de prosa.** Defeito que uma checagem mecânica pegaria vira checagem em
  `scripts/plan-lint.py` ou linha no brief do verificador, não parágrafo novo.
- **Este arquivo tem teto.** `scripts/check-skills.sh`, na raiz do plugin, recusa `SKILL.md` acima
  de 19 mil caracteres, porque o que passa disso some depois de uma compactação. Regra nova entra
  em uma linha aqui e o caso medido vai para `references/`. Melhore antes de acrescentar.
- **Conceito, não caso:** leia o `AGENTS.md` da raiz do plugin antes de escrever.
- **Escreva no clone git do plugin:** a pasta desta skill, se ela for um repositório git; senão o
  caminho gravado em `~/.config/planning-workflow/clone`. Sem nenhum dos dois, deixe o texto
  proposto no relatório.
- **Commit e push no mesmo trabalho:** rode `scripts/check-skills.sh`, commite só os caminhos que
  mudou, dê push na branch principal e rode `scripts/sync-harnesses.sh` se existir. Diga ao
  usuário o commit em uma linha. O histórico do git é o backup: desfazer é um `git revert`.
