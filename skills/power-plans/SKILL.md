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
  `spec-interview`: design aprovado, invoque esta. Serve qualquer projeto — as
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

Medido num ciclo de auditoria de turno de atendimento: o snapshot de evidência tinha 17 KB, media o
problema ao segundo, citava `arquivo:linha` e contava frequência em produção. Ainda assim o
plano saiu com **três afirmações falsas**, e as três eram do lado da *prescrição*:

| afirmação do plano | realidade | custo |
|---|---|---|
| "corte em `ai_audit_logs.created_at`" | é quando o turno **fechou**, ~13 s DEPOIS do inbound a recuperar. O corte cru excluiria exatamente a mensagem alvo | **o fix seria um no-op, e passaria verde** |
| "o registro auditado aparece na flag de teto impossível" | `max=20000` é plausível e não bate em nenhum dos 3 critérios congelados | um worker gastou um ciclo de dispatch para escalar |
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

**Norma citada não é fato verificado.** Quando o plano invoca uma regra da documentação do
projeto ("o checklist manda X", "a convenção aqui é Y"), `[LIDO: checklist.md:44]` prova que o
**documento** diz — não que o **código** faz. Documentação envelhece; o código é a verdade. Norma
que decide uma tarefa vira `[MEDIDO:]` contra o repositório antes de entrar no plano.

Medido em 2026-09-03: um plano citou a regra "não use chave estrangeira para a tabela de usuários
do auth", vinda do checklist de segurança do próprio projeto. A medição no schema devolveu **7 de
7 tabelas comparáveis fazendo exatamente isso, e nenhuma fazendo o contrário**. Obedecer o
documento teria feito da tabela nova a única exceção do banco. Quem estava errado era o documento,
e ele foi corrigido no mesmo trabalho. Custo da verificação: uma query.

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

> **A linha só fecha com a CONTAGEM do falsificador.** Escreva a consulta ou o `grep` que
> conta o caso que derruba a afirmação, e o número que ela devolveu, mesmo que seja zero.
> Contagem que confirma a afirmação mede outra coisa e não fecha a linha.

Medido em 2026-09-12: uma afirmação de carga dizia *"os vínculos persistidos cobrem a
duplicação entre dois provedores"*, o falsificador estava escrito na frase certa (*"vínculo
não existe"*), e a coluna de resultado trazia `[MEDIDO: 149 linhas vinculadas]`. A consulta
que contava o falsificador tinha a mesma forma, com um `not exists` a mais, e devolvia 32
pares sem vínculo em 90 dias. Ninguém a rodou porque a tabela aceitava qualquer `[MEDIDO:]`.
Quem a rodou foi a revisão externa, e virou bloqueador.

### As classes que morderam de verdade — confira estas por nome

1. **Semântica de coluna, flag ou campo. NUNCA infira pelo nome.** `created_at` de uma tabela
   de auditoria parece "quando aconteceu" e significa "quando fechou". Abra a linha e compare
   com um caso conhecido. Este projeto tem uma família inteira de bugs assim
   (um booleano cujo nome descreve o que o lead **disse**, lido como "o que o estágio
   **entregou**"). O plano de 26/08 reproduziu, na
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

   Resultado real do turno auditado: `created_at 22:58:15.38`, `processing_time_ms 14493`,
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
   aparecer na flag Y", rode os critérios de Y contra X **agora**. Foi assim que o registro
   entrou num item de gate que ele não satisfazia.
4. **Caminho, comando e nome existem?** `ls` no script, `--help` no subcomando, `\d` na
   tabela. Custa segundos e aparece no passo do coordenador, que é onde ninguém testa antes.
   **Arquivo NOVO não tem `ls`:** o caminho dele cita o irmão existente do mesmo tipo e a
   configuração que o descobre (diretório de testes, `include`, glob), os dois com `[LIDO:]`.
   Caminho novo deduzido de uma norma escrita é `[SUPOSTO]`. Medido em 2026-09-12: o plano
   pôs o teste ponta a ponta novo no diretório de artefatos que a documentação do projeto
   mandava usar, fora do diretório de testes do runner; o runner listaria zero testes e a
   tarefa entregaria um arquivo que nunca roda. Havia dezenas de irmãos no diretório certo.
   **E saída de `--help` cortada não prova ausência:** `| head -N` trunca a lista, e o cabeçalho
   que você usa para recortar pode não existir naquela versão. Rode o `--help` inteiro ou `grep`
   pelo nome do subcomando. Medido em 2026-09-21: concluir "esse comando não existe" a partir de
   um recorte fez o plano proibir, no brief de TODAS as tarefas, uma capacidade que o executor
   tinha — e o coordenador passou a executá-la à mão por ele, 13 vezes.

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
   **Validação, filtro ou gate novo sobre uma saída que já existe É remoção**, mesmo que a
   spec o descreva como garantia nova. A medição é no histórico persistido: quanto da saída
   de hoje o gate rejeitaria, em uma consulta. Medido em 2026-09-12: um contrato do plano
   proibia número fora de fatos autorizados num campo de texto livre; os prompts em produção
   mandavam citar números, e 153 de 209 respostas do mês tinham dígito. Nenhum documento
   tinha olhado a saída atual, e duas tarefas paralelas teriam implementado contratos
   incompatíveis.
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

10. **Tarefa que SUBSTITUI um módulo por outro (receita própria no lugar da compartilhada).**
    A ordem de resolução do alvo não é o inventário do módulo. O módulo substituído tem
    **gatilhos** (quando ele age sem ninguém pedir), e cada um é um item da matriz de
    consumidores, com decisão escrita: "mantido", "removido porque X", "coberto por Y".
    Medido em 2026-09-01/02, num ciclo que isolava uma vertical de negócio nova: o plano do
    pré-LLM próprio da vertical listou a ordem do alvo (vínculo → opção ativa → texto) e os
    gatilhos de pedido de foto e de nome no texto, e omitiu o gatilho "interesse já vinculado"
    do módulo da vertical antiga que estava sendo substituído (lead já vinculado + zero opção
    → apresentar com foto). Um gate adversarial, sete tarefas, suíte
    verde por nome e três cenários novos pagos passaram; quem achou foi o cenário de REGRESSÃO
    da vertical, que reprovou no turno 3 porque uma flag de entrega só era gravada por um
    caminho que a mudança tornara raro. A lista
    de gatilhos custa um `grep` por `reason:` no módulo antigo; a omissão custou um run pago,
    uma onda de correção e um redeploy.

11. **Tarefa que INSERE uma peça nova dentro de tela, página ou módulo que já existe.** A matriz
    de consumidores registra o ponto de inserção ("`X.tsx` — novo consumidor: uma linha") e isso
    *parece* resolver o item. Não resolve: **o que você insere herda o estado do hospedeiro**, com
    os defeitos dele junto. Antes de dimensionar a tarefa, leia o que o hospedeiro já faz com os
    valores que a sua peça vai consumir — a data, o fuso, o usuário, o filtro, a unidade.
    Medido em 2026-09-03: a spec descrevia a virada de meia-noite **corretamente** (*"a data é
    resolvida a cada consulta pelo fuso do aparelho"*), e a tela hospedeira fixava a data no
    `mount` desde muito antes da branch. O card novo nasceu certo e herdou o defeito: com o app
    aberto na virada, o registro ia para o dia anterior. Nenhum FR falhou, nenhum contrato foi
    violado — o hospedeiro é que não tinha sido lido. Custa um `git show <merge-base>:<arquivo>`.

12. **"Importar a mesma função" não é paridade quando a ENTRADA mora no chamador.** Reaproveitar
    o predicado puro do motor num consumidor externo parece eliminar a duplicação; se a seleção,
    o filtro ou o enriquecimento do dado acontecem antes de a função ser chamada, o consumidor
    reproduz o veredito só se reproduzir também a entrada. Medido em 2026-09-04: o plano mandava
    o coletor da auditoria diária importar `evaluateItemPresentation` do motor; a revisão externa
    mostrou que o motor filtra `is_ai_generated`, exclui notas internas e **enriquece as opções
    com preço do catálogo** dentro do probe (`item-presentation.ts:681-760`), e reproduziu um
    veredito invertido só pela ausência do preço. Antes de prescrever "importe X", leia quem
    prepara o argumento de X e faça a preparação ser exportada junto.

13. **Teste do consumidor que fabrica o campo que o produtor real não emite.** Um fake que
    monta `{ sent: false, error: "..." }` e um worker que lê exatamente isso passam verdes
    enquanto o corpo HTTP real nunca carrega `error`. Medido em 2026-09-04: o corpo final do
    `ai-chat` tinha `sent` e não tinha `error` (`index.ts:4593`), e o early-exit não devolvia nem
    `sent`; o contrato do plano dependia dos dois. Regra: o teste do consumidor recebe a saída
    **do produtor real** (fixture gerada pelo teste do produtor), e o `Pronto quando` diz de onde
    ela vem. O contrato congela o shape produzido, não o shape desejado.

14. **Remover um evento/linha de log exige procurar leitores por TEMPO, não só por chave.** O
    grep pela chave que só a linha "duplicada" carregava (`idempotent_skip_notify`) deu zero
    leitores, e a afirmação de carga "ninguém consome a segunda linha" passou. O consumidor real
    lia `order by triggered_at desc limit 1` — a **última** linha, qualquer que fosse
    (`evolution-webhook/index.ts:1005`, referência de abandono para reativar; reproduzido na
    fronteira das 24 h). Regra: para toda linha que o plano deixa de gravar, procure `order by
    … desc`, `limit 1`, `max(`, `last` e `lag(` sobre a tabela, além dos campos da linha.


15. **Plano que promete um ESCRITOR ÚNICO ("ponto de estrangulamento").** "A partir daqui toda
    escrita sai de um lugar só" é afirmação de carga, e ela se sustenta com a lista dos lugares
    que escrevem **hoje** — não com o lugar que você enxergou lendo o fluxo principal.
    Inventariar de verdade é listar os **sites de escrita** no alvo: todos os chamadores da
    função que você vai proteger, mais as rotinas que o próprio armazenamento executa sozinho
    (gatilhos, jobs, hooks). Conferir que os arquivos existem não é inventário.
    Medido em 2026-09-21: o plano reconheceu a família já na primeira rodada do gate e exigiu o
    ponto único — mas sobre o caminho visível. Existia um segundo escritor, um auxiliar privado
    que fazia a própria escrita e decidia a própria autorização, e ele só apareceu na rodada 2:
    custou uma rodada de gate mais uma onda inteira de correção. Se o inventário acusa N
    escritores, a tarefa nasce exigindo **um**; se você não consegue enumerá-los, o plano não
    pode prometer o ponto único, e dizer isso é mais barato que descobrir no gate.

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

### Vermelho pelo motivo errado também não é cobertura

Medido no ciclo `2026-09-14-auditoria-da23`: quatro dos sete cenários E2E novos
deram o primeiro vermelho pelo motivo ERRADO, e dois chegaram a dar verde sem
provar nada:

- a LLM **reparava** o defeito no mesmo turno (lia as duas mensagens no
  histórico e sobrescrevia a cidade fundida via tool) — verde no código velho;
- o abridor do cenário **invalidava o próprio fixture** (`"sobre isso?"` e
  `"ele"` sem contexto supersediam a atribuição do anúncio) — vermelho de
  setup, não de defeito;
- o turno anterior já entregava a foto, e o lock anti-spam segurava o reenvio
  mesmo com o fix — o sinal "foto enviada" não discriminava nada;
- fraseado da LLM variava (faixa vs mínimo, nome do empreendimento, paráfrase
  da promessa) e quebrava asserções que pinavam texto, não comportamento.

**A regra:** vermelho/verde de cenário E2E só conta com a CAUSA inspecionada.
No vermelho, abra o report e confirme que a falha é a asserção do defeito (tool
call, estado, sinal determinístico) — não derailment de setup, transferência
discricionária ou fraseado. No verde contra código velho, desconfie primeiro do
cenário, não comemore: confira se o caminho do defeito realmente engajou. E ao
escrever a asserção, prefira o sinal que nenhum agente discricionário pode
reescrever (efeito de guard, flag, tool sintética) ao texto da resposta ou ao
estado final que a LLM pode reparar.

## Fase 1 — decompor

### Níveis de complexidade

Três níveis. O critério é **custo do erro somado à profundidade de raciocínio**, nunca tamanho. Uma tarefa de dez linhas que decide precedência entre regras é complexa. Uma de trezentas linhas de tradução é baixa.

- **Complexa** — o erro é caro ou difícil de detectar: invariante, concorrência, segurança, dado de produção, irreversível. Ou exige segurar muito contexto ao mesmo tempo.
- **Média** — solução conhecida, escopo claro, o erro aparece em teste ou na tela.
- **Baixa** — mecânica, verificável por inspeção, sem decisão de design.

Rubrica completa com exemplos e casos de fronteira: `references/complexity-rubric.md`.

Na dúvida entre dois níveis, suba. O modelo mais forte numa tarefa média custa menos que o retrabalho de uma complexa mal feita.

**O plano nunca nomeia modelo.** Escreve `<MODELO_COMPLEXA>`, `<MODELO_MEDIA>`, `<MODELO_BAIXA>` e `<MODELO_GATE>` como placeholder. Quem atribui é o usuário, na hora de executar, porque a escolha depende de custo, disponibilidade e humor do dia, não do plano.

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

**Linha NOVO cita o irmão.** Arquivo que ainda não existe entra na matriz com o irmão existente
do mesmo tipo e a configuração que o descobre, os dois com `[LIDO:]`. Sem isso o caminho é
`[SUPOSTO]`, e o `ls` da auto-revisão não tem o que conferir (classe 4, acima).

**Depois de escrever a matriz, releia as descrições das tarefas e procure responsabilidade
repetida.** Duas tarefas podem não colidir em arquivo e ainda assim receberem a mesma frase
("resolve a config no bootstrap"). Colisão de responsabilidade é colisão, e aparece mais tarde
e mais cara que a de arquivo.

### Contratos congelados

Este é o item que faz o paralelismo existir. Workers não divergem na ordem das coisas, divergem no formato delas.

Congele, antes da primeira onda: tipos e interfaces compartilhadas, shape de request e response, nomes de chave de i18n, props na fronteira entre dois componentes, e a fixture de casos que serve de fonte da verdade de uma regra de negócio.

Quem escreve é o coordenador, num passo próprio antes de despachar qualquer worker, e commita. Não delegue a um worker o contrato de que os outros dependem.

Escreva literal, em bloco de código completo. Contrato descrito em prosa é contrato não congelado.

**Campo derivado tem tabela de derivação por origem.** Todo campo do contrato que não é cópia
1:1 de uma coluna vem com a regra por origem, e cada origem com a sua medição na linha real.
Medido em 2026-09-12: o contrato tinha `mode: outdoor | treadmill | unknown` sem dizer de onde
vinha; a spec tinha medido esteira num provedor e não olhado o sinal de esteira do outro, onde
149 corridas em esteira chegavam com ganho de elevação zero e virariam "rua plana" pela regra
literal, formando par com corridas de rua.

**Contrato não é mais restrito que o FR que implementa.** Se o plano aperta uma regra que a
spec enuncia mais solta, isso é decisão com autoria na spec, não detalhe técnico do plano.

### Critério de pronto: é contrato também, e cola literal

O `Pronto quando` de cada tarefa **é o cenário de aceitação do FR**, copiado da spec, não uma
paráfrase escrita agora. Vale aqui a frase da seção acima, sem mudar uma palavra: descrito em
prosa, ele é reinventado por quem despacha.

**"Verificável" não basta.** *"Quando `vitest run x.test.ts` passar"* é verificável e não diz
**o que** o teste tem de afirmar — quem escreve o teste decide, pelo que entendeu. *"Dado o aviso
visível, quando tocar Desfazer, então **aquela linha** é apagada"* é o mesmo critério com a
semântica dentro, e é a diferença entre apagar por identidade e apagar por predicado.

Medido em 2026-09-03 (ciclo `contador-agua`): a spec tinha 13 FRs, cada um com cenário
executável, e cobria corretamente virada de meia-noite, duplicação de fórmula e semântica de
campo nulo. O plano citava **6 dos 13 FRs zero vezes** e não tinha **nenhum** `Pronto quando` —
porque as tarefas foram compactadas numa tabela (`| id | tarefa | nível | dono | arquivos |`), e
coluna que não existe não é preenchida. O coordenador então escreveu o critério de cada briefing
de cabeça, relendo a spec. Foi nessa releitura que nasceu o defeito mais caro do ciclo: um campo
que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing, e dias de
descanso ganharam 300 ml que não existiam.

> **Coordenador improvisando critério de pronto É o defeito.** E ele só improvisa quando não há
> o que copiar. O lugar de consertar isso é aqui, não lá.

Compactar tarefas em tabela é legítimo, densidade ajuda. Mas então **a tabela carrega as colunas
`FR` e `Pronto quando`**. O formato é escolha sua; as duas colunas não são.

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

**Um gate por plano**, sobre o candidato integrado, imediatamente **antes** do primeiro passo
irreversível: aplicar migration em produção, deployar, publicar. Migration aplicada não tem `git
revert`, e uma revisão que chega depois disso só documenta o estrago. Um segundo gate só quando há
um segundo passo irreversível com superfície própria (uma publicação de frontend separada do
deploy de backend). Nunca um gate por onda: o que guarda a onda é o aceite do coordenador
(`orchestrating-execute`, seção *Dois mecanismos de qualidade*). Escala parcial ou mínima: sem
gate. Medido em 20 e 21/09/2026: quatro ondas com um gate por onda rodaram cinco gates e nove
tarefas de correção; seis tarefas com um gate rodaram um, corrigiram com teste e publicaram na
mesma noite.

Um gate é uma tarefa como as outras, com nível, dono e dependência. O passo do coordenador que
ele guarda só acontece depois de o gate ter rodado e de as correções aceitas passarem na suíte.
**BLOQUEIA não pede segunda rodada; pede correção com teste.** Escreva isso no plano com essas
palavras: "C<z> não acontece sem a aprovação do gate" é a frase que faz o executor chamar o
revisor de novo até ouvir PASSA.

**O plano também declara o orçamento do advisor, sem agendar consulta nenhuma.** O advisor
(`orchestrating-execute`, seção *O advisor*) é a segunda opinião de rumo que o coordenador
consulta quando a lista do gate pede correção de mecanismo, quando um achado contradiz contrato
congelado, ou ao montar opções para o usuário. Roda no modelo `<MODELO_GATE>`, o mesmo do gate,
com teto de uma consulta por veredito de gate. A consulta é emergente e não se planeja; o
teto e o modelo, sim: entram na tabela de níveis (linha `Gate / Advisor`) e no §7, como no
esqueleto.

### Revisão externa da spec e do plano: recomendada, e quem decide é o usuário

Uma revisão externa read-only da spec e do plano, por outro agente ou outro modelo, antes de
executar, é **recomendada e opcional**. Quem decide se ela acontece, e com qual modelo, é o
usuário: no pedido que abriu o ciclo ("use tal modelo para a revisão adversarial") ou na entrega
do plano. A skill recomenda; não agenda.

Por que recomendar: quem escreveu o plano é o pior revisor dele. Medido em 2026-08-26, num plano
com evidência medida, contratos congelados e auto-revisão feita, **a auto-revisão achou zero furos
e a revisão externa achou sete**, cinco confirmados no código, um deles capaz de mandar foto de um
lead sem identidade nenhuma. Medido em 2026-09-12: quatro bloqueadores, três documentais e uma
decisão do usuário. Medido em 2026-09-21: oito bloqueadores, todos confirmados no código e no
banco antes de qualquer linha escrita. Não foi falta de rigor na forma; confirmação e verificação
parecem iguais por dentro.

Como oferecer, ao entregar o plano, em uma linha: *"Recomendo revisão externa porque <o que este
plano tem de caro: dado de produção, N tarefas em paralelo, invariante que ele promete preservar>.
Quer? Se sim, diga o modelo."* Se o usuário já nomeou o modelo no pedido, não pergunte de novo:
rode a revisão pelo procedimento de `references/external-review.md` e entregue o plano já
adjudicado. Se ele não pediu, registre "não solicitada" no §0.1 e pare. Feature pequena: diga que
não paga.

**A revisão nunca entra no grafo do plano.** Não existe tarefa `S0 — revisão do plano`, nem
"bloqueia a onda 1". O executor lê o grafo como lista de trabalho, e uma revisão ali dentro vira a
primeira coisa que ele despacha, tenha o usuário pedido ou não. Medido em 2026-09-22: um plano com
a revisão no grafo, executado sem pedido de revisão, abriu o ciclo com um revisor no ar e nenhum
worker. Gate (`S<n>`) é outra coisa: revisa código já escrito, antes de um passo irreversível, e
mora na seção acima.

Duas coisas fazem a revisão render, e as duas custam pouco:

- **Peça a refutação das suas afirmações de carga, nomeadas.** Não mande "revise o plano".
  Liste as três ou quatro afirmações que sustentam o desenho e peça para tentarem derrubar cada
  uma, com `arquivo:linha`. Cada afirmação chega com a consulta do falsificador já rodada e a
  contagem dela; o que você pede é o que essa consulta não viu, não a primeira execução dela.
  A pergunta mais produtiva, sempre a última: *"o que está faltando
  aqui que eu não teria como notar, porque fui eu que escrevi?"*
- **Diga o que o revisor NÃO tem.** Se ele não tem acesso ao banco, ele vai marcar como
  hipótese aquilo que você consegue medir em uma query. Resolva essas hipóteses você mesmo em
  vez de descartá-las: foi assim que duas "hipóteses não verificadas" viraram fatos decisivos
  em 2026-08-26, uma confirmando um bloqueador e outra derrubando um risco inventado.

O veredito da revisão entra no plano, com o que foi aceito, o que foi recusado e por quê. Plano
revisado sem registro da revisão obriga a próxima pessoa a refazer o mesmo trabalho. Registre
também o custo de cada bloqueador aceito: documental, decisão do usuário ou redesenho. É esse
número, não o veredito, que diz se a spec e o plano estavam sãos.

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
  deduzida do nome? Campo derivado de mais de uma origem: uma conferência por origem?
- Para cada fix: com o código de hoje, ele muda alguma coisa — ou é **no-op que passa verde**?
- Todo caso que o plano promete que vai disparar um critério novo foi rodado contra esse
  critério?
- Todo caminho, comando e subcomando do plano existe? (inclusive os dos passos do coordenador)
  Todo arquivo NOVO cita o irmão existente e a configuração que o descobre?
- O que é emergente está na **watchlist**, com método de verificação, em vez de prometido?
- As **afirmações de carga** estão listadas, e cada uma passou por refutação TENTADA, não por
  citação que a confirma? A linha traz a **contagem do falsificador**, não a que confirma?
- Toda invariante que o plano promete preservar tem o caminho de exceção procurado, e os
  **testes existentes** daquele arquivo lidos?
- Para cada comportamento que o plano REMOVE: os emissores foram contados pelos dois lados,
  chamadores da função **e** literal do texto? Validação ou gate novo sobre saída existente
  contou como remoção, com a medição no histórico persistido?
- Toda receita copiada de outro contexto teve a pré-condição dela conferida aqui?
- Todo passo novo inserido em pipeline existente foi posicionado depois de ler **até o fim** do
  fluxo, e não pelo nome da abstração?
- As linhas reais das entidades afetadas foram olhadas, e não só a contagem?

**Estrutura:**

- **Mecânico, e é o único desta lista que devolve número em vez de opinião:** todo `FR-n` da spec
  aparece em pelo menos uma tarefa, e toda tarefa tem `Pronto quando` copiado de um cenário — ou
  a marca explícita *"infra, sem FR"*?

  ```bash
  for n in $(grep -o 'FR-[0-9]\+' <spec> | sort -u -V); do
    printf '%-6s plano=%s\n' "$n" "$(grep -cw "$n" <plano>)"
  done
  ```

  **`-w` não é enfeite:** sem ele `FR-1` casa dentro de `FR-10`, e o requisito que ninguém citou
  aparece como coberto — o falso passe cai justamente no FR de número baixo, que costuma ser o
  comportamento central da feature.

  Os outros itens são de julgamento, e julgamento aprova o que ele mesmo escreveu. `plano=0` é um
  requisito que nenhum worker vai ver. Rode antes de entregar o plano, e de novo no preflight da
  execução.
- Toda tarefa tem nível, dono e dependências explícitas?
- Todo arquivo tocado aparece na matriz de ownership, com um dono só, **derivado do traçado
  do caminho** e não da memória do que você leu?
- Nenhuma responsabilidade aparece em duas tarefas, mesmo sem colisão de arquivo?
- A ordem das ondas segue dependência de **comportamento**, com o que LIGA a mudança por
  último e reversível?
- Nenhum passo de validação tem item que você já sabe que vai falhar por causa de tarefa
  posterior?
- Todo contrato de que dois ou mais workers dependem está escrito literal e datado de antes da onda 1?
- Nenhum contrato é mais restrito que o FR que implementa? Se é, a decisão está na spec, com autoria?
- O gate é um por plano, antes do primeiro passo irreversível, e nenhuma onda tem gate próprio?
- Todo par "não pode junto" tem a razão escrita?
- Algum worker precisa rodar comando que este projeto proíbe delegar?
- O caminho crítico está marcado?
- Sobrou placeholder de modelo, e nenhum modelo nomeado?
- A tabela de níveis tem a linha `Gate / Advisor` com `<MODELO_GATE>`, e o §7 traz o orçamento do
  advisor (uma consulta por veredito de gate)?
- A revisão externa da spec e do plano está FORA do grafo (nenhum `S0`, nenhum "bloqueia a onda
  1"), e o §0.1 registra a revisão feita ou "não solicitada"?

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

Siga a convenção do projeto. Procure planos anteriores (`docs/plans/`, `docs/**/plans/`, `plans/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/plans/AAAA-MM-DD-<topico>.md` e diga ao usuário que você criou a convenção.

Esqueleto pronto para copiar: `references/plan-template.md`.

Depois de escrever, commite o plano, ofereça a revisão externa em uma linha (Fase 3) e **pare**. Não suba worker. Se o usuário quiser executar, a skill é `orchestrating-execute`.
