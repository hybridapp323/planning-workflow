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
