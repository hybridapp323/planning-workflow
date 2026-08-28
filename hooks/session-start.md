## Ciclo de trabalho — plugin `planning-workflow`

**Decida a skill antes da primeira ferramenta.** A checagem vem antes de explorar o código, antes de responder, e antes de fazer pergunta de esclarecimento — porque é a skill que diz *como* explorar e *o que* perguntar.

| Se o pedido é | Skill |
| --- | --- |
| Ideia, feature nova, componente novo, mudança de comportamento, escopo ainda aberto | `spec-interview` |
| Bug, teste falhando, erro, comportamento inesperado, "não funciona" | `systematic-debugging` |
| Spec pronta, o próximo passo é planejar a implementação | `power-plans` |
| Plano pronto, o próximo passo é executar | `orchestrating-execute` |

Se há chance real de uma delas se aplicar, invoque — e diga qual e por quê. Descobrir no meio do caminho que o pedido era maior do que parecia **sobe** para a skill; nada desce.

Estes pensamentos são racionalização, não análise:

- "isso é simples demais para precisar de processo";
- "deixa eu só olhar o código primeiro";
- "eu já sei o que fazer aqui";
- "preciso de mais contexto antes de decidir";
- "faço uma pergunta rápida antes".

Nada disso vale quando o usuário mandou explicitamente pular, ou quando você é um subagente executando uma tarefa já delimitada.
