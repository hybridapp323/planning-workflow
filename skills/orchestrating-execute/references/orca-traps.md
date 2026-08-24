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
# 2. Só então busque o corpo do relatório:
orca orchestration dispatch-show --task <task_id> --json
```

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
