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

Decisões de produto fechadas antes de qualquer coisa ser construída: em obra grande viram uma spec escrita; em obra pequena, um design curto no chat. Nunca worker no ar.

Escreva no idioma em que o usuário está falando com você.

<PORTAO-DURO>
Não invoque skill de implementação, não escreva código, não crie arquivo de
projeto e não execute nenhuma ação de implementação até o usuário pedir
explicitamente a implementação. Spec e plano prontos não são esse pedido. Isso
vale para TODA tarefa em TODO caminho abaixo. A cerimônia escala com a tarefa;
o portão nunca escala.

E um segundo portão: **nada se escreve, nem spec nem código, enquanto houver
decisão de produto em aberto ou galho da árvore sem resposta.** Em troca, a spec
não espera aprovação: decisões fechadas, spec escrita, plano escrito, direto.
</PORTAO-DURO>

## Duas decisões separadas: quanto perguntar e quanto escrever

**Quanto perguntar não depende do tamanho.** Decisão de produto (muda o que o usuário vê, o dado gravado ou o custo) vira pergunta, em todo caminho, até a fronteira esvaziar. Decisão técnica, e a de como você conduz o trabalho (onde salva, como mostra), você toma e avisa. Pedido curto não é pedido fechado: "adiciona login" cabe numa linha e esconde uma dúzia de decisões.

**Quanto escrever depende do tamanho da obra.** Diga o caminho em voz alta, para o usuário poder corrigir: a estimativa antes da primeira pergunta ("isso me parece uma mudança pequena: pergunto o que está aberto e apresento um design curto no chat, sem spec") e o tamanho final quando as decisões fecharem.

| Caminho | O que é | O que produz |
| --- | --- | --- |
| **Sonda** | Pergunta de viabilidade ou pedido de protótipo: "dá pra…", "é possível…", "faz um protótipo de…". | Uma resposta ou um protótipo, não código que fica. Diga em 2–3 frases o que vai testar, descubra do jeito mais barato que ainda esteja correto, e reporte como recomendação. |
| **Direta** | Mudança em código que **já existe neste repositório**, sem decisão de produto em aberto: você lista os arquivos e a prova antes de começar. | Nada desta skill. Diga em 3 a 5 linhas o que vai fazer e como prova, e faça. |
| **Limitada** | Obra pequena com decisão de produto em aberto: um agente faz numa sessão, e ela se desfaz com um revert. | As rodadas que as decisões pedirem (quase sempre uma), um design curto no chat que diz o que você assumiu, e a implementação, pelos portões do projeto. Sem arquivo de spec, sem plano. |
| **Arquitetural** | Obra grande: projeto ou subsistema novo, capacidade nova com fluxo próprio, vários donos ou tarefas com contrato entre elas, ou mudança que grava dado que não volta atrás. | O processo inteiro: contexto, rodadas até a fronteira esvaziar, varredura de cobertura, spec escrita, auto-revisão, `power-plans` direto, sem portão de aprovação. |

**O que separa limitada de arquitetural é o tamanho da obra, não o número de perguntas.** Mudança pequena com seis perguntas continua limitada; "é em produção" e "outros usam" não a fazem subir. Suba quando o design não couber em dez linhas de chat ou aparecer um segundo dono, e diga por quê. Os dois erros custam: inflar (spec e plano para mudança de um arquivo) aparece como demora; encolher aparece como decisão do usuário tomada por você no meio da implementação.

**Direta e limitada medem o repositório, não a sua familiaridade.** Se o fluxo que você vai mudar não está aqui para ser lido, a tarefa não é nenhuma das duas.

## Fase 1 — contexto, antes da primeira pergunta

Leia o estado do projeto: arquivos que o pedido toca, `CLAUDE.md` / `AGENTS.md`,
`.claude/plan-profile.md` se existir, commits recentes e docs de decisão.

**Feature com tela só fecha com referência visual.** Decisão de tela não se toma em texto: o
usuário decide vendo. Antes de fechar a spec (ou o design curto, na limitada) de qualquer coisa com interface, uma destas três
tem de valer, e a spec diz qual (§8.3): (1) há um protótipo ou uma tela existente apontada como
referência, **aprovada e exercitada pelo usuário** (ele percorreu os estados, não só olhou a
primeira prancha); (2) a spec lista as decisões visuais e o usuário as fechou na entrevista
(onde a tela vive, navegação, o que aparece em cada estado, ações e destaque, textos); ou (3)
o usuário dispensou a referência, e a dispensa fica escrita. Se o projeto tem skill ou guia de
design, siga-o ao montar o protótipo. Com referência aprovada, extraia dela as decisões e
pergunte só o que estiver ausente ou em conflito, sem reabrir a aprovação.

**Fato externo é sonda, não premissa.** Resposta de API de terceiro ou comportamento de modelo
de que o desenho depende se mede com uma chamada real, agora ou como primeiro passo do plano.

**Fato é trabalho seu, decisão é do usuário.** Se uma pergunta da rodada precisa de um fato do ambiente — o que a tabela tem hoje, quantos usuários caem nesse caso, se aquele componente já existe — despache um subagente de contexto limpo para descobrir. Nunca pergunte ao usuário o que você mesmo pode olhar.

Não bloqueie: só as perguntas que dependem de uma busca em andamento esperam; faça o resto da rodada agora.

### Questione o caminho antes de abrir a árvore

O pedido costuma chegar como um **caminho**, não como um **objetivo**. Depois de ler o contexto, escreva em uma linha o objetivo por trás do pedido (se o usuário não disse o para quê, essa é a primeira pergunta, aberta, sem opções) e confira se o caminho pedido é o mais barato até ele. Se existe um que chega lá com uma fração do esforço, ou se o pedido contraria decisão já registrada no projeto, apresente o trade-off e a recomendação **antes** de qualquer pergunta sobre o como. Não fabrique alternativa para parecer crítico; se o usuário reafirma o caminho, registre a decisão com a alternativa descartada e siga. Pedido com vários subsistemas independentes: diga isso de saída e decomponha, um ciclo por peça. Detalhe: `references/profundidade.md`.

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

Nos dois formatos, **toda pergunta vem com a sua recomendação**, redigida para que um "sim" a aceite: sem ela, você transfere ao usuário um trabalho que é seu.

### O que perguntar

Propósito, restrição, critério de sucesso. **Traga o que o usuário não pensou:** a pergunta que mais vale é a que ele não faria sozinho. Especificamente, o que costuma ficar assumido em silêncio:

- **O que está fora de escopo** — a lista do que essa feature explicitamente *não* faz.
- **Quem mais consome** o dado, a tela ou o arquivo que isso muda.
- **O que acontece no caminho ruim** — erro, vazio, offline, usuário sem permissão, dado que já existe.
- **O estado anterior** — o que acontece com quem já usa a versão de hoje. Migração, retrocompatibilidade, dado legado.
- **Como se mede que funcionou**, se a feature tem meta de produto.

Corte sem dó o que ninguém pediu (YAGNI).

## Profundidade: quando a entrevista acabou de verdade

**A entrevista não acaba quando você já dá conta de escrever alguma spec: é aí que as decisões não feitas viram decisões suas, tomadas em silêncio. Acaba quando a fronteira esvazia e a varredura de cobertura não acusa categoria ausente.**

### O teste de fechamento

Antes de declarar a entrevista encerrada, em todo caminho, faça este exercício por escrito para você mesmo (na limitada, o passo 4 é passar pela lista de *O que perguntar*):

1. **Liste toda decisão que você tomou sozinho** para conseguir descrever a solução — formato, nome, ordem, default, limite, o que acontece no caso vazio, onde o arquivo mora.
2. **Cada item dessa lista é uma pergunta que faltou.** Se a escolha muda comportamento que o usuário vê, dado gravado ou custo, ela vira pergunta na próxima rodada, com a sua recomendação. Só detalhe sem efeito fora do código (nome interno, ordem de arquivo) pode ficar como "assumida por mim".
3. **Silêncio nunca conta como resposta.** Uma decisão que o usuário não viu não está aprovada só porque ele não reclamou.
4. **Percorra a varredura de cobertura** (`references/coverage-scan.md`), marcando cada categoria Claro / Parcial / Ausente. Os passos 1 a 3 acham o que você decidiu; a varredura acha o que você **não pensou**. Todo Parcial ou Ausente vira pergunta da próxima rodada, ou uma linha explícita na spec: *"não se aplica porque X"* (só quando não se aplicar de fato, não para fugir da pergunta).

Se a lista do passo 1 tem mais de duas ou três linhas, ou a varredura do passo 4 deixou categoria sem resposta, você parou cedo: monte a próxima rodada com elas.

### Rodadas, parada precoce e quando parar

- **Só pare quando uma rodada inteira não abrir galho novo.** No caminho arquitetural, uma rodada é sempre pouco: a primeira estabelece o quê, a segunda descobre o como e o que quebra, a terceira encontra o que ninguém tinha visto.
- **Você parou cedo se:** escreveu "por padrão" ou "provavelmente" no design; daria para implementar de duas formas bem diferentes; não sabe dizer o que fica de fora, nem o que acontece com quem já usa; o usuário respondeu "tanto faz" (ofereça a recomendação e feche); ou uma opção contradiz um requisito já dito e o texto da opção não avisa.
- **"Chega, escreve" com decisão aberta** não autoriza spec com decisão aberta: liste cada decisão restante com a sua recomendação e peça um aval único. Sem o aval, nada de spec.

Detalhe e casos medidos: `references/profundidade.md`.

## Fase 3 — o design

No caminho arquitetural, a escolha entre **2 a 3 abordagens** é uma decisão da árvore como qualquer outra: entra numa rodada, com os trade-offs no texto de cada opção e a recomendada primeiro. Não é uma apresentação à parte que espera aval.

Quando a fronteira esvaziar e a varredura não acusar categoria ausente, o design vai direto para a spec, sem apresentação por seções e sem perguntar "está de pé?". Se, ao montar o design, você descobrir uma decisão que ninguém tomou, ela não entra no design: volta como rodada de perguntas, e a spec espera. Cubra: arquitetura, componentes, fluxo do dado, tratamento de erro, e como se testa.

**Desenhe para isolamento:** unidades pequenas, de propósito claro, com interface definida e testáveis em separado; de cada uma você sabe dizer o que faz, como se usa e de que depende.

**Em código que já existe:** siga os padrões que estão lá; refatoração não relacionada fica fora.

## Fase 4 — escrever a spec (só no caminho arquitetural)

Salve seguindo a convenção do projeto: procure specs anteriores (`docs/specs/`, `docs/**/specs/`, `specs/`) e imite caminho e formato de nome. Sem nenhuma, use `docs/specs/AAAA-MM-DD-<topico>-design.md` e diga que criou a convenção. Se o projeto guarda specs em pastas por estado, a spec nasce em "a fazer" e anda junto com o plano dela.

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
7. **Exemplo é asserção** — toda tabela de valores de referência foi **calculada** pela regra que a
   spec enuncia, com a coluna intermediária à mostra (caso medido em `references/spec-template.md`)?
8. **Tela** — se há interface, o §8.3 diz qual das três condições da Fase 1 vale?

Conserte inline.

### Conferência do construtor, antes do plano

Auto-revisão feita, despache um subagente de contexto limpo, em modelo intermediário, com o brief de `references/conferencia-do-construtor.md`: ele lê a spec como quem vai planejar sem poder falar com ninguém, e lista onde teria de chutar. O que já estava respondido entra na spec; o técnico você decide e marca como assumido; **o que for de produto volta ao usuário numa rodada única, e o plano espera.**

### Sem portão de aprovação: direto para o plano

A spec não espera aval do usuário. Conferência fechada, **mostre no chat, em até dez linhas, o que ele pode querer contestar**: as decisões marcadas "assumida por mim", o que ficou fora de escopo e, se há tela, a referência que governa. Não é pedido de aval e você não espera resposta: é a lista de revisão dele. Diga onde a spec está e invoque `power-plans` no mesmo turno. Se o usuário pedir mudança na spec depois, mude, refaça a auto-revisão e ajuste o plano junto.

## Estado terminal

- **Sonda, direta e limitada:** o que a tabela de caminhos diz, pelo fluxo normal do projeto. Sem documento de plano.
- **Arquitetural:** decisões fechadas, spec escrita e conferida → invoque **`power-plans`** direto, sem esperar aval, e nenhuma outra skill. Não invoque skill de implementação, de design de front-end, nem de execução. `power-plans` é o próximo passo, ponto.

## Sinais de que você está se enganando

| Pensamento | Realidade |
| --- | --- |
| "Tem muita pergunta, melhor abrir a spec" | Quem pede spec é o tamanho da obra, não o número de perguntas. Obra pequena: pergunte tudo, design curto no chat, e faça. |
| "Falta uma decisão, mas escrevo a spec e ele corrige depois" | Spec não começa com decisão aberta. Não há aprovação depois para pegá-la: faça a rodada. |
| "Cresceu, mas já estou quase acabando" | Complexidade escondida sobe o caminho no meio do trabalho. Pare e diga. |
| "Isso é detalhe, decido na implementação" | Se muda o que o usuário vê, o dado ou o custo, é decisão dele tomada às escondidas. Pergunte, em qualquer caminho. |
| "Já tenho o suficiente pra escrever a spec" | Suficiente para escrever não é o critério. Rode o teste de fechamento. |
| "Percorri a árvore inteira, então cobri tudo" | A árvore só tem os galhos que alguém abriu. Rode a varredura de cobertura. |
| "A tela eu descrevo em texto" | Decisão de tela se toma vendo. Referência exercitada, decisões visuais fechadas, ou dispensa escrita. |
| "Ele pediu esse caminho, então é só detalhar" | O pedido é um meio. Escreva o objetivo e confira se existe caminho mais barato antes da primeira rodada. |
| "Ele não questionou, então concordou" | Silêncio não é aval. Ele só viu o que você mostrou. |

## Documentação viva

Quando uma sessão revelar uma pergunta que **faltou** e custou retrabalho, ela entra aqui (lista da Fase 2, categoria de `references/coverage-scan.md`, seção de `references/spec-template.md`, sinais de parada precoce ou a tabela acima) **no mesmo trabalho**, não "depois".

O critério para entrar é um só: **custou** (bug, escopo refeito, discussão que se repetiu). Preferência de estilo e ideia não testada ficam de fora.

Como escrever e publicar: pelo `AGENTS.md` da raiz do plugin (conceito, não caso; teto de 19 mil caracteres neste arquivo, o caso medido vai para `references/`; **commit e push no mesmo trabalho**). O clone git do plugin é a pasta desta skill, se for repositório git; senão o caminho em `~/.config/planning-workflow/clone`; sem nenhum, deixe a proposta no relatório.

---

*A classificação por caminhos, o portão duro antes da implementação e a auto-revisão da spec são adaptados da skill `brainstorming` do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent). As rodadas de fronteira vêm da skill `grilling`.*
