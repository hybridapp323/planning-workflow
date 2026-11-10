## Ciclo de trabalho — plugin `planning-workflow`

**Comece pelo tamanho do pedido, não pela skill.** A maior parte dos pedidos não precisa de spec nem de plano.

| O pedido é | Faça |
| --- | --- |
| Mudança delimitada: você consegue dizer os arquivos e a prova antes de começar, e ela se desfaz com um revert | **Direto, sem skill.** Leia o que vai tocar, diga em 3 a 5 linhas o que vai fazer e como prova, e faça. Sem spec, sem arquivo de plano, sem revisão externa |
| Bug, teste falhando, erro, "não funciona" | `systematic-debugging` |
| Feature nova grande, subsistema novo, ou pedido com **escopo ainda aberto**: sobram várias decisões de produto que ninguém tomou | `spec-interview` |
| Spec fechada de trabalho com vários donos, contrato entre tarefas, ou passo irreversível sem portão próprio do projeto | `power-plans` |
| Plano pronto **e o usuário pediu explicitamente para executar** | `orchestrating-execute` |

Protótipo, investigação e pergunta ("dá pra…?", "como funciona…?") não abrem spec nem plano: responda, ou construa o protótipo. Pergunta sobre algo que parece quebrado ("por que não disparou?") é a linha do bug.

Falta **uma ou duas decisões** num pedido delimitado, mesmo que seja "qual dos dois caminhos"? Isso não é escopo aberto: pergunte numa mensagem só, com a sua recomendação, e siga direto, sem skill.

**Na dúvida entre dois caminhos, comece pelo mais leve e suba quando aparecer o motivo:** um segundo dono, um contrato que outra tarefa consome, um dado que não volta atrás. Diga que subiu e por quê. Tamanho do diff, número de arquivos e "é em produção" não são motivo.

- **Você está inflando se:** o documento que vai escrever é maior que a mudança; o usuário já descreveu o pedido por inteiro e você abre entrevista; o plano teria uma tarefa só.
- **Você está encolhendo se:** não sabe dizer o que fica de fora; a mudança mexe em dado que não se desfaz e o projeto não tem portão para isso; dois agentes vão trabalhar ao mesmo tempo.

Nada disso vale quando o usuário mandou usar ou pular uma skill, ou quando você é um subagente executando uma tarefa já delimitada.
