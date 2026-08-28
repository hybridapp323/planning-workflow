---
name: power-plans
description: >-
  Escreve o plano de implementação de uma feature já especificada, desenhado
  para execução multi-agente em paralelo: nível de complexidade por tarefa
  (complexa / média / baixa), matriz de ownership de arquivo, contratos
  congelados antes da primeira onda, grafo de ondas com dependências explícitas
  e gates que bloqueiam passos irreversíveis. USE SEMPRE que a spec ou o design
  estiver pronto e o próximo passo for planejar a implementação, e sempre que
  ouvir "escreve o plano", "plano de implementação", "como a gente paraleliza
  isso", "divide entre os agentes", "quantos workers", "monta o plano dessa
  feature", "prepara isso pra multi-agente". É o estado terminal da skill
  `brainstorming`: design aprovado, invoque esta. Serve qualquer projeto — as
  regras específicas saem do CLAUDE.md/AGENTS.md do repositório. Ela escreve o
  plano e para: quem sobe worker é `orchestrating-execute`.
---

# Plano de implementação para execução multi-agente

## O que sai daqui

Um arquivo de plano, e nada mais. Nenhuma linha de código, nenhuma migration, nenhum worker no ar.

O plano não cita orquestrador. Um grafo com níveis, donos e contratos congelados vale igual executado pelo Orca, por subagente nativo, ou por uma pessoa por tarefa. Amarrar a ferramenta aqui só encurta a validade do documento.

Escreva no idioma em que o usuário está falando com você.

## Primeira decisão: o portão de escala

Antes de qualquer coisa, decida quanto aparato essa feature merece. Um plano de 15 tarefas para uma mudança de duas telas é imposto, não rigor.

| Situação | O que fazer |
| --- | --- |
| 1 a 3 arquivos, um domínio só, sem migration nem deploy | Não use este aparato. Escreva cinco linhas de plano e implemente. |
| 4+ tarefas com donos diferentes, **ou** toca banco / edge function / deploy / dado de produção, **ou** existe trabalho genuinamente independente para paralelizar | Aparato completo: fases 0 a 4. |
| Entre os dois | Use as partes que pagam: níveis e ownership de arquivo. Pule ondas e gates. |

Diga ao usuário qual dos três você escolheu, e por quê, antes de escrever o plano. Se ele discordar, ele corrige agora e não depois de vinte minutos de documento.

## Fase 0 — evidência antes de plano

O erro caro não é planejar errado. É planejar em cima de suposição que ninguém checou, porque o plano fica coerente, convincente e falso ao mesmo tempo.

1. Leia a spec inteira.
2. Abra os arquivos que ela promete tocar. Anote `arquivo:linha` de tudo que confirma ou contradiz o que a spec assume.
3. Consulte o estado real do dado sempre que a spec depender dele: schema, trigger, policy, e **contagem**. Contagem muda prioridade. "Vamos suportar X" é outra conversa quando X tem zero usuário hoje.
4. Escreva o snapshot de evidência.

**O snapshot** é um arquivo com o que foi lido, os `arquivo:linha` das descobertas, as queries rodadas e o resultado cru delas. Guarde fora do repositório (scratchpad da sessão) a menos que o projeto tenha lugar próprio. Ele paga duas vezes: fecha as lacunas agora, e é o que se entrega ao revisor externo depois, se houver revisão.

**Regra dura:** um bloqueador que você não conseguiu reproduzir no código ou no dado não é bloqueador, é hipótese. Escreva-o como hipótese, com o que faltou para confirmar.

**Esta fase cobre o DIAGNÓSTICO e para aí.** Os fatos que a sua solução vai inventar ainda não
existem agora. Eles têm fase própria, logo abaixo, e ignorá-la foi o que produziu três
afirmações falsas num plano cujo snapshot de evidência tinha 17 KB.

### Validar a spec, e consertá-la se precisar

A spec passou pela aprovação do usuário, mas quem a escreveu não estava tentando paralelizar. Três lacunas só aparecem agora, e as três quebram execução paralela:

- **Contratos ausentes.** A spec descreve comportamento mas não fixa formato. Dois workers vão inventar dois formatos.
- **Matriz de consumidores ausente, e ela é BIDIRECIONAL.** Quem mais **lê** o dado, o campo ou o arquivo que essa feature muda? Um resolver, um job agendado, uma exportação, uma tela secundária. E, na direção que quase sempre falta: quem mais **escreve ou emite** o comportamento que a feature altera? Feature nova morre num consumidor esquecido; feature que REMOVE comportamento morre num emissor esquecido.
- **Decisões sem o que foi descartado.** Sem isso, o primeiro worker que achar a alternativa "melhor" vai implementá-la.

Se faltar, conserte a spec, e diga ao usuário exatamente o que você mudou nela. Planejar em cima de spec furada só adia o furo.

## Fase 0.5 — a evidência da SOLUÇÃO, não só a do problema

A Fase 0 valida **a spec**: o que o problema é, onde ele mora, quanto dado ele afeta. Isso é
metade. A outra metade nasce depois, quando você desenha a correção, e **não passa por
evidência nenhuma** se você não voltar de propósito.

Medido no ciclo `2026-08-26-auditoria-nome-removido`: o snapshot de evidência tinha 17 KB, media o
problema ao segundo, citava `arquivo:linha` e contava frequência em produção. Ainda assim o
plano saiu com **três afirmações falsas**, e as três eram do lado da *prescrição*:

| afirmação do plano | realidade | custo |
|---|---|---|
| "corte em `ai_audit_logs.created_at`" | é quando o turno **fechou**, ~13 s DEPOIS do inbound a recuperar. O corte cru excluiria exatamente a mensagem alvo | **o fix seria um no-op, e passaria verde** |
| "a [nome removido] aparece em `flag_y`" | `max=20000` é plausível e não bate em nenhum dos 3 critérios congelados | um worker gastou um ciclo de dispatch para escalar |
| `node scripts/run-e2e.mjs` | o caminho é `.claude/skills/ai-chat-e2e/scripts/run-e2e.mjs` | comando quebrado no passo do coordenador |

Nenhuma das três estava no snapshot — porque nenhuma existia quando a Fase 0 rodou. A regra
que faltava é esta:

> **Evidência que para no diagnóstico não protege a prescrição.** Todo fato NOVO que a
> solução inventa entra na mesma disciplina do fato que descreveu o problema.

### Etiqueta de procedência: obrigatória em todo fato do plano

Toda afirmação factual do plano carrega uma das três, literal:

```
[MEDIDO: <comando ou query> → <resultado cru>]      verificado agora, com o resultado à vista
[LIDO: caminho/arquivo.ts:120-134]                  confirmado no código, com a linha
[SUPOSTO: <o que provaria que é falso>]             NÃO verificado, e traz o próprio falsificador
```

**Regra dura:** um fato de que a implementação de uma tarefa **depende** não pode ficar
`[SUPOSTO]`. Ou você mede antes de congelar o plano, ou o primeiro passo daquela tarefa é
medir, escrito assim: *"se der diferente, PARE e escale — não improvise"*. Fato decorativo
pode ser suposto; fato que sustenta um fix, não.

Isso é barato. As três falhas acima custavam um `ls` e duas queries.

### A carga do plano: liste o que ele SUSTENTA, e tente derrubar

A etiqueta acima prova que você **olhou**. Ela não prova que você olhou o caminho inteiro, e
é aí que mora o furo caro: a afirmação que o desenho inteiro apoia em cima.

Antes de congelar, escreva a lista das **afirmações de carga**: as que, se falsas, derrubam
uma decisão estrutural do plano. Elas quase sempre têm forma negativa ou de invariante:

- "isso continua garantido mesmo com a mudança";
- "não existe caminho que faça X";
- "esse comportamento só nasce em Y";
- "desativar Z é seguro porque Z é a única porta".

> **Para uma afirmação de carga, a evidência é uma REFUTAÇÃO TENTADA, não uma citação.**
> Citar a linha que te dá razão é confirmação; procurar a linha que te derruba é verificação.

O método, três passos e nenhum é caro:

1. **Escreva o falsificador em uma frase.** "Isto seria falso se existisse um caminho que
   satisfaça a checagem sem o dado real."
2. **Busque o falsificador, não a confirmação.** Leia a função auxiliar de que a checagem
   depende, não só a linha que a enuncia. Faça `grep` pelo caminho de exceção, pelo
   relaxamento, pelo bypass, pelo `||`. Leia os **testes existentes** daquele arquivo: um
   teste que trava o comportamento permissivo é a prova pronta de que sua invariante não vale.
3. **Puxe a linha real da entidade afetada**, não o agregado. Contagem responde "quantos"; a
   sua afirmação normalmente é sobre "este". Se o plano toca N registros, olhe os N quando N é
   pequeno, e uma amostra nomeada quando não é.

Medido em 2026-08-26, num ciclo de configuração de cliente: o plano afirmava *"o envio
continua exigindo o dado de identidade em qualquer etapa"*, com etiqueta `[LIDO:]` apontando
para o trecho certo da função de política, e a citação estava correta.
A afirmação, não: uma função auxiliar noventa linhas acima aceitava o nome como presente
quando um marcador persistido dizia "esse campo foi pulado", e **um teste do próprio
repositório travava esse comportamento**. Pior, o único registro afetado **já tinha o marcador
gravado**, de um teste feito dias antes. Três verificações de segundos derrubariam a
afirmação: ler o auxiliar, ler o teste vizinho, e dar um `select` na linha. Nenhuma foi feita
porque a afirmação parecia confirmada. Quem achou foi a revisão externa.

### As classes que morderam de verdade — confira estas por nome

1. **Semântica de coluna, flag ou campo. NUNCA infira pelo nome.** `created_at` de uma tabela
   de auditoria parece "quando aconteceu" e significa "quando fechou". Abra a linha e compare
   com um caso conhecido. Este projeto tem uma família inteira de bugs assim
   (`campo_a`, `campo_b`, `campoC`: booleano cujo nome descreve o
   que o lead **disse**, lido como "o estágio **entregou**"). O plano de 26/08 reproduziu, na
   camada de planejamento, exatamente o defeito que ele fora escrito para corrigir.

   A verificação inteira é **uma query**, e ela devolve o veredito sem interpretação:

   ```sql
   select a.created_at, a.processing_time_ms,
          a.created_at - (a.processing_time_ms||' ms')::interval as turno_comecou,
          (select max(m.created_at) from messages m
             where m.conversation_id = a.conversation_id
               and m.direction = 'inbound' and m.created_at < a.created_at) as ultimo_inbound
   from ai_audit_logs a
   where a.conversation_id = '<a conversa do caso>' order by a.created_at;
   ```

   Resultado real do turno da [nome removido]: `created_at 22:58:15.38`, `processing_time_ms 14493`,
   `turno_comecou 22:58:00.888`, e o inbound engolido em `22:58:02.586`. Ou seja: o inbound é
   **posterior ao início** do turno (logo invisível ao motor, e recuperável) mas **anterior ao
   `created_at`** por 13,0 s — cortar no `created_at` o classificaria como "já visto" e o fix
   não faria nada. Nos seis turnos da conversa o atraso variou de 6,5 s a 36,3 s, e dois vieram
   com `processing_time_ms = 0`, caso de borda que sozinho já obriga a exigir que a linha de
   auditoria **emoldure** o outbound.

2. **O fix é no-op?** Antes de escrever a tarefa, pergunte: com o código de hoje, esta
   mudança altera alguma coisa? Um corte que já exclui o alvo, um guard que já não dispara,
   um campo que já vem preenchido. **No-op passa verde** — é a pior falha possível, porque
   produz teste, relatório e commit sem produzir efeito.
3. **O caso prometido realmente dispara o critério novo?** Se o plano diz "o lead X vai
   aparecer na flag Y", rode os critérios de Y contra X **agora**. Foi assim que a [nome removido]
   entrou num item de gate que ela não satisfazia.
4. **Caminho, comando e nome existem?** `ls` no script, `--help` no subcomando, `\d` na
   tabela. Custa segundos e aparece no passo do coordenador, que é onde ninguém testa antes.

5. **Invariante que você promete PRESERVAR.** "A mudança mantém a garantia G" é afirmação
   de carga (ver acima). O comentário do código **não é** evidência de G: comentário envelhece,
   e a contradição entre o comentário e o código é justamente onde o bug mora. Evidência de G é
   o caminho de exceção que você procurou e não achou, mais o teste que hoje trava G.
6. **Emissores de um comportamento que você vai REMOVER.** Quando a tarefa é "a partir de
   agora o sistema não pergunta mais X", a pergunta não é "onde está o X que eu achei", é
   **"quantos lugares conseguem emitir X?"**. Enumere todos antes de dimensionar a tarefa, e
   procure de duas formas, porque elas acham coisas diferentes: pelos **chamadores** da função
   canônica, e pelo **literal do texto** emitido. Emissor que escreve a frase inline não
   aparece na busca por chamador, e é o que sobrevive ao fix. Medido no mesmo ciclo: o plano
   mapeou 1 emissor, existiam 5, e 2 dos que faltavam eram literais escritos dentro de um
   guard. Um teste por emissor, não um teste da função canônica.
7. **Receita copiada de outro contexto.** Reaproveitar um procedimento documentado é certo, e
   ele vem com pré-condições que ninguém reescreve junto. Antes de colar, escreva o que a
   receita **assumia** e confirme que vale aqui. Medido: um `update ... set stage_id = null`
   copiado de uma receita onde os estágios eram **apagados**, aplicado a um caso onde eles
   apenas ficavam inativos. Na receita original o nulo era obrigatório; no caso novo travava o
   fluxo.
8. **Passo novo dentro de pipeline existente.** Escolher a posição pelo nome da abstração
   ("é um guard, vai na cadeia de guards") é como o passo entra cedo demais ou tarde demais.
   **Leia do seu ponto de inserção até o fim do fluxo** e liste tudo que ainda pode mutar o que
   você produziu, ou produzir o estado que você observa. Medido: um passo de fechamento
   colocado "no fim da cadeia" não via as transferências criadas depois dela, e era
   sobrescrito por uma reescrita posterior.
9. **Tarefa que ADIA, SEGURA ou BLOQUEIA uma ação que já existe.** Antes de escrevê-la, ache o
   **ponto único onde a ação acontece, ANTES dos efeitos colaterais**. Se os efeitos já
   ocorreram quando o seu código consegue observar a ação, você não está adiando nada: está
   mentindo para o usuário final e deixando o sistema em estado inconsistente. Se esse ponto
   único não existe, a tarefa não é uma feature, é uma máquina de estado nova. Diga isso e
   corte, ou promova a frente própria.

### O que NÃO dá para decidir no plano — diga isso em vez de fingir

Rigor não é prometer que o plano prevê tudo; é separar o decidível do emergente e escrever a
fronteira. Não são planejáveis, e o plano deve dizê-lo:

- **defeito que depende de uma escolha do modelo** (a LLM decide transferir, ou responde em
  prosa em vez de lista). Não é reproduzível sob demanda: a prova é teste determinístico, e a
  verificação é telemetria de produção;
- **interação entre peças que ainda não existem** — um guard novo cruzando com outro guard só
  se avalia depois de escritos. É para isso que serve o gate adversarial, não o plano;
- **corrida de tempo real** que o harness de teste não reproduz.

Escreva estes como **watchlist do plano**, com o método de verificação que os cobre. Um plano
que promete cobrir o emergente vira álibi; um que declara a fronteira vira mapa.

### Cenário de teste escrito e não executado é HIPÓTESE, não cobertura

Medido no ciclo `2026-08-27-canais-sociais-whatsapp`. Dois cenários E2E foram escritos junto
com o código, revisados como especificação, e **passaram por quatro rodadas de gate
adversarial sem nunca terem rodado**. Na primeira execução, os cinco runs pagos expuseram
**cinco defeitos** — e três deles estavam no próprio cenário ou no harness, não no motor:

- o cenário abria com uma frase que disparava um early-exit determinístico, então provava o
  early-exit e não o comportamento alvo;
- usava um número de telefone que o validador rejeita como lixo, e o turno falharia
  parecendo bug de código;
- o runner exigia um job agendado para provar que algo **não** acontece;
- o runner filtrava o atendente por um critério mais estrito que o da produção;
- e o motor tinha um defeito que só aparece na frase real: um ponto final no fim da frase
  matava a extração do número.

**A regra:** um plano não pode contar um cenário não executado como evidência. Ou o cenário
roda antes do gate, ou ele entra no plano com a etiqueta `[SUPOSTO:]` e o passo do
coordenador diz explicitamente "rodar ANTES de considerar coberto". Uma tabela de cenários
com a coluna "a executar" é uma lista de promessas.

**Corolário para o orçamento:** reserve execuções pagas para *descobrir*, não só para
*confirmar*. O ciclo gastou 9 execuções onde o plano previa 5, e as 4 extras foram as que
acharam os defeitos — o custo estava no lugar certo.

## Fase 1 — decompor

### Níveis de complexidade

Três níveis. O critério é **custo do erro somado à profundidade de raciocínio**, nunca tamanho. Uma tarefa de dez linhas que decide precedência entre regras é complexa. Uma de trezentas linhas de tradução é baixa.

- **Complexa** — o erro é caro ou difícil de detectar: invariante, concorrência, segurança, dado de produção, irreversível. Ou exige segurar muito contexto ao mesmo tempo.
- **Média** — solução conhecida, escopo claro, o erro aparece em teste ou na tela.
- **Baixa** — mecânica, verificável por inspeção, sem decisão de design.

Rubrica completa com exemplos e casos de fronteira: `references/complexity-rubric.md`.

Na dúvida entre dois níveis, suba. O modelo mais forte numa tarefa média custa menos que o retrabalho de uma complexa mal feita.

**O plano nunca nomeia modelo.** Escreve `<MODELO_COMPLEXA>`, `<MODELO_MEDIA>`, `<MODELO_BAIXA>` como placeholder. Quem atribui é o usuário, na hora de executar, porque a escolha depende de custo, disponibilidade e humor do dia, não do plano.

### Ownership de arquivo

Um arquivo, um dono. É isto que impede dois workers paralelos colidirem, e é o item mais barato de esquecer e mais caro de descobrir tarde.

Se duas tarefas precisam do mesmo arquivo, você tem três saídas legítimas e nenhuma quarta:

1. Junte as duas numa tarefa só.
2. Parta o arquivo, e o corte vira parte do plano.
3. Serialize com dependência explícita no grafo.

"As duas mexem e depois a gente concilia" não é saída. Escreva a matriz como tabela, caminho por caminho, e marque-a como normativa.

Arquivos que várias tarefas **leem** mas ninguém escreve não entram no conflito. Diga isso explicitamente, senão alguém serializa à toa.

**A matriz não sai da memória, sai de um traçado.** Listar os arquivos que você leu enquanto
desenhava produz uma matriz que parece completa e não é: ela contém a origem e o destino, e
perde o meio. Para cada dado ou comportamento novo, siga o caminho inteiro e anote **cada
salto**, porque cada salto é um arquivo com dono:

```
onde nasce  ->  quem transporta  ->  quem decide  ->  quem emite  ->  quem consome
```

O salto mais esquecido é o transporte: um objeto de contexto reconstruído no meio do caminho
**descarta silenciosamente** todo campo que ninguém encaminhou de propósito, e aí a sua flag
nova chega `undefined` no destino com todos os testes verdes. Medido em 2026-08-26: uma
matriz de 22 arquivos saiu com 5 faltando, e o que mais doía era exatamente um desses
transportes.

**Depois de escrever a matriz, releia as descrições das tarefas e procure responsabilidade
repetida.** Duas tarefas podem não colidir em arquivo e ainda assim receberem a mesma frase
("resolve a config no bootstrap"). Colisão de responsabilidade é colisão, e aparece mais tarde
e mais cara que a de arquivo.

### Contratos congelados

Este é o item que faz o paralelismo existir. Workers não divergem na ordem das coisas, divergem no formato delas.

Congele, antes da primeira onda: tipos e interfaces compartilhadas, shape de request e response, nomes de chave de i18n, props na fronteira entre dois componentes, e a fixture de casos que serve de fonte da verdade de uma regra de negócio.

Quem escreve é o coordenador, num passo próprio antes de despachar qualquer worker, e commita. Não delegue a um worker o contrato de que os outros dependem.

Escreva literal, em bloco de código completo. Contrato descrito em prosa é contrato não congelado.

## Fase 2 — o grafo

**Ondas.** Uma onda termina exatamente onde o coordenador precisa agir. Descubra o que este projeto proíbe delegar (ver *Regras do projeto*, abaixo): tipicamente git, migration, deploy e publicação. Esses passos viram passos do coordenador, e são eles que definem onde a onda quebra. Não é escolha estética.

Escreva três coisas, sempre:

1. **O grafo**, em ASCII, com as dependências visíveis.
2. **O que roda junto**, por onda.
3. **O que NÃO roda junto, com a razão de cada par.** Sem a razão escrita, alguém vai "otimizar" isso depois e reintroduzir a colisão.

Marque o **caminho crítico**. É o que diz se vale acrescentar worker ou se você só vai acrescentar espera.

**Ordene por dependência de COMPORTAMENTO, não por custo.** A tentação é pôr primeiro o que é
barato e reversível, tipicamente configuração, e deixar o código para depois. Isso inverte a
ordem real: configuração que liga um comportamento cujo código ainda não existe deixa o
sistema num estado que ninguém desenhou, meio novo e meio velho, **em produção**. A regra
geral: primeiro o que é aditivo e inerte (schema, código com default igual ao de hoje), depois
o que entrega, e por último a chave que LIGA. Esse último passo é o cutover, e ele deve ser
reversível numa linha.

**Corolário que economiza uma rodada inteira:** se, ao escrever um passo de validação, você
já sabe apontar um item dele que vai falhar por causa de outra tarefa ainda não feita, a
ordem está errada. Não escreva "este item vai falhar aqui, é esperado" — isso é um gate que
não guarda nada. Reordene.

## Fase 3 — gates

Um gate não é uma revisão. Revisão acontece depois e informa; gate acontece antes e bloqueia.

Posicione gate imediatamente **antes** de cada passo irreversível: aplicar migration em produção, deployar, publicar. Migration aplicada não tem `git revert`, e uma revisão que chega depois disso só documenta o estrago.

Um gate é uma tarefa como as outras, com nível, dono e dependência. O que o distingue é que o passo do coordenador que ele guarda não pode acontecer sem o resultado dele. Escreva isso no plano com essas palavras.

### Revisão externa: opcional no meio-termo, PADRÃO no aparato completo

Quando o usuário pedir, ou quando a feature for grande o bastante para valer, ofereça uma revisão externa read-only antes de executar. Não fixe qual agente ou modelo faz.

**No aparato completo ela deixa de ser cortesia e vira parte do plano**, pelo motivo mais
simples possível: quem escreveu o plano é o pior revisor dele. Medido em 2026-08-26, num plano
com evidência medida, contratos congelados e auto-revisão feita: **a auto-revisão achou zero
furos e a revisão externa achou sete**, cinco deles confirmados por mim no código, um deles
capaz de mandar foto de um lead sem identidade nenhuma. Não foi falta de rigor na forma; foi
que confirmação e verificação parecem iguais por dentro.

Duas coisas fazem a revisão render, e as duas custam pouco:

- **Peça a refutação das suas afirmações de carga, nomeadas.** Não mande "revise o plano".
  Liste as três ou quatro afirmações que sustentam o desenho e peça para tentarem derrubar cada
  uma, com `arquivo:linha`. A pergunta mais produtiva, sempre a última: *"o que está faltando
  aqui que eu não teria como notar, porque fui eu que escrevi?"*
- **Diga o que o revisor NÃO tem.** Se ele não tem acesso ao banco, ele vai marcar como
  hipótese aquilo que você consegue medir em uma query. Resolva essas hipóteses você mesmo em
  vez de descartá-las: foi assim que duas "hipóteses não verificadas" viraram fatos decisivos
  em 2026-08-26, uma confirmando um bloqueador e outra derrubando um risco inventado.

O veredito da revisão entra no plano, com o que foi aceito, o que foi recusado e por quê. Plano
revisado sem registro da revisão obriga a próxima pessoa a refazer o mesmo trabalho.

Procedimento, mandato read-only, e como verificar depois que o revisor realmente não escreveu: `references/external-review.md`.

**Ao receber o relatório, não valide os bloqueadores por deferência.** Verifique cada um você mesmo, separe o que é buraco real do que é decisão de negócio, e leve as decisões de negócio ao usuário com resumo e recomendação. Um revisor competente ainda erra de tamanho: superdimensiona o que não tem usuário e subdimensiona o que já está quebrado.

## Fase 4 — fecho

Escreva os passos do coordenador entre as ondas e depois da última: o que ele aplica, verifica, commita e deploya, em ordem, com o comando.

Termine com os portões de entrega do projeto. Descubra quais são (ver abaixo) em vez de assumir: pode ser deploy, migration, bundle OTA, build nativo, publicação em loja. E inclua a documentação que este projeto exige atualizar no mesmo commit da mudança, se exigir.

## Auto-revisão antes de entregar

Duas listas, e a primeira é a que faltava. Estrutura impecável em cima de fato falso continua
sendo plano falso.

**Verdade — cada item vale um `ls` ou uma query:**

- Todo fato do plano tem etiqueta `[MEDIDO:]`, `[LIDO:]` ou `[SUPOSTO:]`?
- Nenhum `[SUPOSTO:]` sustenta a implementação de uma tarefa? (se sustenta: medir agora, ou
  virar o primeiro passo da tarefa com "se der diferente, PARE e escale")
- Toda coluna, flag ou campo citado teve a **semântica conferida na linha real**, e não
  deduzida do nome?
- Para cada fix: com o código de hoje, ele muda alguma coisa — ou é **no-op que passa verde**?
- Todo caso que o plano promete que vai disparar um critério novo foi rodado contra esse
  critério?
- Todo caminho, comando e subcomando do plano existe? (inclusive os dos passos do coordenador)
- O que é emergente está na **watchlist**, com método de verificação, em vez de prometido?
- As **afirmações de carga** estão listadas, e cada uma passou por refutação TENTADA, não por
  citação que a confirma?
- Toda invariante que o plano promete preservar tem o caminho de exceção procurado, e os
  **testes existentes** daquele arquivo lidos?
- Para cada comportamento que o plano REMOVE: os emissores foram contados pelos dois lados,
  chamadores da função **e** literal do texto?
- Toda receita copiada de outro contexto teve a pré-condição dela conferida aqui?
- Todo passo novo inserido em pipeline existente foi posicionado depois de ler **até o fim** do
  fluxo, e não pelo nome da abstração?
- As linhas reais das entidades afetadas foram olhadas, e não só a contagem?

**Estrutura:**

- Toda tarefa tem nível, dono e dependências explícitas?
- Todo arquivo tocado aparece na matriz de ownership, com um dono só, **derivado do traçado
  do caminho** e não da memória do que você leu?
- Nenhuma responsabilidade aparece em duas tarefas, mesmo sem colisão de arquivo?
- A ordem das ondas segue dependência de **comportamento**, com o que LIGA a mudança por
  último e reversível?
- Nenhum passo de validação tem item que você já sabe que vai falhar por causa de tarefa
  posterior?
- Todo contrato de que dois ou mais workers dependem está escrito literal e datado de antes da onda 1?
- Todo passo irreversível tem gate antes?
- Todo par "não pode junto" tem a razão escrita?
- Algum worker precisa rodar comando que este projeto proíbe delegar?
- O caminho crítico está marcado?
- Sobrou placeholder de modelo, e nenhum modelo nomeado?

## Regras do projeto: de onde saem

Esta skill é genérica de propósito. O que a torna afiada em cada repositório vem de lá, não daqui.

Leia `CLAUDE.md` e `AGENTS.md` do projeto, e `.claude/plan-profile.md` se existir. Procure especificamente por:

- o que subagente **não** pode rodar neste checkout;
- como mudança de schema é aplicada, e o que a torna irreversível;
- quais são os portões de entrega;
- que documentação precisa acompanhar a mudança no mesmo commit;
- convenções de idioma, de commit e de nomeação.

Se o projeto não tiver esses arquivos, pergunte ao usuário estas quatro coisas antes de escrever o plano. Elas mudam o grafo, não são detalhe.

## Onde salvar

Siga a convenção do projeto. Procure planos anteriores (`docs/**/plans/`, `docs/superpowers/plans/`, `plans/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/plans/AAAA-MM-DD-<topico>.md` e diga ao usuário que você criou a convenção.

Esqueleto pronto para copiar: `references/plan-template.md`.

Depois de escrever, commite o plano e **pare**. Não suba worker. Se o usuário quiser executar, a skill é `orchestrating-execute`.
