# Passos do coordenador, cron de verificação e fecho

Referência da skill `orchestrating-execute`. Leia antes de qualquer passo irreversível e ao encerrar o ciclo.

## Passos que são sempre seus

Descubra no `CLAUDE.md` / `AGENTS.md` do projeto o que não se delega. Quase sempre inclui:

- git: `add` com caminhos explícitos, `commit`, `push`;
- aplicar mudança de schema;
- deploy de função ou serviço;
- publicação para usuário.

Estes são os passos que definem onde as ondas quebram. Se você se pegar delegando um deles, o grafo do plano estava errado, não o projeto.

Com ondas em worktrees separadas, "seus" quer dizer do coordenador principal. O coordenador de onda
commita no próprio branch e concilia o rebase; push, integração na branch principal, schema, deploy
e publicação continuam do principal. Worker não roda git em nenhum dos dois casos.

**Identificador de ordem escolhido no plano envelhece durante a execução.** Versão de migração,
número de sequência, nome com data: o plano o escolheu contra o destino daquele dia, e a branch
principal pode ter recebido outros enquanto as ondas rodavam. No passo irreversível, leia o último
identificador aplicado no destino (o registro de migrações de produção, não o repositório) e, se o
seu ficou atrás, renomeie antes de aplicar e reescreva as referências; o conteúdo provado não muda.
Medido em 2026-09-30: o plano fixou uma versão, a branch principal recebeu quatro migrações de
outro ciclo durante a execução, e a do plano entraria fora de ordem.

Ao commitar, estage caminho por caminho e confira o que está estagiado. Em checkout compartilhado por sessões paralelas, `add -A` varre trabalho alheio para dentro do seu commit, e ninguém acha depois pelo histórico.

## Cron de verificação: nunca pendente

Regra do usuário (02/11/2026): **terminou a tarefa, o cron entra agendado no mesmo commit.**
Cron "a agendar", "falta o cron" ou tarefa no quadro para agendá-lo depois é cron pendente, e
cron pendente não roda. Medido em 02/11/2026: um fecho entregou plano em "em validação" com o
cron virado tarefa de backlog; o usuário teve de pedir de novo.

1. **Use o agendador do ambiente, pela receita dele:** se a máquina ou o projeto tem skill ou
   runbook de cron (agendador do orquestrador, do sistema, de CI), carregue-o antes de escrever o
   script: é lá que estão o portão por data e as armadilhas medidas daquele agendador.
2. **Modelo intermediário, fixo nas duas camadas** (no agendamento e no script): o que o usuário
   definiu para rotina agendada, nunca o padrão da conta nem o modelo do gate. Confira no
   agendador que o argumento de modelo ficou gravado.
3. **Agende antes do commit do fecho**, gateado pela data (`--precheck`), mesmo que o deploy
   em produção venha depois ou seja de outra sessão: o portão por data e por `deploy_sha` cuida
   disso. O script entra no mesmo commit; o nome da automation vai para a linha de estado do
   plano e para a tarefa do quadro.
4. **Prova antes de entregar:** `run.sh --check-window` responde fechado hoje e aberto na data;
   uma execução real em pasta descartável, sem anunciar, gera o relatório.
5. **Mudança que envia algo a pessoas reais (push, WhatsApp, e-mail, qualquer mensagem) leva uma
   SEGUNDA leitura, curta: 7 dias depois de ficar ligada para elas.** O cron do prazo (14 ou 30
   dias) só veria um aviso duplicado ou errado semanas depois de gente de verdade já ter recebido.
   Se o plano não trouxe essa leitura, **acrescente-a você mesmo** e diga no relato que acrescentou:
   não espere o usuário pedir (medido em 03/11/2026: um plano de notificações entregou só o cron do
   prazo, de 30 dias, e a leitura de 7 dias só existiu porque o usuário a pediu depois do fecho).
   Ela mede dano, não sucesso: envio duplicado (mesma pessoa, mesmo tipo e dia), fora da janela de horário, no idioma errado, a quem já tinha feito a
   ação que o aviso cobra; limite zero em cada. Mesmo script do cron do prazo, com a janela por
   parâmetro e **pasta de controle própria** (o ponteiro da leitura curta não pode marcar o ciclo
   longo como entregue). Se a chave de ligar ainda está desligada, o portão lê o estado e o instante
   em que a chave foi ligada (e esse instante tem de ser regravado a cada ligada), não uma data fixa.

## Fecho

1. Rode lint e testes do projeto, você mesmo.
2. **Mova plano e spec pelo tipo de entrega que o plano declarou** (`power-plans`, seção
   *Saída de "em validação"*), no mesmo commit do fecho. Se o projeto guarda planos em pastas
   por estado (a fazer / em validação / feito, ou o nome que o `CLAUDE.md` / `AGENTS.md` der):
   - **Com backend:** de "a fazer" para "em validação", com `sai até AAAA-MM-DD` na linha de
     estado, e o(s) cron(s) de verificação **já agendado(s)** (o do prazo e, se a mudança envia
     algo a pessoas reais, a leitura curta de 7 dias), com o nome de cada um na linha de estado, no
     MESMO commit do fecho (ver *Cron de verificação: nunca pendente*, abaixo). **Nunca vá para
     "feito" no fecho:** quem move é quem lê o veredito.
   - **Só interface:** o usuário valida antes de produção; publicada em produção, vai direto para
     "feito", sem prazo nem cron. Se a publicação ainda não aconteceu, siga para "em validação"
     com a nota "só interface: vai para feito ao publicar em produção".
   Reescreva toda referência ao caminho antigo: índices, outros planos, skills, scripts e
   comentário de código. Link relativo de dentro da pasta movida muda de profundidade junto.
   Se o projeto não tem pastas de estado, pergunte uma vez se quer adotá-las; sem resposta,
   siga a convenção que existe.
3. Commite com caminhos explícitos.
   **Com protótipo aprovado e entrega de front:** antes do commit, confira que cada tela entregue
   tem a comparação lado a lado com a prancha (seção *Entrega de front com protótipo aprovado*).
   Faltou uma, o ciclo não fecha.
4. Responda os portões de entrega do projeto, sem esperar o usuário perguntar. Se o projeto entrega por bundle ou build nativo, diga sim ou não para cada um.
5. Atualize a documentação que este projeto exige atualizar no mesmo commit.
6. Feche as tasks no Orca com o resultado real, e os terminais: `wave.sh sweep` tem de responder que não há terminal de task encerrada aberto, e o único terminal seu na árvore é o do coordenador. Task que fica aberta some do radar e reaparece como confusão na próxima sessão.
7. Confira que toda task `ADV-n` tem o bloco de registro (recomendou / decidi / divergência) no documento do ciclo, e que cada divergência está no relatório ao usuário com essas palavras.
8. Relate ao usuário o que ficou de fora, se ficou, e por quê.
   Registre no documento do ciclo **uma linha de esforço**: modelos e esforço por tarefa, número de workers,
   rodadas de gate, duração, e tokens ou custo quando o runtime informar ("não disponível" quando
   não informar). Tire do que o orquestrador já registra; não crie coleta manual nem documento
   novo. Ponha ao lado a estimativa do plano (tokens e relógio) e diga quantas vezes errou e em
   qual parcela: é o que calibra a próxima estimativa. Sem essa linha, ninguém sabe se um processo mais curto ficou mais barato ou só empurrou
   trabalho para o ciclo seguinte.
9. Uma linha por skill do ciclo (`spec-interview`, `power-plans`, esta): o que entra, em qual
   arquivo, ou *"nada entra, porque X"*. Lição que fica só no relatório de revisão é lição que a
   próxima spec paga de novo. O que entrar segue a seção *Documentação viva*, no fim desta skill.

Se alguma armadilha nova aparecer durante a execução, acrescente-a a `references/orca-traps.md` no mesmo trabalho, pelas regras da seção *Documentação viva*. É a única forma de a próxima execução não pagar de novo.
