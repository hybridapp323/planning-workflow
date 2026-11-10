# Fecho do plano e saída de "em validação"

Referência da skill `power-plans`. Leia ao escrever os passos finais do coordenador, onde salvar o plano e como ele sai de "em validação".

## Fase 4 — fecho

Escreva os passos do coordenador entre as ondas e depois da última: o que ele aplica, verifica, commita e deploya, em ordem, com o comando.

Termine com os portões de entrega do projeto. Descubra quais são (ver abaixo) em vez de assumir: pode ser deploy, migration, bundle OTA, build nativo, publicação em loja. E inclua a documentação que este projeto exige atualizar no mesmo commit da mudança, se exigir. E escreva a saída de "em validação": tipo de entrega, prazo e o cron de verificação (seção *Saída de "em validação"*, em *Onde salvar*).

## Onde salvar

Siga a convenção do projeto. Procure planos anteriores (`docs/plans/`, `docs/**/plans/`, `plans/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/plans/AAAA-MM-DD-<topico>.md` e diga ao usuário que você criou a convenção.

Se o projeto guarda planos em pastas por estado (a fazer / em validação / feito), o plano novo nasce em "a fazer", ao lado da spec. Quem o move para "em validação" é o fecho de `orchestrating-execute`; para "feito", quem lê o veredito do cron de verificação. Plano só de interface pula "em validação" (seção abaixo). Plano que ainda não rodou fora de "a fazer" some da lista de trabalho.

### Saída de "em validação": tipo, prazo e cron de verificação

"Em validação" sem data vira depósito. Medido em 2026-10-26: 52 planos parados lá, e 27 deles
já estavam em produção com usuários reais usando, esperando uma prova visual que ninguém ia
colher. Por isso o plano decide **na escrita** como vai sair de lá, em três campos da seção de
fecho (modelo em `references/plan-template.md`, passo 6 do fecho):

**1. Tipo de entrega.** Decide se o plano passa por "em validação":

| Tipo | Exemplos | Caminho |
| --- | --- | --- |
| **Só interface** | tela, visual, animação, texto, layout, sem regra nem dado novo | o usuário valida antes de produção; publicado em produção, vai **direto para "feito"** no mesmo commit que registra a publicação. Sem prazo, sem cron |
| **Interface com backend** ou **só backend** | tela que grava ou lê dado novo, endpoint, migração, rotina agendada, webhook, pagamento, integração, cálculo, saída de IA | vai para "em validação" com prazo e cron agendado |

Na dúvida, é o segundo: se um erro só apareceria no dado ou no log, não na tela, há backend.

**2. Prazo.** `sai até AAAA-MM-DD`, contado da chegada a produção: **14 dias** por padrão,
**30 dias** quando o efeito precisa de ciclo longo para aparecer (uso semanal, renovação de
assinatura, métrica de retenção, rotina mensal) ou quando o plano promete uma medição nessa data.
Escreva o motivo da escolha em uma linha.

**3. Cron de verificação.** Especifique no plano, para ser agendado no MESMO commit do fecho, nunca
deixado pendente (`orchestrating-execute`, *Cron de verificação: nunca pendente*), em modelo
intermediário, gateado pela data e pelo `deploy_sha` da chegada a produção, pelo agendador que o
ambiente usar (a skill ou o runbook de cron da máquina ou do projeto diz como). Ele roda na data do prazo, gateado pela data para não subir agente antes, e responde a
pergunta do critério: *o que foi implementado está funcionando em produção, sem bug?*
O plano deixa escrito:

- **Sinais de funcionamento:** 1 a 3 consultas agregadas que provam uso real (linhas novas por
  dia, usuários distintos, eventos de sucesso). Consulta pronta, com o filtro que exclui contas
  de teste e do dono.
- **Sinais de bug:** onde o erro apareceria (evento de erro do app, log da função, chamado de
  suporte, falha recorrente, valor fora da faixa esperada) e o limite que conta como bug.
- **Saída:** o relatório com o veredito (*funcionando*, *bug*, *sem uso*) e a evidência
  numérica. O cron **não** move arquivo nem commita: quem move é a sessão que lê o veredito.

**Leitura curta, quando a mudança envia algo a pessoas reais.** Se o que foi implementado manda
push, WhatsApp, e-mail ou qualquer mensagem a usuários, o plano especifica uma **segunda leitura,
7 dias depois de a mudança ficar ligada para elas** (se estiver atrás de uma chave desligada, a
contagem começa ao ligar, não no deploy). Ela não mede sucesso, mede dano: envio duplicado (mesma
pessoa, mesmo tipo e dia), fora da janela de horário, no idioma errado, a quem já tinha feito a
ação que o aviso cobra. O limite de cada checagem é zero. O cron do prazo continua existindo; a
leitura curta é o alarme precoce. Sem ela, o aviso errado só seria visto no dia do prazo, com gente de verdade já
tendo recebido (medido em 03/11/2026: o plano de uma funcionalidade de notificações trazia só o
cron de 30 dias, e a leitura de 7 dias nasceu de um pedido do usuário depois do fecho).

No prazo, o veredito decide o destino. O plano nunca fica sem decisão:

| Veredito | Destino |
| --- | --- |
| Funcionando: em produção, usado, sem sinal de bug | "feito", com a evidência na linha de estado (`feito em AAAA-MM-DD: <evidência>`) |
| Bug | abre a correção; o plano fica e ganha prazo novo e cron novo, contados da correção em produção |
| Sem uso ou não entregue (atrás de chave desligada, só para admin, parcial) | pergunte ao usuário: feito como está, abandonado, ou prazo novo com o que falta. Uma prorrogação só; na segunda, a decisão é feito ou abandonado |

Planos que já estão em "em validação" sem tipo nem cron se revisam em lote: separe os de só
interface já em produção e os com uso real evidente, que saem sem consulta, e gaste checagem
leve (1 a 3 consultas) só onde falta evidência.

Esqueleto pronto para copiar: `references/plan-template.md`.

Depois de escrever, e sem nenhuma decisão do usuário em aberto, **não commite ainda**: pare e pergunte *revisão externa ou commit e push* (Fase 3, seção da revisão externa). Com a resposta, siga até o push sem nova parada. Não suba worker nem implemente: só com pedido explícito do usuário, e a skill então é `orchestrating-execute`.
