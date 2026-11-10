---
name: spec-interview
description: >-
  Transforma uma ideia ainda aberta em uma spec fechada, através de uma
  entrevista em rodadas: mapeia a árvore de decisões, pergunta em lote tudo que
  já dá para decidir agora com a resposta recomendada em cada pergunta, busca
  sozinha os fatos que estão no código ou no banco, e só para quando não sobra
  decisão em aberto; só então escreve a spec, sem pedir aprovação. Use para
  feature nova grande, subsistema novo ou pedido com escopo ainda aberto, e ao
  ouvir "tenho uma ideia", "me entrevista", "me pergunta", "não sei bem o que eu
  quero", "fecha o escopo comigo", "escreve a spec", "brainstorm". NÃO use para
  mudança delimitada que o usuário já descreveu por inteiro, nem para protótipo
  ou investigação: isso se faz direto. É o estado de entrada do ciclo completo:
  termina invocando `power-plans`. Nenhuma linha de código sai daqui sem pedido
  explícito de implementação.
---

# Da ideia à spec fechada

## O que sai daqui

Uma spec escrita só depois de todas as decisões fechadas, ou uma resposta em duas frases. Nunca código, nunca arquivo de projeto tocado, nunca worker no ar.

Escreva no idioma em que o usuário está falando com você.

<PORTAO-DURO>
Não invoque skill de implementação, não escreva código, não crie arquivo de
projeto e não execute nenhuma ação de implementação até o usuário pedir
explicitamente a implementação. Spec e plano prontos não são esse pedido. Isso
vale para TODA tarefa em TODO caminho abaixo. A cerimônia escala com a tarefa;
o portão nunca escala.

E um segundo portão, só do caminho arquitetural: **a spec não começa enquanto
houver decisão em aberto ou galho da árvore sem resposta.** Em troca, ela não
espera aprovação: decisões fechadas, spec escrita, plano escrito, direto.
</PORTAO-DURO>

## Primeira decisão: o portão de escala

Classifique o pedido **antes da primeira pergunta** e diga a classificação em voz alta — "isso me parece limitado, então vou apresentar um design curto aqui no chat em vez de escrever spec" — para o usuário poder corrigir na hora.

| Caminho | O que é | O que produz |
| --- | --- | --- |
| **Sonda** | Pergunta de viabilidade ou pedido de protótipo: "dá pra…", "é possível…", "faz um protótipo de…". | Uma resposta ou um protótipo, não código que fica. Diga em 2–3 frases o que vai testar, descubra do jeito mais barato que ainda esteja correto, e reporte como recomendação. |
| **Direta** | Mudança delimitada em código que **já existe neste repositório**, que o usuário já descreveu por inteiro: você lista os arquivos e a prova antes de começar. | Nada desta skill. Diga em 3 a 5 linhas o que vai fazer e como prova, e faça. Se o pedido já é a ordem de implementar, não há rodada de perguntas nem espera por aval. |
| **Limitada** | Mudança delimitada em que sobra **uma ou duas decisões** que mudam o que o usuário vê, o dado gravado ou o custo. | Uma rodada com essas perguntas, um design curto no chat, e a implementação. Sem arquivo de spec, sem plano. |
| **Arquitetural** | Projeto ou subsistema novo, feature grande, ou mudança de interface de que outros dependem **com escopo ainda aberto**. | O processo inteiro: contexto, rodadas até a fronteira esvaziar, spec escrita, auto-revisão, `power-plans` direto, sem portão de aprovação. |

**Direta e limitada medem o repositório, não a sua familiaridade.** Se o fluxo que você vai mudar não está aqui para ser lido, a tarefa não é nenhuma das duas.

**Na dúvida entre dois caminhos, o mais leve.** Suba quando o motivo aparecer (uma decisão que ninguém tomou, um segundo dono, um dado que não volta atrás), diga que subiu e refaça a classificação. Classificar como arquitetural "por segurança" o que o usuário pediu simples custa entrevista, spec, plano e revisão para uma mudança de um arquivo: é o erro mais caro desta skill, e ele aparece para o usuário como demora.

## Fase 1 — contexto, antes da primeira pergunta

Leia o estado do projeto: arquivos que o pedido toca, `CLAUDE.md` / `AGENTS.md`,
`.claude/plan-profile.md` se existir, commits recentes e docs de decisão.

**Feature com tela só fecha com referência visual.** Decisão de tela não se toma em texto: o
usuário decide vendo. Antes de fechar a spec de qualquer coisa com interface, uma destas três
tem de valer, e a spec diz qual (§8.3): (1) há um protótipo ou uma tela existente apontada como
referência, **aprovada e exercitada pelo usuário** (ele percorreu os estados, não só olhou a
primeira prancha); (2) a spec lista as decisões visuais e o usuário as fechou na entrevista
(onde a tela vive, navegação, o que aparece em cada estado, ações e destaque, textos); ou (3)
o usuário dispensou a referência, e a dispensa fica escrita. Se o projeto tem skill ou guia de
design, siga-o ao montar o protótipo. Com referência aprovada, extraia dela as decisões e
pergunte só o que estiver ausente ou em conflito, sem reabrir a aprovação.

**Fato externo é sonda, não premissa.** Resposta de API de terceiro ou comportamento de modelo
de que o desenho depende se mede com uma chamada real, agora ou como primeiro passo do plano.

**Fato é trabalho seu, decisão é do usuário.** Se uma pergunta da rodada precisa de um fato do ambiente — o que a tabela tem hoje, quantos usuários caem nesse caso, se aquele componente já existe — despache um subagente para descobrir. Nunca pergunte ao usuário o que você mesmo pode olhar.

Não bloqueie: uma busca em andamento é um pré-requisito não resolvido, então só as perguntas que dependem dela esperam. Faça o resto da rodada agora.

### Questione o caminho antes de abrir a árvore

O pedido costuma chegar como um **caminho**, não como um **objetivo**. Depois de ler o contexto, escreva em uma linha o objetivo por trás do pedido e confira se o caminho pedido é o mais barato até ele. Se existe um que chega lá com uma fração do esforço, ou se o pedido contraria decisão já registrada no projeto, apresente o trade-off e a recomendação **antes** de qualquer pergunta sobre o como. Não fabrique alternativa para parecer crítico; se o usuário reafirma o caminho, registre a decisão com a alternativa descartada e siga. Pedido com vários subsistemas independentes: diga isso de saída e decomponha, um ciclo por peça. Detalhe: `references/profundidade.md`.

## Fase 2 — as rodadas

Trate o problema como uma **árvore de decisões**: toda decisão ramifica nas decisões que dependem dela.

A **fronteira** é o conjunto de decisões cujos pré-requisitos já estão resolvidos — o que dá para perguntar **agora**, sem chutar resposta que você ainda não ouviu. Pergunte a fronteira inteira numa rodada só, cada pergunta com a sua resposta recomendada. Depois espere.

Cada resposta do usuário reformata a árvore: decisão fechada empurra a fronteira e desbloqueia o que dependia dela. Recalcule a fronteira e faça a próxima rodada. **Pergunta cuja resposta depende de outra ainda aberta nesta rodada pertence à rodada seguinte, não a esta.**

### Formato das perguntas

**Use a ferramenta de modal nativo do harness** (`AskUserQuestion` no Claude Code): até 4 perguntas por chamada, o que cobre uma rodada de fronteira inteira. Cada pergunta com 2 ou 3 opções, a recomendada primeiro e marcada `(Recomendado)`, e uma linha dizendo o que cada opção custa. Use `preview` quando a comparação for visual ou de código.

**Mais de 4 perguntas na rodada:** duas chamadas seguidas. Nunca funda duas decisões numa pergunta para caber no limite.

**Se o harness não tiver essa ferramenta**, escreva a rodada em texto, numerada, com a recomendação explícita:

```
❓ **Q1** — **<título>**: <pergunta>

➡️ <sua resposta recomendada, e por quê>

---

❓ **Q2** — ...
```

Nos dois formatos, **toda pergunta vem com a sua recomendação**: sem ela, você transfere ao usuário um trabalho que é seu.

### O que perguntar

Propósito, restrição, critério de sucesso. E, especificamente, o que costuma ficar assumido em silêncio:

- **O que está fora de escopo** — a lista do que essa feature explicitamente *não* faz.
- **Quem mais consome** o dado, a tela ou o arquivo que isso muda.
- **O que acontece no caminho ruim** — erro, vazio, offline, usuário sem permissão, dado que já existe.
- **O estado anterior** — o que acontece com quem já usa a versão de hoje. Migração, retrocompatibilidade, dado legado.
- **Como se mede que funcionou**, se a feature tem meta de produto.

Corte sem dó o que ninguém pediu (YAGNI).

## Profundidade: quando a entrevista acabou de verdade

**A entrevista não acaba quando você já dá conta de escrever alguma spec: é aí que as decisões não feitas viram decisões suas, tomadas em silêncio. Acaba quando a fronteira esvazia e a varredura de cobertura não acusa categoria ausente.**

### O teste de fechamento

Antes de declarar a entrevista encerrada, faça este exercício, sempre, e por escrito para você mesmo:

1. **Liste toda decisão que você tomou sozinho** para conseguir descrever a solução — formato, nome, ordem, default, limite, o que acontece no caso vazio, onde o arquivo mora.
2. **Cada item dessa lista é uma pergunta que faltou.** Se a escolha muda comportamento que o usuário vê, dado gravado ou custo, ela vira pergunta na próxima rodada, com a sua recomendação. Só detalhe sem efeito fora do código (nome interno, ordem de arquivo) pode ficar como "assumida por mim".
3. **Silêncio nunca conta como resposta.** Uma decisão que o usuário não viu não está aprovada só porque ele não reclamou.
4. **Percorra a varredura de cobertura** (`references/coverage-scan.md`), marcando cada categoria Claro / Parcial / Ausente. Os passos 1 a 3 acham o que você decidiu; a varredura acha o que você **não pensou**. Todo Parcial ou Ausente vira pergunta da próxima rodada, ou uma linha explícita na spec: *"não se aplica porque X"* (só quando não se aplicar de fato, não para fugir da pergunta).

Se a lista do passo 1 tem mais de duas ou três linhas, ou a varredura do passo 4 deixou categoria sem resposta, você parou cedo: monte a próxima rodada com elas.

### Rodadas, parada precoce e quando parar

- **Só pare quando uma rodada inteira não abrir galho novo.** No caminho arquitetural, uma rodada é sempre pouco.
- **Você parou cedo se:** escreveu "por padrão" ou "provavelmente" no design; daria para implementar de duas formas bem diferentes; não sabe dizer o que fica de fora, nem o que acontece com quem já usa; o usuário respondeu "tanto faz" (ofereça a recomendação e feche); ou uma opção contradiz um requisito já dito e o texto da opção não avisa.
- **"Chega, escreve" com decisão aberta** não autoriza spec com decisão aberta: liste cada decisão restante com a sua recomendação e peça um aval único. Sem o aval, nada de spec.

Detalhe e casos medidos: `references/profundidade.md`.

## Fase 3 — o design

No caminho arquitetural, a escolha entre **2 a 3 abordagens** é uma decisão da árvore como qualquer outra: entra numa rodada, com os trade-offs no texto de cada opção e a recomendada primeiro. Não é uma apresentação à parte que espera aval.

Quando a fronteira esvaziar e a varredura não acusar categoria ausente, o design vai direto para a spec, sem apresentação por seções e sem perguntar "está de pé?". Se, ao montar o design, você descobrir uma decisão que ninguém tomou, ela não entra no design: volta como rodada de perguntas, e a spec espera. Cubra: arquitetura, componentes, fluxo do dado, tratamento de erro, e como se testa.

**Desenhe para isolamento:** unidades pequenas, com um propósito claro cada, conversando por interface bem definida, testáveis em separado. Para cada uma, você tem que conseguir responder: o que faz, como se usa, de que depende.

**Em código que já existe:** siga os padrões que estão lá. Melhoria pontual no que atrapalha o trabalho entra no design; refatoração não relacionada, não.

## Fase 4 — escrever a spec (só no caminho arquitetural)

Salve seguindo a convenção do projeto. Procure specs anteriores (`docs/specs/`, `docs/**/specs/`, `specs/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/specs/AAAA-MM-DD-<topico>-design.md` e diga ao usuário que você criou a convenção. Se o projeto guarda specs em pastas por estado (a fazer / em validação / feito), a spec nasce em "a fazer" e anda junto com o plano dela.

Esqueleto pronto para copiar: `references/spec-template.md`. Copie a estrutura, não o conteúdo; corte seção que a feature não usa e diga que cortou. Três coisas do esqueleto não são opcionais, porque o plano vai citá-las: requisito com id (`FR-n`) e pelo menos um cenário de aceitação (*dado / quando / então*); critério de sucesso com id (`SC-n`), número e baseline; e a lista de quem mais consome e emite o que muda, nas duas direções.

Além do design, a spec registra **o que foi descartado, e por quê** (sem isso, o primeiro implementador que achar a alternativa "melhor" vai implementá-la) e **as decisões, com autoria**: *decidida pelo usuário* ou *assumida por mim*. Decisão que muda comportamento, dado ou custo e está como assumida é pergunta que faltou.

### Auto-revisão, antes de mostrar

Releia com olhos frios e conserte na hora:

1. **Placeholder** — sobrou "TBD", "a definir", seção vazia, requisito vago?
2. **Contradição** — alguma seção briga com outra? A arquitetura bate com a descrição das features? Resposta de rodada que invalidou uma frase anterior **substitui** a frase; nada contraditório sobrevive "para contexto".
3. **Escopo** — isso cabe em um plano de implementação só, ou precisa ser decomposto?
4. **Ambiguidade** — algum requisito comporta duas leituras? Escolha uma e escreva explícito. Procure token a token, pela lista de *Placeholders* de `references/coverage-scan.md`: adjetivo sem número, verbo sem objeto mensurável, recurso sem o que acontece quando falha, o mesmo conceito com dois nomes.
5. **Decisão órfã** — sobrou decisão marcada "assumida por mim" que devia ter virado pergunta? Se sim, pare a escrita e faça a rodada: não há aprovação depois para pegá-la.
6. **Rastreabilidade** — todo FR tem cenário de aceitação e uma linha em "como se prova"? Todo SC tem número e baseline?
7. **Exemplo é asserção, não ilustração** — toda tabela de valores de referência foi
   **calculada** a partir da regra que a spec enuncia, com a coluna intermediária à mostra? Regra
   mais exemplos escritos à mão se contradizem sem ninguém notar lendo (caso medido nas notas de
   `references/spec-template.md`).
8. **Tela** — se há interface, o §8.3 diz qual das três condições da Fase 1 vale?

Conserte inline. Não precisa revisar de novo.

### Sem portão de aprovação: direto para o plano

A spec não espera aval do usuário. Auto-revisão feita, **mostre no chat, em até dez linhas, o que ele pode querer contestar**: as decisões marcadas "assumida por mim", o que ficou fora de escopo e, se há tela, a referência que governa. Não é pedido de aval, e você não espera resposta: é a lista de revisão dele, que sem isso ninguém vê. Diga onde a spec está e invoque `power-plans` no mesmo turno. Se o usuário pedir mudança na spec depois, mude, refaça a auto-revisão e ajuste o plano junto.

## Estado terminal

- **Sonda:** uma recomendação ou um protótipo reportado. Fim.
- **Direta:** a mudança feita e provada, pelo fluxo normal do projeto. Sem spec, sem plano.
- **Limitada:** design curto e implementação pelo fluxo normal do projeto. Sem documento de plano.
- **Arquitetural:** decisões fechadas e spec escrita → invoque **`power-plans`** direto, sem esperar aval, e nenhuma outra skill. Não invoque skill de implementação, de design de front-end, nem de execução. `power-plans` é o próximo passo, ponto.

## Sinais de que você está se enganando

| Pensamento | Realidade |
| --- | --- |
| "Melhor abrir a spec, por segurança" | O usuário descreveu o pedido por inteiro e a mudança se desfaz com um revert: é direta. Inflar também é erro, e ele paga em demora. |
| "É pequeno, mas vou entrevistar para alinhar" | Se não sobra decisão que mude o que ele vê, o dado ou o custo, não há o que perguntar. Faça. |
| "O design é óbvio, começo enquanto ele lê" | No caminho arquitetural, implementação só com pedido explícito. Spec e plano prontos não são pedido. |
| "Falta uma decisão, mas escrevo a spec e ele corrige depois" | Spec não começa com decisão aberta. Não há aprovação depois para pegá-la: faça a rodada. |
| "Eu conheço esse tipo de app, então é direta" | Direta mede o repositório. Projeto novo não tem fluxo existente: é arquitetural. |
| "Cresceu, mas já estou quase acabando" | Complexidade escondida sobe o caminho no meio do trabalho. Pare e diga. |
| "Pergunto ao usuário se essa tabela já existe" | Fato é trabalho seu. Despache um subagente e descubra. |
| "Faço uma pergunta por mensagem pra não sobrecarregar" | A fronteira inteira vai numa rodada. Perguntar em fila multiplica as idas e voltas. |
| "Já tenho o suficiente pra escrever a spec" | Suficiente para escrever não é o critério. Rode o teste de fechamento. |
| "Percorri a árvore inteira, então cobri tudo" | A árvore só tem os galhos que alguém abriu. Rode a varredura de cobertura. |
| "A tela eu descrevo em texto" | Decisão de tela se toma vendo. Referência exercitada, decisões visuais fechadas, ou dispensa escrita. |
| "Ele pediu esse caminho, então é só detalhar" | O pedido é um meio. Escreva o objetivo e confira se existe caminho mais barato antes da primeira rodada. |
| "Ele não questionou, então concordou" | Silêncio não é aval. Ele só viu o que você mostrou. |

## Documentação viva

Esta skill melhora com o uso. Quando uma sessão revelar uma pergunta que **faltou** e custou retrabalho depois, ela entra aqui — na lista da Fase 2, numa categoria de `references/coverage-scan.md`, numa seção de `references/spec-template.md`, nos sinais de parada precoce, ou na tabela acima — **no mesmo trabalho**, não "depois".

O critério para entrar é um só: **custou.** Uma pergunta esquecida que virou bug, escopo refeito, ou uma discussão que se repetiu pela segunda vez. Preferência de estilo e ideia não testada ficam de fora — a skill perde o fio se virar depósito.

Como escrever: melhore a seção que já cobre o assunto antes de acrescentar linha (este arquivo tem teto de 19 mil caracteres, conferido por `scripts/check-skills.sh`; o caso medido vai para `references/`); siga o `AGENTS.md` da raiz do plugin (conceito, não caso); escreva no clone git do plugin (a pasta desta skill, se for repositório git; senão o caminho em `~/.config/planning-workflow/clone`; sem nenhum, deixe a proposta no relatório). **Commit e push no mesmo trabalho:** rode `scripts/check-skills.sh`, commite só os caminhos que mudou, dê push na branch principal, rode `scripts/sync-harnesses.sh` se existir e diga ao usuário o commit em uma linha. O histórico do git é o backup.

---

*A classificação em três caminhos, o portão duro antes da implementação e a auto-revisão da spec são adaptados da skill `brainstorming` do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent). O formato de rodadas de fronteira vem da skill `grilling`.*
