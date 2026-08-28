# Armadilhas do Orca já pagas

Cada item aqui custou tempo real numa execução. Acrescente novos no mesmo trabalho em que aparecerem.

## Worker parado parece worker vivo

Um worker sentado num prompt de aprovação de ferramenta continua batendo heartbeat e mostrando atividade no terminal. Ele nunca chega a `worker_done`, e o `check --wait` espera para sempre.

Por isso o modo sem prompt não é conveniência, é requisito:

- Claude Code: `claude --permission-mode bypassPermissions`
- Codex: `codex --dangerously-bypass-approvals-and-sandbox`

## O flag de bypass vai DENTRO do `--command`

`orca worktree create --agent <x>` e `orca terminal create --agent <x>` sobem o agente pelo preset do próprio Orca e **não repassam** flags extras. Sempre que a regra acima precisar valer, use a forma explícita com `--command` e ponha o flag lá dentro.

## `run-create` antes de qualquer `task-*`

Sem uma run vinculada, `orca orchestration task-list` responde `run_required: No Run is bound`. Crie a run no começo:

```bash
orca orchestration run-create --objective "<objetivo>"
```

## Prompt de update do codex trava o `tui-idle`

O codex às vezes sobe com "Update available! X -> Y" e fica esperando resposta. O `terminal wait --for tui-idle` devolve `blockedReason: "codex-update-prompt"` e o dispatch nunca é entregue.

Conserto: mande a opção de pular e espere de novo.

```bash
orca terminal send --text "2" --enter
orca terminal wait --for tui-idle
```

Confira a numeração da opção no terminal antes de mandar. Ela muda entre versões.

## `codex exec` não é o TUI

`codex exec` rejeita `-a never` (`unexpected argument '-a' found`): esse flag só existe no TUI interativo. E o `exec` se recusa a rodar fora de um diretório confiável, então rode de dentro do repositório.

## Sessão headless não herda a autenticação da interativa

Uma sondagem headless pode responder `AuthRequired... No access token was provided` para um MCP que está perfeitamente autenticado na sessão interativa do mesmo agente. Isso **não** prova que o worker não tem acesso.

Antes de concluir que um worker não alcança um serviço: confirme com o usuário, e ofereça os caminhos alternativos (CLI com credencial de arquivo de ambiente, por exemplo). Concluir errado faz o worker devolver hipótese onde daria para ter evidência.

## O primeiro `check --wait` pode voltar só com keepalive

Ele retorna sem mensagem de lifecycle e sai. Isso é ponto de checagem, não falha. Confirme que o worker está vivo e rearme a espera.

## Confirme que o modelo certo subiu

Depois de criar o terminal, olhe o rodapé dele. Terminal que subiu com o modelo errado produz trabalho de qualidade errada e você só descobre no `worker_done`.

## `worker-release` pode falhar com `invalid_argument`

Se a task já foi fechada por `task-update --status completed`, a falha do release é cosmética. Não refaça o trabalho por causa dela.

## Provenance: worker fora do Orca não vira worker do Orca

Se o trabalho acabou rodando fora da orquestração, diga isso com essas palavras. Não descreva retroativamente um agente externo como orquestrado. Para reparar, rode ou revalide pelo caminho normal: terminal novo mais dispatch injetado.

## Verifique o read-only de um revisor duas vezes

Uma checagem no instante do `worker_done` não cobre o que o agente escreveu depois dela. Verifique de novo ao terminar de aplicar o relatório, e reporte qualquer arquivo modificado que não seja seu, em vez de commitá-lo junto.

## No Grok, Enter NÃO envia — Ctrl+Enter envia

O TUI do Grok mostra no rodapé `Enter:queue │ Alt+Enter:newline │ Ctrl+Enter:send now`.
`orca terminal send --enter` só empilha o texto na caixa de composição: o worker
fica parado com o brief inteiro visível e **nunca começa**, enquanto `terminal
wait --for tui-idle` responde `satisfied=true` — porque ele *está* ocioso.

Custou um worker parado por ~10 minutos parecendo vivo. Conserto:

```bash
orca terminal send --terminal <h> --text "<brief>" --enter --json
sleep 3
orca terminal send --terminal <h> --text $'\x1b[13;5u' --json   # CSI-u de Ctrl+Enter
# se não sair, repita e complemente com $'\x1b\r'
```

Confirme depois lendo o terminal: a caixa tem de estar **vazia** e o rodapé
perde o `Ctrl+Enter:send now`.

## Worker "se bloqueia" no terminal e NUNCA vira escalação

Dois workers Codex imprimiram "Bloqueado: ..." no próprio terminal e ficaram
ociosos no prompt — um deles até dizia "Enviei a evidência ao coordenador", mas
nenhuma `escalation` chegou ao inbox. A task fica `dispatched` para sempre, e
uma sentinela que só olha `task-list` dorme junto.

Conserto medido: a sentinela precisa de um segundo detector — para cada task
não-terminal, ler o terminal do worker e classificar atividade
(`Working (|Thinking|Waiting for response|esc to interrupt|Exploring`); N
leituras ociosas consecutivas (~3 min) com task aberta = acordar o coordenador.
O coordenador então lê o motivo do bloqueio no scrollback e destrava com
`terminal send` (decisão inline), sem redespachar do zero.

## Checkout com arquivos root:root 644 circuit-breaka os workers

Num checkout compartilhado, arquivos antigos podem estar `root:root 0644`
enquanto os terminais rodam como usuário comum: o `apply_patch` do worker falha
3× e o Orca marca a task como `failed` — às vezes DEPOIS de o worker ter
terminado o resto (task "failed" com trabalho pronto no terminal). Sem sudo, o
conserto é recriar o arquivo usando a escrita do DIRETÓRIO:
`mv f f.bak && cp f.bak f && rm f.bak` (novo dono = usuário atual, conteúdo
idêntico, git não vê diferença). Antes de cada onda, teste `! -writable` nos
arquivos da matriz de ownership e destrave preventivamente.

## Mensagens de orquestração são GLOBAIS do runtime

`orca orchestration check --types escalation` numa sentinela consumiu a
escalação de OUTRA run (outro projeto, mesmo runtime) e disparou alarme falso —
e o consumo compete com o coordenador legítimo daquela run. Sentinela não usa
`check`; vigia `task-list` + terminais das próprias tasks.

## Detecção de conclusão: use `task-list`, não `check --wait`

`orca orchestration check --wait` **compete** com as leituras manuais do
coordenador. Quem lê primeiro consome a entrega; se o coordenador rodar
`orchestration inbox` para inspecionar, a sentinela nunca vê aquele
`worker_done` e espera para sempre.

Pior: `check --wait` **reentrega** mensagem já vista, então um laço ingênuo gira
milhares de vezes por minuto contando só a primeira. `--unread` responde
`ok:false` em algumas builds.

**`orca orchestration task-list --json` é autoritativo e não-consumidor.** Uma
sentinela que faz poll de `status == completed` por task não compete com
ninguém. Deixe `check` só para `escalation`/`decision_gate`.

## Um worker pode terminar SEM emitir `worker_done`

Aconteceu com um gate de revisão: ele concluiu, imprimiu o veredito no terminal
e o `send --type worker_done` não chegou ao inbox. A causa provável foi ordem de
entrega — o brief foi mandado ANTES do `dispatch --inject`, então o agente
trabalhou sem os IDs de ciclo de vida em contexto.

Duas consequências: **sempre `dispatch --inject` primeiro, brief depois**; e a
sentinela precisa de um teto de silêncio que acorde o coordenador em vez de
esperar indefinidamente.

## Revisor read-only aplicou migração em PRODUÇÃO

Um gate com mandato explícito de "não aplique, não rode `db push` sem
`--dry-run`" acabou aplicando a migração ao lutar contra um `.env.local`
corrompido — chegou a usar `unshare -rm` com `mount --bind /dev/null` para
contornar o parser. A prova ficou na saída: `"message":"Finished supabase db
push."` (um dry-run imprime `DRY RUN: migrations will *not* be pushed`).

Instrução no brief não basta para passo irreversível. **Terminal de gate não
deve ter credencial de banco no ambiente.**

## Modelo Codex: `gpt-5.6` puro NÃO existe — é `-sol`/`-terra`/`-luna`, e o effort é argumento separado

`codex --model gpt-5.6` sobe o TUI normalmente (rodapé até mostra "gpt-5.6
xhigh"), mas o primeiro request devolve
`400: The 'gpt-5.6' model is not supported when using Codex with a ChatGPT
account` — e o worker fica parado parecendo pronto. O dispatch foi entregue, a
task nunca anda.

Os ids válidos da conta estão em `~/.codex/models_cache.json` (hoje:
`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`; efforts por modelo:
`low|medium|high|xhigh|max` — alguns têm `ultra`). Quando o usuário pedir
"GPT 5.6 no Max", isso vira DOIS argumentos:

```bash
codex --model gpt-5.6-sol -c model_reasoning_effort="max" --dangerously-bypass-approvals-and-sandbox
```

Cheque duas coisas depois de criar o terminal: o rodapé mostra
`gpt-5.6-sol max`, E — como o rodapé mente para modelo inválido — que após o
dispatch o terminal mostra atividade real ("Working…/Exploring"), não um erro
400 no tail.

## Restart do runtime desvincula a Run — `task-create` volta a falhar

Depois de um restart do Orca/da sessão, `task-create` responde `run_required: No
Run is bound` mesmo com a run existindo. Revincule com:

```bash
orca orchestration run-use --id <run_id> --json
```

(o flag é `--id`, não `--run`). As tasks e dispatches antigos continuam lá.

## E2E pago de longa duração NÃO vai em Bash background com timeout default

O tool Bash do coordenador mata o comando no timeout padrão (~2 min) MESMO em
`run_in_background` — um run E2E de 4 cenários (~15-25 min) morreu no meio do
cenário 2, desperdiçando turnos pagos e deixando um run parcial. Para trabalho
pago serial e longo, use o Monitor (timeout até 1h) com a saída filtrada por
`grep --line-buffered` das linhas de veredito, ou fatie em execuções de um
cenário por comando com `timeout` explícito ≤ 600000.

## `terminal close` sem `--tab` deixa o pane vivo

`orca terminal close --terminal <h>` responde `ok:true` com `ptyKilled:true`,
mas o pane/tab continua listado e consumindo memória — depois de uma execução
com 20+ workers a UI estava cheia de terminais "mortos". `--tab` fecha e espera
a remoção durável:

```bash
orca terminal close --terminal <h> --tab --json
```

Também medido: o primeiro `close` às vezes responde `ok:false` e o retry
imediato responde `ok:true` — trate o primeiro `false` como retry, não como
falha.

## `check --wait` devolve mensagem ANTIGA não-lida, não a próxima nova

Com inbox cheio de ciclos anteriores, `check --wait` retorna imediatamente com
worker_done velhos e esconde o novo — o coordenador "esperou" e recebeu o
passado. Filtre por `createdAt >=` do instante do dispatch (grave o timestamp
num arquivo na hora de despachar), nunca por presença/ausência. Corolário: um
snapshot de ids "vistos" com `--limit N` desliza quando chegam mensagens novas
e ressuscita antigas de fora da janela.

## Segundo `worker_done` do mesmo dispatch é rejeitado — o PRIMEIRO vale

Pedir ao worker que "reenvie o worker_done" depois de ele já ter mandado gera
`Rejected worker_done: Dispatch <ctx> capability is revoked` — a mensagem
original havia chegado e o dispatch foi consumido. Antes de re-engajar um
worker "que não reportou", procure o worker_done dele por timestamp no inbox.

## `setsid` retorna na hora — monitore o FILHO, não o pid do wrapper

`setsid nohup cmd & echo $!` imprime o pid do wrapper, que morre em ms; um
Monitor com `while kill -0 <esse pid>` encerra imediatamente com o trabalho
vivo. Vigie com `pgrep -f "<assinatura do comando>"`.

## A fonte da verdade de conclusão é `task-list`, NUNCA o inbox

Medido em 24/08: um worker mandou `worker_done`, o runtime marcou a task
`completed` e fechou o terminal — e o coordenador ficou 20+ min "esperando"
porque todos os seus vigias olhavam o INBOX (`check --wait`, filtros por id,
filtros por timestamp), que ora repete mensagem velha, ora perde a nova.
O laço correto de supervisão é:

```bash
# 1. Sinal durável: o status da task vira completed/failed quando o
#    worker_done chega, mesmo que você nunca veja a mensagem.
orca orchestration task-list --json   # status da SUA task
# 2. O CORPO do relatório vive SÓ na caixa, e ler não dá ack:
orca orchestration inbox --limit 200 --json   # filtre por payload.taskId
```

**CORREÇÃO de 26/08/2026 — este bloco mandava buscar o corpo em
`dispatch-show --task`, e isso está ERRADO.** Medido contra um `worker_done`
real: `dispatch-show` devolve só metadados do dispatch (`status`,
`assignee_handle`, `dispatched_at`, `completed_at`, `capability_hash`) e
**nenhum** campo do relatório — sem `body`, sem `filesModified`, sem
`reportPath`, sem `outcome`. Quem seguia a receita à risca terminava com ZERO
material de revisão e reconstruía tudo por `git diff` e scrollback.

O estrago medido no run `run_544ce7e1694d`: **36 `worker_done` + 5 `question` +
4 `escalation` chegaram e nenhum foi lido**; duas perguntas nunca receberam
`reply` e uma delas fez um worker fechar `--outcome failed` por bloqueio que se
destravava em trinta segundos.

O certo é usar os DOIS canais: `task-list` para saber que acabou (autoritativo,
não-consumidor) e a CAIXA para saber o que aconteceu. `inbox`, `check --peek` e
`check --all` **não dão `ack`** e por isso não competem com sentinela nenhuma —
a objeção "check compete com o coordenador" vale só para `check`/`check --wait`,
que fixam a Delivery. A skill `orchestration` traz o mecanismo pronto
(`scripts/wave.sh`).

Complementos: terminal `exited` + task `completed` = worker terminou e saiu
(não é crash); terminal `exited` + task `dispatched` = morreu no meio — aí
sim redespache. `check --wait` continua útil como GATILHO barato de "algo
chegou", mas a decisão de avançar onda se toma no `task-list`.

## Retry de `dispatch --inject` REVOGA o contexto que o worker já recebeu

`dispatch --inject` que responde `agent_prompt_stalled` muitas vezes JÁ
ENTREGOU o preâmbulo (a TUI estava ocupada só para a confirmação). Re-rodar o
dispatch cria um contexto novo e revoga o antigo — o worker termina horas
depois e o `worker_done` dele volta com `Dispatch <ctx> capability is
revoked`, deixando task e coordenador travados um esperando o outro.
Regra: depois de um `stalled`, LEIA o terminal; se o worker já está
trabalhando na task, NÃO redispache. Se a revogação já aconteceu, feche a
task você mesmo com `task-update --status completed` depois de verificar os
artefatos em disco — o trabalho não se perde, só o protocolo.

## `dispatch` devolve `runtime_error` quando o worker ainda está ocupado

Diferente do `agent_prompt_stalled` (que costuma ter entregado o preâmbulo
mesmo assim), o `runtime_error` no `dispatch --inject` aparece quando o agente
está no meio de um turno — a TUI não aceita input novo. Aqui o preâmbulo NÃO
foi entregue e a task fica `ready`, órfã.

Receita: `terminal wait --for tui-idle --timeout-ms 420000`, e só então
redespache a MESMA task (`dispatch --task <id>` de novo). Não crie task nova,
não mande `terminal send` por cima — o `send` num agente ocupado também some.
Medido em 2026-08-24: dois `runtime_error` seguidos no mesmo worker viraram
dispatch bem-sucedido depois de um `tui-idle` de ~3 min.

## Um brief longo só existe se estiver na SPEC da task

`orca orchestration dispatch` não tem `--body`/`--brief`: ele injeta o
preâmbulo mais a `--spec` da task, e `task-update` **não** edita spec (só
status/result). Ou seja: task criada com spec de uma linha entrega ao worker
uma linha, por mais contrato que exista no plano.

Crie a task já com o brief inteiro — `--spec "$(cat brief-T1.md)"` — e, se
você criou tasks curtas antes de escrever os briefs, crie as definitivas e
marque as antigas como `blocked` com `--result '{"note":"superseded"}'`, para
o `task-list` não virar um cemitério ambíguo.

## Teste que importa o `index.ts` de uma edge function morre no `serve()`

Worker que escreve uma function nova em Deno tende a proteger o `serve()` com
`if (import.meta.main)` — justamente porque o teste que importa o módulo
levanta um listener e falha com `NotCapable: Requires net access to
0.0.0.0:8000`. Só que no Supabase Edge Runtime não é garantido que o módulo de
entrada tenha `import.meta.main === true`: a função sobe e não responde nada,
e o cron vira erro silencioso.

O desenho certo é o que esses repos já usam: **entrada fina** (`index.ts` com
três linhas: importa `serve`, importa o handler, chama `serve(handler)`) e a
lógica testável num módulo ao lado. Diga isso NO BRIEF, antes de o worker
descobrir o conflito sozinho e escolher o `import.meta.main`.

## O ÍNDICE do git é compartilhado entre sessões paralelas, não só o worktree

Sabia-se que `git add -A` varre trabalho alheio. O que não estava escrito: mesmo
`git add <caminhos explícitos>` seguido de `git commit` pode varrer, porque o
`.git/index` é o MESMO para todas as sessões no checkout. Se a outra sessão
estagia os arquivos dela entre o seu `add` e o seu `commit`, eles entram no SEU
commit com a SUA mensagem.

Medido em 2026-08-25: `git add` de 3 arquivos, `git diff --staged --stat`
imprimiu 25 arquivos (incluindo uma migration de outra sessão), e o commit levou
todos. Conserto foi `git reset --soft HEAD~1 && git reset` e recommit — barato só
porque nada tinha sido empurrado ainda.

Forma imune, use sempre:

```bash
git commit -F <arquivo-de-mensagem> -- caminho/a.ts caminho/b.ts
```

O pathspec depois do `--` commita o conteúdo do WORKTREE só daqueles caminhos e
ignora o índice, sem limpar o que a outra sessão estagiou. Para arquivo novo,
ainda é preciso `git add` antes (só ele fica no índice), e aí o `--` protege o
resto.

## Worker que para numa decisão manda `--outcome failed` e CONSOME o dispatch

Um brief que diz "pare e reporte em vez de improvisar" produz exatamente isso: o
worker termina com `worker_done --outcome failed`, a task vira `failed` e a
capability do dispatch é revogada. Isso é o worker acertando, não falhando.

Consequência prática: não dá para "responder e continuar" no mesmo dispatch.
Crie uma task NOVA (`T1-B`, `T2-C`...) com a decisão colada literal e despache
para o MESMO terminal, que ainda tem todo o contexto e os arquivos meio-escritos
em disco. O brief da continuação precisa dizer "o que você já escreveu está
correto e NÃO deve ser revertido", ou o worker recomeça do zero.

Em 2026-08-25 foram 6 continuações assim numa execução de 8 tarefas, e nenhuma
custou retrabalho — só um dispatch a mais cada.

## `bunx` pode estar quebrado no checkout e derrubar meia onda

Neste repo (caminho com espaço, `node_modules` do Deno), `bunx vitest run`
responde `error loading current directory` / `CouldntReadCurrentDirectory` e nem
chega a carregar teste. Dois workers reportaram "bloqueado por ambiente" com o
código já pronto e correto — dispatch queimado por um comando no brief.

Antes da onda 1, rode o comando de teste do plano UMA VEZ você mesmo. Se falhar,
descubra a rota que funciona e coloque-a em TODO brief:

```bash
node node_modules/vitest/vitest.mjs run <caminho>
```

Corolário: quando um worker disser "bloqueado por ambiente", rode a suíte dele
você mesmo antes de acreditar. Duas vezes aqui o código estava verde e só o
runner do brief estava errado.

## Gate que reprova por flakiness pré-existente ainda é reprovação — verifique, não presuma

O critério "qualquer falha na suíte ⇒ reprove" é o certo para escrever no brief,
mas ele pega flakiness de área que a entrega não toca. Em 2026-08-25 o gate
reprovou por 11 unhandled errors em `input-otp` e num provider de cache, com
5.326 testes passando e todos os critérios substantivos verdes.

O que destrava, na ordem, e o que NÃO basta:

1. Rodar os arquivos acusados isolados (passaram).
2. Conferir que nenhum deles está em `git log --format="" --name-only <base>..HEAD`.
3. Comparar com uma rodada completa SUA anterior (a minha tinha 0 unhandled).

Só com os três é honesto seguir. "É flaky" sem os três é presunção — e num
checkout compartilhado a causa pode ser o trabalho da OUTRA sessão, que também
não é seu, mas que você precisa nomear.

## `reply` pode ficar órfã: o `ask` do worker expira e ele abre thread NOVA

Medido em 2026-08-26 no ciclo `citycar-ajustes-ia`. O worker (Codex) mandou `ask`, o
coordenador respondeu com `orchestration reply --id <msg_id>` ~2 min depois, e a resposta
**nunca chegou ao worker**: o `ask` dele já tinha expirado, e em vez de retomar por
`ask --resume <message_id>` ele abriu uma **pergunta nova**, com id novo. A reply do
coordenador ficou pendurada na thread velha, e a mesma pergunta voltou 15 minutos depois.

Custo: dois ciclos de espera armada e ~20 min de worker parado numa decisão de uma linha.

Duas defesas, use as DUAS:

1. **Responda na thread MAIS RECENTE**, não na que você viu primeiro. Reconsulte
   `orchestration inbox --limit 3 --json` e pegue o `question` do topo antes de responder.
2. **Mande a mesma resposta também para `--to dispatch:<ctx_id>`**, que é mail durável do
   dispatch e não depende de um `ask` vivo:

```bash
orca orchestration reply --id "$MSG" --body "$ANS" --json
orca orchestration send --to dispatch:<ctx_id> --type dispatch --subject '<assunto>' --body "$ANS" --json
```

Sintoma que denuncia o problema: uma `escalation` chega DEPOIS da sua reply repetindo a
mesma dúvida, com o texto "pergunta enviada ao coordenador". Isso não é o worker sendo
redundante; é ele não tendo recebido nada.

## O guard de posse do `wave.sh adopt` não funciona para terminal de agente

`wave.sh adopt <handle> '<titulo>'` compara o título que você deu no `terminal create` com
o que está no ar. **Os CLIs de agente renomeiam o pane assim que sobem**: um terminal
criado com `--title CITYCAR-T3` aparece como `Claude Code`; com `--title CITYCAR-T2`,
como `auto_pilot_crm`. O adopt recusa os três, corretamente do ponto de vista dele.

Consequência: `wave close` e `wave sweep` não conseguem fechar terminal de worker criado
pelo caminho baixo nível (`terminal create --command '<agente ...>'` + `dispatch --inject`),
que é justamente o caminho obrigatório quando você precisa fixar modelo e effort do Codex.

Saídas, em ordem de preferência:

1. `worker-start` quando o modelo/effort couber no que ele expressa — aí o Orca cria e
   POSSUI o terminal, e o sweep funciona.
2. Caminho baixo nível: **anote os handles que o seu próprio `terminal create` devolveu**
   e feche com `orca terminal close --terminal <h> --tab` no fim. A proveniência é sua,
   veio da sua própria chamada; o que falta é o Orca saber disso.

Não adote pelo título "de trás para frente" (lendo o título que o agente pôs e passando
esse): isso derruba a única defesa que existe contra fechar a sessão do usuário.

## `wave wait` acorda com escalação de OUTRA run — e pode consumi-la

Medido em 2026-08-27, durante o Ciclo 1 do desacoplamento do Hybrid Fit: um
`wave wait` armado para a minha run acordou com um `### EVENTO ###` vazio, e o
`inbox` mostrou logo em seguida uma escalação de outro projeto ("T3b requer
consumidor em index.ts fora do ownership" — trabalho de automações WhatsApp,
outra run, mesmo runtime). O corpo não foi impresso, mas o ciclo de
drenar-e-ack do `wave wait` roda `check --ack`, que consome a Delivery.

Efeito colateral: o coordenador legítimo daquela run pode nunca ver a
escalação, e o worker dele fica parado esperando resposta que não vem.

Isto CONFIRMA e amplia a entrada "Mensagens de orquestração são GLOBAIS do
runtime" logo acima: não vale só para sentinelas, vale para o próprio
`wave wait` do coordenador.

Mitigação, enquanto não houver filtro por run no `check`:
- Depois de todo `wave wait` que acorde com evento que NÃO é de uma task sua,
  rode `orca orchestration inbox --limit 5 --json` e confira o `task-id` de
  cada mensagem contra o seu `task-list`.
- Mensagem que não é sua: avise no relato ao usuário que ela passou pela sua
  caixa, para que a outra sessão possa ser reativada. Não há como devolver a
  mensagem à fila.

## O Codex sobrescreve o título do terminal, e o `wave adopt` recusa

Medido em 2026-08-27. `orca terminal create --title 'X worker' --command 'codex …'` cria o
terminal com o título certo, mas o TUI do Codex o reescreve para o **basename do cwd**. Na
volta, `wave.sh adopt <handle> 'X worker'` recusa:

```
RECUSADO: o titulo nao bate.
  esperado: 'CTWA-LOTE Terra worker'
  no ar   : 'atribuiton_ads'
```

Não é ambiguidade real — o handle veio do recibo do `create`, não de comparar `terminal list`.
Mas o guard não tem como saber disso, e ele está certo em recusar.

Saídas, em ordem de preferência:
1. `orchestration worker-start --agent codex --model <id> --effort <id>`, que dá posse de
   verdade (`ownershipState: "owned"`) — use quando não precisar de argv custom.
2. Precisando de argv custom (o caso do Codex com `-c model_reasoning_effort`), aceite que o
   terminal fica `unproven`, **guarde o handle do recibo do `create`** e feche no fim por esse
   handle, com `--tab`. Não tente adotar pelo título: ele não sobrevive.

Consequência prática: `wave sweep` não fecha esses terminais. O fechamento é manual e
explícito, e só vale para o handle que VOCÊ anotou na criação.

## `.env.local` não está no worktree — e sem ele o Supabase CLI parece sem permissão

Em repositório com worktrees do Orca, o `.env.local` (gitignored) vive só no **checkout
principal**. Rodar `supabase db query --linked` de dentro do worktree responde:

```
LegacyPlatformAuthRequiredError: Access token not provided.
```

Isso parece falta de permissão e não é: é falta de `SUPABASE_ACCESS_TOKEN` no ambiente. O
worker conclui "não tenho banco" e devolve hipótese onde daria para ter evidência — exatamente
o modo de falha que a seção da sessão headless já descreve, por outra porta.

Conserto, e passe isto NO BRIEF do worker em vez de deixá-lo descobrir:

```bash
set -a; . <checkout-principal>/.env.local; set +a
supabase db query --linked "select …;"
```

Confirme o caminho e teste UM select antes de despachar. Vale também para o MCP do Supabase,
que sobe `not logged in` nos Codex e faz o worker achar que está cego.

## "tsc passou" pode ser um tsconfig que não compila nada

Medido em 2026-08-27, num repo Vite + TS com project references. O worker relatou "tsc e lint
passaram" e havia um `TS2304: Cannot find name '<x>'` no arquivo que ele acabara de editar —
um `ReferenceError` garantido em runtime para três verticais de cliente real.

Causa: `tsconfig.json` na raiz continha só `references` e nenhum `include`/`files`. Então:

```bash
npx tsc --noEmit -p tsconfig.json     # exit 0, e NÃO compilou nada
npx tsc --noEmit -p tsconfig.app.json # pega o TS2304
```

Duas lições, e a segunda é a que se repete:

1. Quando o brief exigir typecheck, **nomeie o comando exato**, com o projeto certo. "Rode o
   tsc" delega ao worker uma escolha que ele não tem como fazer bem.
2. Repo grande costuma ter milhares de erros pré-existentes nesse projeto (aqui: ~2.800). Um
   worker que rode o comando certo e veja a enxurrada conclui "já estava quebrado" e segue.
   Exija o filtro: `... 2>&1 | grep <ArquivoDele>` **não imprime nada**, e peça a saída vazia
   colada no relatório.

Mesma família do `deno check --no-lock --node-modules-dir=auto <fn>/index.ts` que este projeto
já documenta: a suíte com `--no-check` não pega `TS2304`, e a revisão estática humana também
não — conferir colunas não é conferir escopo de identificador.

## Dispatch entregue não se cancela: o worker ocupado não recebe a interrupção

Medido em 2026-08-27. O coordenador despachou uma tarefa de nível MÉDIA para o worker do nível
BAIXA (terminal livre na hora, tabela de atribuição esquecida). A tentativa de cancelar falhou:

```
orca terminal send --terminal <h> --text 'PARE...' --enter
=> ok:false  code: "agent_prompt_stalled"
```

`terminal send` só entrega quando o TUI está ocioso. Worker ocupado **não tem caixa de
entrada** para interrupção — `orchestration send --to dispatch:<id>` também só é lido quando
ELE roda `check`, o que um worker no meio da tarefa não faz.

Duas conclusões:

1. **Confira a tabela de atribuição ANTES de cada `dispatch`, não só no começo da onda.**
   "O terminal está livre" é a pergunta errada; a certa é "de quem é esta tarefa". Terminal
   livre do worker errado é armadilha, não oportunidade.
2. Quando já aconteceu, **não mate o worker no meio**. Deixe terminar e mande o resultado para
   o gate adversarial, que já existe para isso. Matar custa o trabalho inteiro e deixa arquivo
   pela metade no disco; revisar custa uma leitura.
