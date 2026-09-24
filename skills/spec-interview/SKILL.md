---
name: spec-interview
description: >-
  Transforma uma ideia ainda aberta em uma spec aprovada, através de uma
  entrevista em rodadas: mapeia a árvore de decisões, pergunta em lote tudo que
  já dá para decidir agora com a resposta recomendada em cada pergunta, busca
  sozinha os fatos que estão no código ou no banco, e só para quando não sobra
  decisão em aberto. USE SEMPRE antes de qualquer trabalho criativo — feature
  nova, componente novo, mudança de comportamento — e sempre que ouvir "quero
  fazer", "vamos construir", "tenho uma ideia", "me entrevista", "me pergunta",
  "não sei bem o que eu quero", "fecha o escopo comigo", "escreve a spec",
  "brainstorm". É o estado de entrada do ciclo: termina invocando `power-plans`,
  que escreve o plano de implementação. Nenhuma linha de código sai daqui sem
  aprovação explícita.
---

# Da ideia à spec aprovada

## O que sai daqui

Uma spec aprovada pelo usuário, ou uma resposta em duas frases. Nunca código, nunca arquivo de projeto tocado, nunca worker no ar.

Escreva no idioma em que o usuário está falando com você.

<PORTAO-DURO>
Não invoque skill de implementação, não escreva código, não crie arquivo de
projeto e não execute nenhuma ação de implementação até ter dito ao usuário o
que você pretende fazer e ele ter aprovado. Isso vale para TODA tarefa em TODO
caminho abaixo. A cerimônia escala com a tarefa; o portão nunca escala.
</PORTAO-DURO>

## Primeira decisão: o portão de escala

Classifique o pedido **antes da primeira pergunta** e diga a classificação em voz alta — "isso me parece limitado, então vou apresentar um design curto aqui no chat em vez de escrever spec" — para o usuário poder corrigir na hora.

| Caminho | O que é | O que produz |
| --- | --- | --- |
| **Sonda** | Pergunta de viabilidade: "dá pra…", "é possível…", "quero só saber se funciona". | Uma resposta, não código que fica. Apresente a pergunta e o que vai testar em 2–3 frases, colha um "pode", descubra do jeito mais barato que ainda esteja correto, e reporte como recomendação. O que você construiu fica marcado como descartável. |
| **Limitada** | Mudança bem delimitada em código que **já existe neste repositório**: uma flag, um endpoint pequeno, um fix de um arquivo. | Uma ou duas rodadas de perguntas, um design curto no chat, aprovação, implementação direta. Sem arquivo de spec, sem plano. |
| **Arquitetural** | Projeto novo, subsistema novo, mudança que altera como as peças se encaixam ou muda interface de que outros dependem. | O processo inteiro: contexto, rodadas até a fronteira esvaziar, opções, design por seções, spec escrita, auto-revisão, aprovação, `power-plans`. |

**Limitada mede o repositório, não a sua familiaridade.** Se o fluxo que você vai mudar não está aqui para ser lido, a tarefa não é limitada. Entender o tipo de app não basta.

**Na dúvida entre dois caminhos, suba.** A catraca é de mão única: complexidade escondida que aparece no meio do trabalho **sobe** o caminho — pare, diga isso, e refaça a classificação. Nada desce no meio do caminho.

## Fase 1 — contexto, antes da primeira pergunta

Leia o estado do projeto: arquivos que o pedido toca, `CLAUDE.md` / `AGENTS.md`, commits recentes, docs de decisão se o projeto tiver.

**Fato é trabalho seu, decisão é do usuário.** Se uma pergunta da rodada precisa de um fato do ambiente — o que a tabela tem hoje, quantos usuários caem nesse caso, se aquele componente já existe — despache um subagente para descobrir. Nunca pergunte ao usuário o que você mesmo pode olhar.

Não bloqueie: uma busca em andamento é um pré-requisito não resolvido, então só as perguntas que dependem dela esperam. Faça o resto da rodada agora.

**Se o pedido tem vários subsistemas independentes** ("uma plataforma com chat, arquivos, cobrança e analytics"), diga isso imediatamente, antes de gastar perguntas refinando detalhe. Ajude a decompor: quais são as peças independentes, como se relacionam, em que ordem. Cada peça ganha o próprio ciclo spec → plano → implementação.

## Fase 2 — as rodadas

Trate o problema como uma **árvore de decisões**: toda decisão ramifica nas decisões que dependem dela.

A **fronteira** é o conjunto de decisões cujos pré-requisitos já estão resolvidos — o que dá para perguntar **agora**, sem chutar resposta que você ainda não ouviu. Pergunte a fronteira inteira numa rodada só, cada pergunta com a sua resposta recomendada. Depois espere.

Cada resposta do usuário reformata a árvore: decisão fechada empurra a fronteira e desbloqueia o que dependia dela. Recalcule a fronteira e faça a próxima rodada. **Pergunta cuja resposta depende de outra ainda aberta nesta rodada pertence à rodada seguinte, não a esta.**

### Formato das perguntas

**Use a ferramenta de modal nativo do harness** (`AskUserQuestion` no Claude Code): até 4 perguntas por chamada, o que cobre uma rodada de fronteira inteira. Cada pergunta com no máximo 2 opções, a recomendada primeiro e marcada `(Recomendado)`, e uma linha dizendo o que cada opção custa. Use `preview` quando a comparação for visual ou de código.

**Se a rodada tiver mais de 4 perguntas**, faça duas chamadas seguidas. Nunca funda duas decisões numa pergunta só para caber no limite — "que formato, e onde salvar?" são duas decisões, e o usuário só vai responder uma.

**Se o harness não tiver essa ferramenta**, escreva a rodada em texto, numerada, com a recomendação explícita:

```
❓ **Q1** — **<título>**: <pergunta>

➡️ <sua resposta recomendada, e por quê>

---

❓ **Q2** — ...
```

Nos dois formatos, a regra é a mesma: **toda pergunta vem com a sua recomendação.** Pergunta sem recomendação transfere ao usuário um trabalho que é seu.

### O que perguntar

Propósito, restrição, critério de sucesso. E, especificamente, o que costuma ficar assumido em silêncio:

- **O que está fora de escopo** — a lista do que essa feature explicitamente *não* faz.
- **Quem mais consome** o dado, a tela ou o arquivo que isso muda.
- **O que acontece no caminho ruim** — erro, vazio, offline, usuário sem permissão, dado que já existe.
- **O estado anterior** — o que acontece com quem já usa a versão de hoje. Migração, retrocompatibilidade, dado legado.
- **Como se mede que funcionou**, se a feature tem meta de produto.

Corte sem dó o que ninguém pediu (YAGNI). Uma opção que você acha "legal ter" é escopo que o usuário vai pagar.

## Profundidade: quando a entrevista acabou de verdade

Este é o ponto onde uma entrevista boa se distingue de um questionário. A tentação é parar na primeira rodada em que você já consegue escrever *alguma* spec — e é exatamente aí que as decisões não feitas viram decisões suas, tomadas em silêncio, descobertas na implementação.

**A entrevista não acaba quando você já dá conta de escrever. Acaba quando a fronteira esvazia e a varredura de cobertura não acusa categoria ausente.**

### O teste de fechamento

Antes de declarar a entrevista encerrada, faça este exercício, sempre, e por escrito para você mesmo:

1. **Liste toda decisão que você tomou sozinho** para conseguir descrever a solução — formato, nome, ordem, default, limite, o que acontece no caso vazio, onde o arquivo mora.
2. **Cada item dessa lista é uma pergunta que faltou.** Ou ela vira pergunta na próxima rodada, ou ela vira uma linha explícita no design: *"assumi X; se não for, me diz."*
3. **Silêncio nunca conta como resposta.** Uma decisão que o usuário não viu não está aprovada só porque ele não reclamou.
4. **Percorra a varredura de cobertura** (`references/coverage-scan.md`), marcando cada categoria Claro / Parcial / Ausente. Os passos 1 a 3 são introspectivos: acham o que você decidiu. Não acham o que você **não pensou**, porque nenhum galho da árvore levava até lá. A varredura é a lista externa que acha isso. Todo Parcial ou Ausente vira pergunta da próxima rodada, ou uma linha explícita na spec: *"não se aplica porque X"*.

Se a lista do passo 1 tem mais de duas ou três linhas, ou a varredura do passo 4 deixou categoria sem resposta, você parou cedo: monte a próxima rodada com elas.

### Regra das rodadas

Uma resposta do usuário quase sempre abre galho novo — ele escolhe uma opção e aquela opção traz três decisões que não existiam antes. **Só pare quando uma rodada inteira não abrir nenhum galho novo.** Uma rodada só e acabou é sinal de que você tratou a árvore como lista.

**No caminho arquitetural, uma rodada é sempre pouco.** Se você chegou ao fim da primeira rodada achando que entendeu tudo, você entendeu a superfície: a primeira rodada estabelece o quê, a segunda descobre o como e o que quebra, a terceira encontra o que ninguém tinha visto. Não é cerimônia — é onde a spec para de mentir.

### Sinais de que você parou cedo

- Você escreveu "por padrão", "provavelmente" ou "algo como" no design.
- Você conseguiria implementar de duas formas bem diferentes sem violar nada do que foi conversado.
- Você não sabe dizer o que a feature **não** faz.
- Você não sabe o que acontece com quem já é usuário hoje.
- O usuário respondeu com "acho que", "sei lá" ou "tanto faz" — isso é uma decisão em aberto disfarçada de resposta, não um aval. Ofereça a sua recomendação e feche.

### Quando parar mesmo assim

Duas exceções, e só elas: o usuário dizer explicitamente para tocar ("chega, escreve"), ou o caminho ser **sonda** ou **limitada** — nesses, a profundidade certa é rasa por definição. Se o usuário mandar parar com decisão em aberto, escreva as que ficaram abertas na spec, com o default que você assumiu em cada uma.

## Fase 3 — o design

Quando a fronteira esvaziar, apresente o design.

Antes disso, no caminho arquitetural: proponha **2 a 3 abordagens** com trade-offs, liderando pela recomendada e dizendo por quê.

Apresente o design em seções, cada uma dimensionada pela própria complexidade — algumas frases se for direto, até uns três parágrafos se for sutil. Pergunte depois de cada seção se está de pé. Cubra: arquitetura, componentes, fluxo do dado, tratamento de erro, e como se testa.

**Desenhe para isolamento:** unidades pequenas, com um propósito claro cada, conversando por interface bem definida, testáveis em separado. Para cada uma, você tem que conseguir responder: o que faz, como se usa, de que depende.

**Em código que já existe:** siga os padrões que estão lá. Melhoria pontual no que atrapalha o trabalho entra no design; refatoração não relacionada, não.

## Fase 4 — escrever a spec (só no caminho arquitetural)

Salve seguindo a convenção do projeto. Procure specs anteriores (`docs/specs/`, `docs/**/specs/`, `specs/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/specs/AAAA-MM-DD-<topico>-design.md` e diga ao usuário que você criou a convenção. Se o projeto guarda specs em pastas por estado (a fazer / em validação / feito), a spec nasce em "a fazer" e anda junto com o plano dela.

Esqueleto pronto para copiar: `references/spec-template.md`. Copie a estrutura, não o conteúdo; corte seção que a feature não usa e diga que cortou. Três coisas do esqueleto não são opcionais, porque o plano vai citá-las: requisito com id (`FR-n`) e pelo menos um cenário de aceitação (*dado / quando / então*); critério de sucesso com id (`SC-n`), número e baseline; e a lista de quem mais consome e emite o que muda, nas duas direções. A regra existia em prosa e não segurou. Medido em 2026-09-02: de duas specs arquiteturais do mesmo ciclo, uma saiu com 14 seções e a outra com 4, sem decisão com autoria nem alternativa descartada.

Além do design, a spec registra duas coisas que o plano vai precisar e ninguém mais vai lembrar:

- **O que foi descartado, e por quê.** Sem isso, o primeiro implementador que achar a alternativa "melhor" vai implementá-la.
- **As decisões, com autoria.** Cada decisão relevante marcada como *decidida pelo usuário* ou *assumida por mim*. As assumidas são a lista de revisão do usuário — é onde ele vai olhar primeiro.

### Auto-revisão, antes de mostrar

Releia com olhos frios e conserte na hora:

1. **Placeholder** — sobrou "TBD", "a definir", seção vazia, requisito vago?
2. **Contradição** — alguma seção briga com outra? A arquitetura bate com a descrição das features? Resposta de rodada que invalidou uma frase anterior **substitui** a frase; nada contraditório sobrevive "para contexto".
3. **Escopo** — isso cabe em um plano de implementação só, ou precisa ser decomposto?
4. **Ambiguidade** — algum requisito comporta duas leituras? Escolha uma e escreva explícito. Procure token a token, não por impressão geral:
   - adjetivo sem número: rápido, robusto, intuitivo, "em tempo real", grande, muitos, poucos;
   - requisito com verbo e sem objeto mensurável ("o sistema deve suportar X");
   - recurso citado sem o que acontece quando ele falha, está vazio ou demora;
   - o mesmo conceito com dois nomes;
   - "por padrão", "provavelmente", "algo como", "etc.", "e afins".
5. **Decisão órfã** — sobrou decisão marcada "assumida por mim" que devia ter virado pergunta?
6. **Rastreabilidade** — todo FR tem cenário de aceitação e uma linha em "como se prova"? Todo SC tem número e baseline?
7. **Exemplo é asserção, não ilustração** — toda tabela de valores de referência foi
   **calculada** a partir da regra que a spec enuncia, ou foi escrita à mão? Regra mais exemplos
   é uma redundância *derivável*, e ninguém pega a contradição lendo: só computando. Medido em
   2026-09-03: uma tabela de 6 perfis de referência trazia 3 linhas que nenhuma regra única de
   arredondamento produzia; passou pela aprovação do usuário e só caiu na implementação, quando
   um worker calculou os 6 e escalou em vez de dobrar o código para caber na tabela. Calcule
   antes de publicar, e **mostre a coluna intermediária** — erro que fica visível não sobrevive à
   revisão seguinte.

Conserte inline. Não precisa revisar de novo.

### Portão de revisão do usuário

> "Spec escrita em `<caminho>`. Dá uma olhada e me diz se quer mudar alguma coisa antes de eu escrever o plano de implementação."

Espere. Se ele pedir mudança, mude e refaça a auto-revisão. Só avance com o aval dele.

## Estado terminal

- **Sonda:** uma recomendação reportada. Fim.
- **Limitada:** design curto aprovado → implementação pelo fluxo normal do projeto. Sem documento de plano.
- **Arquitetural:** spec aprovada → invoque **`power-plans`**, e nenhuma outra skill. Não invoque skill de implementação, de design de front-end, nem de execução. `power-plans` é o próximo passo, ponto.

## Sinais de que você está se enganando

| Pensamento | Realidade |
| --- | --- |
| "É simples demais pra precisar de design" | Simples significa design curto, não design nenhum. Duas frases e a aprovação. |
| "Vou chamar de limitada e pular a spec" | Procurar um rótulo para pular trabalho **é** a dúvida. Suba o caminho. |
| "O design é óbvio, começo enquanto ele lê" | O portão é a aprovação, não o tamanho do design. Apresente e pare. |
| "Eu conheço esse tipo de app, então é limitada" | Limitada mede o repositório. Projeto novo não tem fluxo existente: é arquitetural. |
| "Cresceu, mas já estou quase acabando" | Complexidade escondida sobe o caminho no meio do trabalho. Pare e diga. |
| "Ele aprovou a sonda, então o resto está aprovado" | Cada tarefa tem a própria classificação e a própria aprovação. |
| "Pergunto ao usuário se essa tabela já existe" | Fato é trabalho seu. Despache um subagente e descubra. |
| "Faço uma pergunta por mensagem pra não sobrecarregar" | A fronteira inteira vai numa rodada. Perguntar em fila multiplica as idas e voltas por dez. |
| "Já tenho o suficiente pra escrever a spec" | Suficiente para escrever não é o critério. Rode o teste de fechamento. |
| "Percorri a árvore inteira, então cobri tudo" | A árvore só tem os galhos que alguém abriu. Rode a varredura de cobertura. |
| "Isso é detalhe, decido na implementação" | Detalhe decidido na implementação é decisão do usuário tomada por você às escondidas. |
| "Ele não questionou, então concordou" | Silêncio não é aval. Ele só viu o que você mostrou. |

## Documentação viva

Esta skill melhora com o uso. Quando uma sessão revelar uma pergunta que **faltou** e custou retrabalho depois, ela entra aqui — na lista da Fase 2, numa categoria de `references/coverage-scan.md`, numa seção de `references/spec-template.md`, nos sinais de parada precoce, ou na tabela acima — **no mesmo trabalho**, não "depois".

O critério para entrar é um só: **custou.** Uma pergunta esquecida que virou bug, escopo refeito, ou uma discussão que se repetiu pela segunda vez. Preferência de estilo e ideia não testada ficam de fora — a skill perde o fio se virar depósito.

---

*A classificação em três caminhos, o portão duro de aprovação e a auto-revisão da spec são adaptados da skill `brainstorming` do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent). O formato de rodadas de fronteira vem da skill `grilling`.*
