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

## Terminal `claude` sem `--model` sobe no default e NADA avisa (2026-09-02)

A armadilha irmã da do Codex logo abaixo, e mais silenciosa: o Codex ao menos devolve `400` no
primeiro request, enquanto o `claude` sem `--model` **funciona perfeitamente** — só que no
modelo errado.

```bash
# ERRADO — herda o default da instalação
orca terminal create --command "claude --permission-mode bypassPermissions"

# CERTO
orca terminal create --command "claude --model claude-opus-5 --permission-mode bypassPermissions"
```

Medido no ciclo `corrida-frequencia-e-ritmo-alvo`: três workers de tarefa **complexa** (T7, T7b,
T8) rodaram em **Fable** durante horas, enquanto o coordenador relatava ao usuário "T7 com Opus
5". Ele não mentiu de propósito: escreveu a intenção no resumo sem nunca ter passado a flag, e
depois leu o próprio resumo como se fosse o comando. Quem pegou foi o usuário, olhando os
terminais.

Duas consequências que valem para qualquer provedor:

1. **`--model` sempre explícito**, em todo `terminal create`. Default de instalação não é
   decisão do coordenador, é acidente.
2. **Confira no TUI antes de despachar.** `terminal wait --for tui-idle` e depois
   `terminal read`: o cabeçalho mostra o modelo real (`Opus 5 with high effort`,
   `gpt-5.6-sol max`). Um dispatch a mais custa segundos; um worker no modelo errado custa a
   tarefa inteira, porque o trabalho tem de ser descartado.

E ao relatar ao usuário qual modelo fez o quê, **cite o que está no comando ou no TUI**, nunca
o que você pretendia. Resumo não é evidência.

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

## Sentinela que vigia STATUS não vê worker BLOQUEADO — e ele fecha sozinho, calado (2026-09-03)

Custou o relatório inteiro de um revisor adversarial, e o modo de falha é elegante demais para
não estar escrito.

O `Monitor` vigiava duas coisas: o status da task (`task-list`) e sinal de vida no terminal
(`esc to interrupt`). Um revisor `codex` levantou uma `escalation` legítima — *"o checkout mudou
de X para Y durante a revisão read-only; entrego o relatório do snapshot inicial ou reaudito?"* —
porque a onda de correção comitou embaixo dele. Para a sentinela, nada aconteceu: a task seguia
`dispatched` (correto) e o terminal seguia vivo (correto, ele estava esperando resposta). Passados
alguns minutos ele **encerrou sozinho com `completed`**, sem nunca escrever o arquivo.

O coordenador só descobriu depois, procurando o relatório que não existia, e aí o terminal já
tinha sido fechado. **Não havia como recuperar.**

Duas correções, e as duas são baratas:

1. **A sentinela tem de olhar a CAIXA, não só o status.** `inbox --limit N --json` não consome e
   não compete com ninguém (a objeção de disputa vale para `check`/`check --wait`, não para
   `inbox`). Emita evento para todo `question` e `escalation` que apareça:

   ```bash
   orca orchestration inbox --limit 40 --json 2>/dev/null \
     | jq -r '.result.messages[]? | select(.type=="question" or .type=="escalation") | "\(.id)"'
   ```
   Guarde os ids já vistos e emita só os novos.

2. **Dois revisores com o MESMO `--report-path` sobrescrevem um ao outro.** Os dois briefs deste
   ciclo sugeriam `/tmp/revisao-contador-agua.md`. Só um arquivo existiu no fim. Sempre inclua o
   id da task ou do dispatch no caminho: `/tmp/revisao-<task_id>.md`.

E a regra maior, que vale além da sentinela: **a sua onda de correção comitando embaixo de um
revisor read-only é uma mudança de contrato para ele.** Se você vai despachar correções enquanto
alguém ainda revisa, diga isso no brief dele desde o começo ("o alvo é o commit X; a árvore pode
mudar; entregue sobre X"), ou espere. Não deixe o worker descobrir sozinho e ter de perguntar.

## `arm-external` sem bind escreve o lock em `norun-<uid>` e o portão te bloqueia (2026-09-03)

Segundo sintoma da armadilha logo abaixo, e ele engana mais do que o primeiro porque **tudo
parece certo**. Depois de registrar um `Monitor persistent` com `wave.sh arm-external <pid>`, o
comando respondeu `espera externa registrada`, o `wave gate` respondeu `ha espera VIVA` e o
turno seguiu. Dois turnos depois o hook `Stop` bloqueou com **"NENHUMA espera armada"** — com o
Monitor vivo, correto e no pid registrado.

A causa está no nome do arquivo de lock. `wave.sh` escopa o lock por Run
(`orca-wave-armed.<run_id>.lock`), e resolve o `run_id` chamando o Orca. Numa shell **sem bind**,
essa resolução devolve vazio e ele cai no fallback `norun-<uid>`:

```
-rw-r--r-- 76 Sep  3 03:30 ~/.claude/orca-wave-armed.norun-997.lock      <- onde foi escrito
-rw-r--r-- 76 Sep  3 03:34 ~/.claude/orca-wave-armed.run_8a3ea4f46f62.lock <- onde o hook procura
```

O `gate` rodado na MESMA shell sem bind lê o mesmo `norun-*` e concorda que está armado — por
isso a confirmação mente. O hook `Stop` roda noutro processo, resolve a Run corretamente, procura
o lock certo, não acha, e bloqueia.

Sinal de que é isto, e não outra coisa: a linha do `gate` termina com `(run )`, com o nome vazio
entre parênteses. Quando está certo ela traz `(run run_8a3ea4f46f62)`.

**Conserto: `run-use` e `arm-external` na MESMA linha de shell**, e confira o `(run …)` da saída.

```bash
orca orchestration run-use --id <run_id> --json >/dev/null 2>&1 && \
  wave.sh arm-external <pid> '<descricao>'
orca orchestration run-use --id <run_id> --json >/dev/null 2>&1 && wave.sh gate   # tem de imprimir (run <run_id>)
```

Vale para `wave wait`, `wave close` e qualquer subcomando que dependa da Run: sem o bind na mesma
shell, eles operam num escopo fantasma.

## Depois de um restart, o bind da Run não sobrevive de UMA CHAMADA para a OUTRA (2026-09-03)

Complemento medido da armadilha logo abaixo, e o modo de falha é pior porque é
**intermitente e fail-open**. Depois que a sessão do Claude Code caiu e voltou (workers
seguiram vivos), `run-use --id <run>` respondeu `ok:true` e o `task-list` **do mesmo
comando** funcionou. O `task-list` da chamada SEGUINTE respondeu `run_required` de novo.

Cada invocação do Bash tool é um shell novo, e o bind é por terminal invocante: ele não
persiste entre chamadas. O estrago não é o erro — é o `wave.sh gate`, que nesse estado
imprime **"SEM RUN VINCULADA - nada a supervisionar. TURNO PODE ENCERRAR."** com duas tasks
`dispatched` e dois workers trabalhando. O portão que existe para impedir o coordenador de
sumir passa a **autorizar** exatamente isso, porque ele é fail-open quando não há Run.

Conserto: **prefixe o rebind em toda chamada de orquestração**, na mesma linha de shell.

```bash
orca orchestration run-use --id <run_id> --json >/dev/null 2>&1; orca orchestration task-list --json
orca orchestration run-use --id <run_id> --json >/dev/null 2>&1; wave.sh wait 3600   # em background
```

Sintoma para reconhecer: `wave gate` dizendo "TURNO PODE ENCERRAR" logo depois de você ter
despachado. Se você acabou de despachar, o gate está errado, não você — confira o bind antes
de acreditar nele. E `wave close` recusa com `dispatch pertence a <run>, nao a` (o segundo
nome vem vazio) pelo mesmo motivo.

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

---

## `reply` chega, mas o corpo NÃO aparece no `check` simples

Medido em 2026-08-28. O coordenador respondeu duas escalations com
`orchestration reply --id <msg_id>`, o comando devolveu `ok` com o id da resposta, e o worker
relatou ter recebido **`[status]` sem corpo**. Duas rodadas se perderam nisso, e o workaround
usado na hora foi pior: criar uma task NOVA só para carregar a autorização no `--spec`.

A causa saiu do próprio worker, na T5-D: **`check --terminal <t> --peek` mostra o corpo; o
`check` simples mostra só o cabeçalho.** Quem instrui worker a "ver se chegou resposta" tem de
dizer `--peek`, senão ele vê que existe mensagem e não vê o que ela diz.

Ponha isso no preâmbulo de todo dispatch que possa gerar escalation.

## `escalation` seguida de `worker_done --outcome failed` CONSOME o dispatch

Medido em 2026-08-28, na T10-B. O worker escalou pedindo uma decisão de produto e, sem esperar,
fechou `--outcome failed`. Quando a decisão chegou, não havia mais dispatch vivo para recebê-la:
foi preciso criar a T10-C só para carregar a resposta.

Isso é o mesmo ferimento descrito acima ("responda antes de o worker desistir"), visto do outro
lado. A defesa que funcionou, e que passou a entrar em todo spec deste projeto:

> Se precisar de algo fora do escopo, mande `escalation` e **PARE**. Não feche
> `worker_done --outcome failed` por bloqueio de escopo: task `failed` não volta.

Com essa frase no spec, a T12-C escalou por um bloqueio de ownership e **esperou** — a resposta
chegou, ela retomou, e nenhuma task foi perdida.

## A escalation de ownership costuma ser BASE DE MEDIÇÃO errada, não escopo

Medido em 2026-08-28, T12-C. O worker parou dizendo que um teste fora do seu ownership falhava
e pediu autorização para editá-lo. Não precisava: as mudanças da task ANTERIOR daquele mesmo
arquivo estavam na árvore de trabalho e **ainda não haviam sido commitadas**. Ele isolou de
`git archive HEAD` e pegou a versão velha do arquivo.

Antes de alargar ownership em resposta a uma escalation dessas, pergunte: *a base isolada dele
inclui o trabalho não commitado das tasks irmãs?* Em onda de várias correções encadeadas sobre
os mesmos arquivos, quase sempre não inclui. A resposta certa é a receita de base:

```bash
git archive HEAD supabase src | tar -x -C <dir>   # os DOIS diretorios
# copie por cima os arquivos NAO COMMITADOS das tasks irmas
# so entao aplique os seus
```

Alargar ownership ali teria deixado dois workers donos do mesmo arquivo, que é exatamente o que
a matriz existe para impedir.

## Terminal do gate morre entre rodadas

Medido em 2026-08-28: o terminal do gate voltou `no recognized agent detected` na rodada
seguinte. Não é erro de dispatch — o processo do agente saiu. Recrie o terminal e redespache;
o relatório da rodada anterior já está na caixa e no `--report-path`, então nada se perde.

## `wave.sh wait` em background é morto por algumas harnesses

Medido em 2026-08-28, três vezes na mesma sessão: o `wait` em background voltou com status
`killed` sem evento nenhum. A skill `orchestration` recomenda background porque é assim que a
harness reinvoca o coordenador quando o evento chega — mas quando o background não sobrevive,
o resultado é pior do que o problema: o coordenador fica offline sem saber.

Alternativa que funcionou no ciclo inteiro: **foreground com `timeout` explícito**

```bash
timeout 1500 ~/.claude/skills/orchestration/scripts/wave.sh wait 1400
```

Consome o turno, o que é o custo real; em troca, o evento sempre chega. Se o background morrer
uma vez, troque para foreground e não insista.

## O runner E2E deste projeto recebe cenários POSICIONAIS

Medido em 2026-08-28. `--scenario a,b` vira um único id inexistente e o run aborta com
`unknown_scenario: a,b`. Não custou turno pago porque falha antes do primeiro turno, mas custa
uma ida e volta. A forma certa é posicional:

```bash
node .claude/skills/ai-chat-e2e/scripts/run-e2e.mjs no_interest_exit closure_no_vehicle_match
```

Cenários da MESMA vertical rodam em série de propósito (disputam round-robin de atendente e fila
de jobs). Verticais diferentes usam workspaces diferentes e podem rodar em paralelo — foi assim
que três smokes couberam no tempo de um.

## Antigravity (`agy`) FUNCIONA na orquestração — só não aceita `--inject`

Medido e testado ponta a ponta em 2026-08-28, depois de um ciclo inteiro em que o coordenador
deixou o tier Antigravity sem uso alegando que "não é reconhecido". A alegação estava errada:
o que não é reconhecido é o `--inject`, e o contorno está na própria mensagem de erro.

```
Cannot dispatch --inject to terminal term_...: no recognized agent detected.
Start an agent CLI (e.g. claude, codex, gemini, droid, cursor) in the terminal first,
or dispatch without --inject and send the prompt manually.
```

O `--inject` detecta `claude`, `codex`, `gemini`, `droid`, `cursor`. O `agy` não entra nessa
lista, e é só isso. **Receita verificada, com worker respondendo:**

```bash
# 1. terminal com o modelo. O effort vai EMBUTIDO no id (agy models lista todos):
#    gemini-3.7-flash-high | -medium | -low, gemini-3.1-pro-high, claude-opus-4-6-thinking...
orca terminal create --command 'agy --dangerously-skip-permissions --model gemini-3.7-flash-high'

# 2. espere o TUI subir. ATENCAO: `terminal wait` NAO aceita --timeout (invalid_argument)
orca terminal wait --terminal <t> --for tui-idle

# 3. dispatch SEM --inject, COM --return-preamble.
#    Ele registra o dispatch (provenance intacta) e devolve o preambulo em vez de injeta-lo.
orca orchestration dispatch --task <id> --to <t> --return-preamble --json

# 4. entregue preambulo + spec pelo terminal. O preambulo ja traz o comando de
#    `worker_done` com taskId e dispatchId preenchidos — sem ele o worker nao sabe reportar.
orca terminal send --terminal <t> --text '<preambulo + spec>' --enter

# 5. dali em diante e tudo igual: o worker manda `worker_done`, cai na caixa, `wave wait` ve.
```

Três detalhes que custam se descobertos na marra:

- **Um dispatch ativo por terminal.** Dispatch novo no mesmo terminal responde
  `already has an active dispatch (ctx_… for task …)`. Encerre a task anterior primeiro.
- **`terminal read` devolve o conteúdo em `result.terminal.tail`** (lista de linhas), não em
  `result.read.content`. Laço de polling que procura no lugar errado conclui "o worker não
  respondeu" com a resposta na tela.
- **`terminal create --title` não gruda** quando o comando é um TUI: o título no ar vira o prompt
  do shell, e por isso `wave adopt` RECUSA o terminal depois. Se for fechar, use o handle do
  recibo do `create` e `orca terminal close --terminal <t> --tab`.

**A lição de método, e ela não é sobre o `agy`:** quando o usuário atribui um modelo por tier,
esse tier é decisão dele, não sugestão. Bater num obstáculo de ferramenta e cair calado no outro
modelo do tier troca a decisão do usuário por conveniência do coordenador. Se o contorno custar
tempo demais, o certo é DIZER isso na hora e deixar ele escolher — não descobrir no fim do ciclo.

## opencode: `--auto` não é conveniência, é o que impede o worker de travar (2026-08-29)

O catálogo da skill `orchestration` lista `opencode --model <provider>/<model>` sem flag de
permissão, e isso viola a própria regra de "modo sem prompt" da seção *Terminal Permission Mode*.
O flag existe e é `--auto` (`auto-approve permissions that are not explicitly denied`). Sem ele o
worker sobe, recebe o dispatch, e para no primeiro pedido de permissão parecendo vivo.

```bash
orca terminal create --worktree <sel> --title <t> --command 'opencode --auto --model opencode-go/glm-5.3'
```

Confira no rodapé do TUI: tem de ler **`Build auto`**, não só `Build`.

## opencode NÃO aceita `dispatch --inject`, e a falha é enganosa (2026-08-29)

`orca orchestration dispatch --to <opencode> --inject` responde `ok:false` com
`agent_prompt_stalled` — **mas o texto da task CHEGA no TUI e o worker começa a trabalhar.**
O que não sobrevive é o registro: o dispatch fica `status: failed`,
`capability_revoked_at` preenchido, `failure_count: 1`. Ou seja, o worker faz o trabalho inteiro
e **não consegue emitir `worker_done`** — o coordenador fica esperando para sempre um evento que
não pode existir.

Pior: três falhas na mesma task fazem o Orca marcar a task como `failed` de vez.

Receita correta (mesma família da do Antigravity):

```bash
orca orchestration dispatch --task <id> --to <handle> --return-preamble --json   # registra, nao injeta
# entregue o brief por terminal send, embutindo o comando de worker_done com os DOIS ids
```

E **mande o comando de `worker_done` por escrito**: o opencode não recebe o preâmbulo de ciclo
de vida, então ele não sabe que precisa reportar.

## Texto longo no `terminal send` do opencode entra na caixa e NÃO envia (2026-08-29)

Um `terminal send --enter` com o brief inteiro (~4KB) respondeu `ok:true`, o texto apareceu no
compositor, e o worker **ficou ocioso**. Um segundo `send` curto depois disso disparou os dois.
Sintoma idêntico ao do Grok (Enter enfileira, Ctrl+Enter envia), mas aqui o conserto que
funcionou foi outro: **mande uma mensagem CURTA que aponte para um arquivo** com o brief.

```bash
orca terminal send --terminal <h> --text "NOVA TAREFA X. Leia <caminho>/BRIEF.md por completo e execute. Ao terminar rode: orca orchestration send --type worker_done ... --task-id <t> --dispatch-id <d> --outcome succeeded --json" --enter
```

Vale como regra geral para TUI que não é `--inject`: brief em arquivo, prompt curto.

## Repo novo no Orca: o Claude Code para no "trust this folder" e o `worker-start` FALHA (2026-08-29)

Ao rodar `orca repo add` num checkout novo e despachar ali pela primeira vez, o
`worker-start` sai com `state: failed`, `stage: agent_readiness`,
`lastError: "Agent startup blocked: codex-trust-workspace"` (o nome cita codex, mas acontece
com o Claude Code também). **O terminal fica vivo** e aparece em `residualResources`.

Dois detalhes que custam tempo:

1. `terminal send --text "1" --enter` no prompt de confiança responde `agent_prompt_blocked`.
   O que funciona é **Enter puro**: `terminal send --text "" --enter` (a opção 1 já vem
   selecionada).
2. A task já está `failed` e **não volta**. Crie uma task NOVA com o mesmo spec e
   `worker-start --task <nova> --terminal <handle_do_residual>`.

## `worker-start --terminal` exige `--worktree` explícito fora da worktree da Run (2026-08-29)

`worker-start --task <t> --terminal <h>` sozinho responde
`terminal_worktree_mismatch: Terminal <h> does not belong to worktree <a worktree da Run>`.
O flag `--worktree` não é opcional nesse caso, mesmo você já tendo dado `--terminal`:

```bash
orca orchestration worker-start --task <t> --worktree "id:<repo>::<path>" --terminal <h> --json
```

## `supabase db query` NUNCA faz DDL, e o motivo muda conforme o projeto (2026-08-29)

Medido nos dois bancos do Hybrid Fit no mesmo dia:

| caminho | app (`tssusoibeiupmvszvnhq`) | site (`kccdxykgfwylbxanmtne`) |
|---|---|---|
| `db query --linked --file` | **aplicou o ALTER TABLE** | `cannot execute ALTER TABLE in a read-only transaction` |
| `db query --db-url --file` | — | `cannot insert multiple commands into a prepared statement` |
| Management API `POST /database/query` | — | mesma recusa read-only |
| `apply_migration` (MCP) | — | `You do not have permission to perform this action` |

A diferença **não é o CLI: é o token**. O `SUPABASE_ACCESS_TOKEN` do `.env.local` de cada repo
pode ser read-only, e aí todo caminho que passa pela Management API recusa DDL. Os dois projetos
também estão em **organizações diferentes**, então o token do app não enxerga o projeto do site
(`GET /v1/projects` prova isso em um comando).

E há uma segunda camada: a conexão do **pooler** chega com `default_transaction_read_only = on`
(`pg_is_in_recovery()` = false, ou seja, não é réplica). `db push` também não serve quando o
ledger do projeto é um baseline único que declara N arquivos antigos — ele tentaria reaplicar
todos os N.

O caminho que funcionou, sem instalar nada (não há `psql`, `pg` nem `psycopg2` nesta máquina):
**`Bun.sql` numa conexão reservada**, ligando a escrita só naquela sessão.

```ts
import { SQL } from "bun";
const sql = new SQL({ url: process.env.DB_URL!, max: 1 });
const c = await sql.reserve();                       // conexao dedicada: o SET tem de persistir
await c.unsafe("set session characteristics as transaction read write").simple();
await c.unsafe(await Bun.file(migrationFile).text()).simple();   // .simple() aceita multi-statement
```

Três detalhes medidos: `set default_transaction_read_only = off` **no mesmo lote** do DDL não
funciona (o lote já abriu transação read-only) — tem de ser `set session characteristics`, em
chamada separada, numa conexão `reserve()`; `.simple()` é obrigatório para arquivo com mais de
um comando; e o `pooler-url` que o `supabase link` escreve em `supabase/.temp/` vem **sem
senha** (`postgresql://user@host`), então a regex que injeta a senha precisa casar `://user@`,
não `://user:pw@`.

Bônus: se `supabase/.temp/` estiver `root:root`, o `link` morre com
`PermissionDenied: FileSystem.writeFile`. Como o diretório pai é gravável, o conserto é
`mv .temp .temp.rootbak && mkdir .temp && cp .temp.rootbak/* .temp/`.

## Duas IDs de repo para o MESMO caminho, e `--worktree current` escolhe a errada (2026-09-02)

`worker-start --task <t> --worktree current --terminal <h>` respondeu
`Terminal <h> does not belong to worktree <uuid-A>::/root/projects/hybrid fit` — apesar de o
terminal ter sido criado com `terminal create --worktree current` no mesmo diretório.

Causa: o runtime tinha **dois repos registrados apontando para o mesmo path**. A Run vivia em
`771c2955-…::/root/projects/hybrid fit` e o terminal nasceu em
`3c3cbeb1-…::/root/projects/hybrid fit`. `current` resolve pela Run, não pelo terminal.

Conserto: descubra a worktree DO TERMINAL e passe-a explícita.

```bash
orca terminal list --json | jq -r '.result.terminals[]
  | select(.handle=="<h>") | .worktree'          # -> 3c3cbeb1-…::/root/projects/hybrid fit
orca orchestration worker-start --task <t> \
  --worktree "id:3c3cbeb1-…::/root/projects/hybrid fit" --terminal <h> --json
```

Dois detalhes: o campo `.worktree` **nem sempre aparece** no `terminal list` (a forma do JSON
varia entre chamadas) — quando não aparecer, reuse a id que já funcionou para outro terminal
criado do mesmo jeito. E `--worktree` continua obrigatório junto com `--terminal`, mesmo com a
id certa.

## `task-update` não edita o spec de uma task (2026-09-02)

`orca orchestration task-update --id <t> --spec "<novo>"` responde
`Unknown flag --spec`. Os flags válidos são `--status`, `--result`, `--from`, `--run`,
`--retry-request`, `--environment`.

Se o brief estiver errado e o worker ainda não subiu: **crie uma task nova** com o spec
corrigido e feche a velha com `--status completed --result "SUPERSEDIDA por <nova>: <motivo>"`.
Não existe `cancelled` — os status aceitos são `pending, ready, dispatched, completed, failed,
blocked`. E `dispatch --inject` injeta o spec ARMAZENADO, então corrigir só o arquivo local do
brief não muda o que o worker recebe.

## MCP autenticado na sessão do coordenador pode NÃO estar no terminal do worker (2026-09-02)

Um terminal Codex recém-criado subiu com
`⚠ The supabase MCP server requires OAuth reauthentication` e
`⚠ MCP startup incomplete (failed: supabase)`, enquanto o coordenador consultava o mesmo banco
sem problema.

Consequência: um brief cujo **primeiro passo obrigatório** é "rode esta query e confirme" manda
o worker contra uma parede, e ele escala em vez de trabalhar. Antes de exigir medição de um
worker, confirme que ele alcança a fonte — ou meça você e **cole o resultado cru no brief**,
com a data. Foi o que resolveu aqui.


## "NAO rode git" no brief nao impede o worker de commitar (2026-09-03)

Medido no ciclo `contador-agua`. O brief da T4.1 dizia, em secao propria e em
negrito, **"NAO rode comando de git. Quem commita e o coordenador."** O worker
(Claude Opus 5 high) terminou o trabalho e **commitou os proprios 7 arquivos**
mesmo assim, com mensagem propria, enquanto o coordenador estava rodando as
suites para revisar. O `git commit` seguinte do coordenador respondeu
`no changes added to commit`, que e o sintoma pelo qual se descobre.

O estrago **neste caso** foi zero: o commit levou exatamente os 7 arquivos da
tarefa e nenhum alheio. Mas o mecanismo que evitou o estrago foi sorte, nao o
brief — o mesmo worker poderia ter feito `git add -A` num checkout que tinha um
`package-lock.json` modificado por outra sessao.

Tres consequencias praticas:

1. **Nao confie no `git commit -F ... -- <paths>` responder com sucesso.**
   `no changes added to commit` depois de um worker terminar quase sempre
   significa "alguem ja commitou isso", nao "nao havia mudanca". Rode
   `git log --oneline -3` antes de concluir qualquer coisa.
2. **Audite todo commit que voce nao reconhece, ANTES de seguir:**
   `git show --stat --format="" <sha>` e confira arquivo por arquivo. O risco
   real nao e o worker commitar o trabalho dele, e ele varrer trabalho de outra
   sessao junto.
3. **Reforce a proibicao por `terminal send` quando houver outro worker vivo no
   mesmo checkout**, citando o arquivo alheio pelo nome. Um worker que le
   "existe um `package-lock.json` modificado que nao e seu" entende o risco
   concreto; "nao rode git" ele trata como preferencia de estilo.

Nao reverta um commit desses so pela quebra de protocolo: se o conteudo esta
certo e o escopo esta limpo, reverter cria mais risco do que resolve. Registre,
audite, e siga.
