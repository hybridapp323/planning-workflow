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

**O critério é o RISCO da mudança, não a superfície que ela toca.** Publicar uma função ou um
serviço se desfaz republicando a versão anterior; isso sozinho não sobe o nível. O que sobe é o que
não se desfaz, o que atravessa donos e o que protege dado de terceiros.

| Escala | Quando | O que fazer |
| --- | --- | --- |
| **Mínima** | Um defeito ou uma família, um dono da decisão, nenhum contrato novo entre tarefas, **sem** migração de schema e sem escrita em dado de produção, reversível por revert + republicação | Plano mínimo (abaixo) e implemente. Sem ondas, sem gate. |
| **Parcial** | Duas ou mais tarefas com donos diferentes, **ou** um contrato que uma tarefa produz e outra consome | Níveis, ownership de arquivo e `Pronto quando` por tarefa. Sem ondas nem gate. |
| **Completa** | Migração, escrita em dado de produção ou outro passo irreversível, **ou** invariante de segurança, permissão ou isolamento entre clientes, **ou** trabalho genuinamente paralelo em arquivos disjuntos | Fases 0 a 4, com um gate antes do passo irreversível. |

Diga ao usuário qual dos três você escolheu, e por quê, antes de escrever o plano. Se ele discordar, ele corrige agora e não depois de vinte minutos de documento.

Medido em 60 dias de um projeto que publica a mesma função várias vezes por dia: o critério antigo
("toca edge function ou deploy → aparato completo") mandou ondas e gate para consertos de um
arquivo, e a documentação de ciclo somou 227 mil linhas contra 92 mil de código de produção;
um único ciclo produziu 13,8 mil linhas em 127 arquivos para 45 requisitos, e outro já tinha 10,6
mil linhas de documento contra 2,4 mil de código antes de executar.

### O plano mínimo: sai a cerimônia, fica a prova

Escala mínima não é "sem prova". O plano cabe numa tela e tem, cada um com `arquivo:linha` ou
consulta:

1. **Causa**, com a evidência que a mostra (não o sintoma do relatório).
2. **Arquivos** que mudam.
3. **Quem mais lê ou emite isto:** uma linha com os outros consumidores e emissores do que muda.
   Uma mudança de um arquivo num módulo compartilhado alcança todos os chamadores dele.
4. **Teste que falha com o fix neutralizado.**
5. **Camada de prova** (ver *Critério de pronto*): a mais barata que exercita o consumidor real.
6. **Publicação e rollback:** o comando e a versão para onde se volta.

Se para escrever o item 3 você precisar de mais de um dono ou de um contrato novo, a escala não era
mínima: suba.

### Um pedido, uma família

Quando a entrada é um relatório com vários achados (auditoria, triagem, lista de bugs), agrupe por
**família**: achados que têm a mesma causa e o mesmo dono da decisão. **Um plano por família**, com
a família no título. Plano que mistura famílias sem relação é recortado antes de escrever: cada
família a mais multiplica leituras, contratos, fixtures e rodadas de gate, e nenhuma delas fica
mais bem consertada por estar junto. O urgente sai já; o resto segue a cadência que o projeto
definir. Vale para a spec que chega: spec que junta famílias sem relação é recortada no mesmo
passo (Fase 0, *Validar a spec*), e cada família segue com o seu plano.

Número de requisitos é **alerta, não bloqueio**: passou de uns dez, confira se não são duas famílias.
Mudanças que precisam ser atômicas ficam juntas mesmo assim, e o plano diz por quê. Medido no mesmo
projeto: requisitos por ciclo subiram de 5 para 45 em um mês, sempre juntando o relatório inteiro.

## Fase 0 — evidência antes de plano

O erro caro não é planejar errado. É planejar em cima de suposição que ninguém checou, porque o plano fica coerente, convincente e falso ao mesmo tempo.

1. Leia a spec inteira.
2. Abra os arquivos que ela promete tocar. Anote `arquivo:linha` de tudo que confirma ou contradiz o que a spec assume.
3. Consulte o estado real do dado sempre que a spec depender dele: schema, trigger, policy, e **contagem**. Contagem muda prioridade. "Vamos suportar X" é outra conversa quando X tem zero usuário hoje.
4. Escreva o snapshot de evidência.

**O snapshot** é um arquivo com o que foi lido, os `arquivo:linha` das descobertas, as queries rodadas e o resultado cru delas. Guarde fora do repositório (scratchpad da sessão) a menos que o projeto tenha lugar próprio. Ele paga duas vezes: fecha as lacunas agora, e é o que se entrega ao revisor externo depois, se houver revisão.

**Sonda não é evidência; o resultado reproduzível é.** Script exploratório (uma consulta de uma
vez, um teste de hipótese, a versão 2 e 3 da mesma sonda) fica no scratchpad e não entra no
repositório. Entra como evidência só o que outra pessoa consegue refazer: a consulta ou a receita,
os parâmetros, o SHA e o resultado cru; ou o caso mínimo promovido a teste. O plano cita o
resultado, não o script. Medido: um ciclo arquivou dezenas de sondas descartáveis como "evidência",
e foi a maior parte dos 127 arquivos dele.

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
| "corte no `created_at` da tabela de auditoria" | é quando o turno **fechou**, ~13 s DEPOIS do inbound a recuperar. O corte cru excluiria exatamente a mensagem alvo | **o fix seria um no-op, e passaria verde** |
| "o registro auditado aparece na flag de teto impossível" | `max=20000` é plausível e não bate em nenhum dos 3 critérios congelados | um worker gastou um ciclo de dispatch para escalar |
| `node scripts/run-e2e.mjs` | o script mora noutro diretório, dentro da pasta de uma skill do projeto | comando quebrado no passo do coordenador |

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

**Fato que sustenta uma DECISÃO que você leva ao usuário não pode ser adiado para o primeiro
passo da tarefa: meça antes de perguntar.** O "PARE e escale" protege a implementação, não a
decisão. Se a premissa cai na execução, o usuário decidiu em cima de um fato falso, a tarefa trava
esperando uma decisão nova e a rodada de perguntas se repete. O sintoma: você escreve a
recomendação ao usuário e, no plano, a mesma premissa aparece como "primeiro passo: medir".
Medido em 26/09/2026: uma recomendação ("o estado pendente deriva de uma flag que o registro já
tem") foi aprovada com a premissa "o registro do caso real tem essa flag" deixada como primeiro
passo da tarefa. A revisão externa rodou a consulta por turno: a flag era falsa em todos os turnos
do caso real. A decisão caiu, o usuário decidiu de novo e a tarefa ficou bloqueada até lá.
Custo da medição que faltou: um `select`.

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

> **A linha só fecha com a CONTAGEM do falsificador, sobre o universo inteiro da afirmação.**
> Escreva a consulta ou o `grep` que conta o caso que derruba a afirmação, e o número que ela
> devolveu, mesmo que seja zero. Contagem que confirma a afirmação mede outra coisa e não fecha
> a linha. E amostra escolhida **porque mostrava o defeito** (os registros que a regra antiga
> gravou errado) não refuta um "nunca": o contraexemplo costuma estar nos casos da mesma forma
> em que a regra antiga acertou por outro caminho, e que por isso ficaram fora da amostra.
> Conte também nesse resto.

Medido em 2026-09-12: uma afirmação de carga dizia *"os vínculos persistidos cobrem a
duplicação entre dois provedores"*, o falsificador estava escrito na frase certa (*"vínculo
não existe"*), e a coluna de resultado trazia `[MEDIDO: 149 linhas vinculadas]`. A consulta
que contava o falsificador tinha a mesma forma, com um `not exists` a mais, e devolvia 32
pares sem vínculo em 90 dias. Ninguém a rodou porque a tabela aceitava qualquer `[MEDIDO:]`.
Quem a rodou foi a revisão externa, e virou bloqueador.

Medido em 2026-10-09: a afirmação *"essa forma de fala, sob aquela pergunta, nunca é
orçamento"* foi contada nos 24 registros em que o defeito tinha gravado um teto: zero
contraexemplos. A revisão externa procurou entre as respostas da mesma forma que **não**
gravaram teto e achou um; a regra que o usuário tinha aprovado erraria exatamente esse caso, e
ele teve de decidir de novo antes de qualquer código.

### As classes que morderam de verdade: confira estas por nome

Cada uma custou um ciclo, uma rodada de gate ou um run pago. O mecanismo e a medição de cada uma
estão em `references/classes-de-erro.md`: **leia a classe inteira quando ela se aplicar** ao plano.

1. **Semântica de coluna, flag ou campo:** nunca infira pelo nome; abra a linha real e compare com
   um caso conhecido.
2. **O fix é no-op?** Com o código de hoje, a mudança altera alguma coisa? No-op passa verde.
3. **O caso prometido dispara o critério novo?** Rode o critério contra o caso agora.
4. **Caminho, comando e nome existem?** Arquivo novo cita o irmão existente; `--help` inteiro,
   nunca recortado.
5. **Invariante que você promete preservar:** caminho de exceção procurado e testes existentes lidos.
6. **Emissores do comportamento que você REMOVE:** chamadores, literal no código e literal nos
   dados; gate novo sobre saída existente é remoção.
7. **Receita copiada de outro contexto:** a pré-condição dela vale aqui?
8. **Passo novo em pipeline existente:** leia do ponto de inserção até o fim do fluxo.
9. **Tarefa que adia, segura ou bloqueia uma ação:** o ponto único antes dos efeitos; ação com
   vários executores lê a mesma trava com a mesma entrada.
10. **Tarefa que substitui um módulo:** os gatilhos do módulo antigo entram na matriz.
11. **Peça nova dentro de um hospedeiro existente:** ela herda o estado (e os defeitos) dele.
12. **"Importar a mesma função" não é paridade** quando a entrada é preparada no chamador.
13. **Teste do consumidor com campo que o produtor real não emite:** a fixture vem do produtor.
    Vale também quando o produtor é a rodada anterior do próprio sistema: cenário de várias
    rodadas prova-se pela camada que grava e relê o estado entre elas.
14. **Remover evento ou linha de log:** procure leitores por tempo (`desc`, `limit 1`, `max`).
15. **Escritor único prometido:** inventário dos sites de escrita de hoje, incluindo gatilhos e jobs.
16. **Linha nova em template, seed ou catálogo global:** o provisionamento de tenant a copia;
    unicidade pode morar num índice.
17. **Detector de texto:** falso positivo medido em amostra real, falso negativo com as frases
    vizinhas, lista de variações no `Pronto quando`.

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

### Prova ponta a ponta: não executado é hipótese, e só conta com a causa inspecionada

Cenário escrito e não executado não é cobertura: roda antes do gate, ou entra `[SUPOSTO:]` com o
passo "rodar ANTES de considerar coberto". Vermelho e verde só contam com a causa inspecionada
(a asserção do defeito, não setup, fraseado ou reparo pelo modelo). Mecanismo e medições:
`references/classes-de-erro.md`, seções finais.

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

A única exceção existe entre ondas paralelas em worktrees separadas (Fase 2): ali o arquivo que as
duas tocam entra na tabela do que não roda junto, com o trecho de cada onda nomeado, e quem
concilia é a onda que integra depois. Dentro de uma onda, nenhuma exceção.

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

**O traçado é uma TABELA do plano, não um exercício de cabeça:** uma linha por requisito que
move dado ou comportamento, uma coluna por salto, `arquivo:linha` em cada célula (esqueleto, §3.1).
Conselho em prosa é aplicado quando o autor lembra; célula vazia fica visível para quem revisa, e
a matriz de ownership passa a ser derivada das células, não da memória. Medido em 25/09/2026:
3 dos 11 bloqueadores da revisão externa eram saltos sem dono (decisão no chamador errado,
comportamento sem ponto de emissão, dado que não chegava a um dos canais de saída), num plano cuja
skill já mandava traçar. A regra existia; a coluna, não.

**A última coluna também é salto, e é a que mais sai em prosa.** Quando o efeito observável de um
requisito é uma superfície (uma tela, um painel, um relatório, uma linha de log que alguém vai
ler), a célula leva o arquivo que a renderiza e o dono dele, não uma frase como "aparece para o
administrador". Frase na última coluna passa pela auto-revisão, porque a célula não está vazia, e
chega à execução sem dono: o coordenador descobre no meio da onda que ninguém desenha aquilo, e
fecha o buraco com contrato novo e responsabilidade dividida entre tarefas já despachadas.
Medido em 29/09/2026: um requisito cujo critério era "depois de N falhas, aparece como pendente
no painel do admin" tinha na última coluna só "pendência visível"; nenhuma tarefa possuía o
painel, e o contrato do dado, a visão e a tela foram repartidos entre três tarefas na segunda
onda.

**Teste existente que trava o comportamento antigo é arquivo da matriz.** Quando o plano muda ou
remove um comportamento, os testes que o afirmam hoje (unitários **e** cenários ponta a ponta)
entram na matriz com dono único e a decisão escrita: reescrever e renomear, nunca apagar. Procure
pelo literal do comportamento nos diretórios de teste, e não só pelo nome do arquivo que muda.
Sem isso, duas tarefas paralelas reescrevem o mesmo teste, ou o teste que exige o comportamento
removido aparece só na bateria antes do deploy. Medido em 25/09/2026: as duas coisas no mesmo
ciclo, uma achada pela revisão externa e a outra só na véspera da publicação.

**Linha NOVO cita o irmão.** Arquivo que ainda não existe entra na matriz com o irmão existente
do mesmo tipo e a configuração que o descobre, os dois com `[LIDO:]`. Sem isso o caminho é
`[SUPOSTO]`, e o `ls` da auto-revisão não tem o que conferir (classe 4, `references/classes-de-erro.md`).

**Depois de escrever a matriz, releia as descrições das tarefas e procure responsabilidade
repetida.** Duas tarefas podem não colidir em arquivo e ainda assim receberem a mesma frase
("resolve a config no bootstrap"). Colisão de responsabilidade é colisão, e aparece mais tarde
e mais cara que a de arquivo.

### Contratos congelados

Este é o item que faz o paralelismo existir. Workers não divergem na ordem das coisas, divergem no formato delas.

Congele, antes da primeira onda: tipos e interfaces compartilhadas, shape de request e response, nomes de chave de i18n, props na fronteira entre dois componentes, e a fixture de casos que serve de fonte da verdade de uma regra de negócio.

**Ordem de eventos também é contrato.** Quando duas tarefas dividem uma transição ou
operação assíncrona, congele estados, identidade da execução, quem inicia/confirma/cancela
e a condição que libera a próxima etapa. Inclua interrupção e retorno com estado vivo.
Flag alterada não prova efeito observado: indique qual confirmação a fronteira requer.
Para interface com referência aprovada, vincule esse contrato ao §8.3 da spec.

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

Medido em 2026-09-03: a spec tinha 13 FRs, cada um com cenário
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

**O `Pronto quando` diz também a CAMADA de prova, da mais barata para a mais cara.** Primeiro a
que exercita o consumidor real sem custo por execução: teste de unidade ou replay do fluxo sobre o
caso real, e comparação da decisão velha com a nova sobre o histórico persistido (mede o alcance:
quantos casos reais mudariam). Prova que chama modelo pago ou envia algo para fora só para o que as
baratas não alcançam: trajetória de vários passos, comportamento do modelo, envio, persistência. E
só o cenário afetado, não a bateria. Paridade de predicado não prova correção de contexto: a
comparação sobre o histórico mostra o alcance, e quem prova é o caso que passa pelo consumidor.
Medido: no mesmo projeto, testes ponta a ponta pagos foram de 29% a 43% dos tokens gastos com o modelo no fluxo principal
num mês.

**A camada precisa preservar o mecanismo sob risco.** Liste as peças reais e as simuladas;
simular a peça que causa o risco deixa aquele cenário pendente, mesmo com teste verde.
Se o risco depende de interação ou ordem de eventos, planeje uma primeira prova do percurso
crítico assim que suas dependências existirem, antes de ampliar variantes. Use a integração
real e separe os eventos como acontecem nela; registre candidato, resultado e limitações.
Esta é prova no aceite do coordenador, não outro gate adversarial, e respeita as autorizações
do projeto. Medido em 2026-10-09: testes com etapas agrupadas passaram com falhas de transição
e reabertura na aplicação real; a prova tardia exigiu novas rodadas de correção.

## Fase 2 — o grafo

**Ondas.** Uma onda termina exatamente onde o coordenador precisa agir. Descubra o que este projeto proíbe delegar (ver *Regras do projeto*, abaixo): tipicamente git, migration, deploy e publicação. Esses passos viram passos do coordenador, e são eles que definem onde a onda quebra. Não é escolha estética.

Escreva três coisas, sempre:

1. **O grafo**, em ASCII, com as dependências visíveis.
2. **O que roda junto**, por onda.
3. **O que NÃO roda junto, com a razão de cada par.** Sem a razão escrita, alguém vai "otimizar" isso depois e reintroduzir a colisão.

Marque o **caminho crítico**. É o que diz se vale acrescentar worker ou se você só vai acrescentar espera.

**Sem número fixo de workers.** Tarefas que tocam arquivos diferentes e não dependem uma da
outra rodam todas juntas na mesma onda; um teto como "3 por vez" só acrescenta espera. O único
freio legítimo é a cota do dia nos modelos, e aí distribua entre provedores e comece pelo caminho
crítico. Durante a onda, cada worker roda só os próprios testes; a suíte inteira roda no aceite.
Medido em 24/09/2026: o plano saiu com teto de 3 workers que ninguém pediu, e o usuário mandou tirar.

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

### Ondas paralelas em worktrees separadas: um coordenador por onda

Dentro de uma onda os workers dividem a árvore, e a ownership resolve. Duas ondas independentes na
mesma árvore, não: cada uma tem aceite, suíte e commit próprios, a suíte de uma roda com o código
pela metade da outra (a mesma classe de *Medir nas dependências do checkout compartilhado*, em
`orchestrating-execute`), e o commit de uma estagia trabalho da outra. Quando o grafo tem duas ou
mais ondas que não dependem uma da outra, cada onda paralela ganha worktree, branch e coordenador
próprios; o coordenador principal toca uma delas na árvore atual. Onda que depende de outra espera
a integração dela e não ganha worktree. Escala parcial não usa isto, e projeto que só aceita branch
ou worktree a pedido pergunta antes.

O plano escreve quatro coisas:

1. **A tabela de papéis.** Só o principal integra na branch principal, publica (homologação
   inclusive), roda teste ponta a ponta, aplica migração e escreve em dado: com dois coordenadores
   publicando no mesmo recurso único (um ambiente de homologação, um ambiente de teste por tipo), o
   teste de um roda com o código do outro. O coordenador de onda despacha e aceita os workers
   dela, roda a suíte, commita no próprio branch e resolve os conflitos com a branch principal.
2. **Os arquivos que duas ondas tocam**, com o trecho de cada uma. Mesmo trecho nas duas é colisão:
   junte, serialize ou parta, como dentro de uma onda.
3. **A ordem de integração**, que é também a ordem dos rebases.
4. **O que a worktree nova precisa**, no passo que a cria. Ela nasce sem o que o git ignora
   (arquivo de segredos, dependências instaladas), e ferramenta que reescreve a pasta de
   dependências pede instalação isolada por worktree.

A entrega da onda é o branch local, não um PR. Procedimento e porquê: `orchestrating-execute`,
*Ondas paralelas em worktrees*.

## Fase 3 — gates

Um gate não é uma revisão. Revisão acontece depois e informa; gate acontece antes e bloqueia.

**Um gate por plano**, sobre o candidato integrado, imediatamente **antes** do primeiro passo
irreversível: aplicar migration em produção, deployar, publicar. Migration aplicada não tem `git
revert`, e uma revisão que chega depois disso só documenta o estrago. Um segundo gate só quando há
um segundo passo irreversível com superfície própria (uma publicação de frontend separada do
deploy de backend), ou quando o plano decide ir à produção em etapas porque uma onda corrige algo
ao vivo e não pode esperar as outras: aí é um gate por produção, com a razão escrita. Nunca um
gate por onda: o que guarda a onda é o aceite do coordenador
(`orchestrating-execute`, seção *Dois mecanismos de qualidade*). Escala parcial ou mínima: sem
gate. Medido em 20 e 21/09/2026: quatro ondas com um gate por onda rodaram cinco gates e nove
tarefas de correção; seis tarefas com um gate rodaram um, corrigiram com teste e publicaram na
mesma noite.

Um gate é uma tarefa como as outras, com nível, dono e dependência. O passo do coordenador que
ele guarda só acontece depois de o gate ter rodado e de as correções aceitas passarem na suíte e
no E2E. **BLOQUEIA não pede segunda rodada; pede correção com teste**, e teste que reprova volta
para correção, nunca para o gate. Escreva isso no plano com essas
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
e a revisão externa achou sete**, cinco confirmados no código, um deles capaz de mandar dado a um
contato sem identidade nenhuma. Medido em 2026-09-12: quatro bloqueadores, três documentais e uma
decisão do usuário. Medido em 2026-09-21: oito bloqueadores, todos confirmados no código e no
banco antes de qualquer linha escrita. Não foi falta de rigor na forma; confirmação e verificação
parecem iguais por dentro.

Como oferecer, ao entregar o plano, em uma linha: *"Recomendo revisão externa porque <o que este
plano tem de caro: dado de produção, N tarefas em paralelo, invariante que ele promete preservar>.
Quer? Se sim, diga o modelo."* Se o usuário já nomeou o modelo no pedido, não pergunte de novo:
rode a revisão pelo procedimento de `references/external-review.md` e entregue o plano já
adjudicado. Se ele não pediu, registre "não solicitada" no §0.1 e pare. Feature pequena: diga que
não paga.

**O modelo nomeado decide o mecanismo, nunca o contrário.** Se o harness em que você roda
oferece esse modelo como subagente, despache a revisão como subagente, sem orquestrador. Se não
oferece (outro fornecedor, outro CLI, um agente do catálogo do orquestrador), a revisão sobe por
orquestração multi-agente: com Orca, a skill `orchestration` (terminal no CLI daquele agente,
task, dispatch, espera por `worker_done`), e confira no TUI que o modelo que subiu é o pedido,
como em `orchestrating-execute`. Sem mecanismo que alcance o modelo, diga isso ao usuário e
pergunte; nunca troque pelo modelo mais próximo que o harness tem. Troca silenciosa entrega
outra revisão com o nome da que ele pediu.

**Agente fora do harness sobe SEMPRE pela skill `orchestration`, nunca em modo headless.**
`codex exec` (ou outro CLI) rodando em segundo plano pelo shell alcança o modelo, mas o usuário não
vê o agente trabalhar nem pode intervir. Terminal visível no orquestrador é o mecanismo, não uma
opção.

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

### A revisão externa roda UMA vez. Nova rodada só com autorização explícita do usuário

**Regra dura:** a revisão adversarial de spec e plano roda **uma vez** por pedido do usuário.
Depois de incorporar os achados, você **para, relata o que mudou e pergunta** se ele quer outra
rodada. Nunca despache a rodada 2 por conta própria, nem que o veredito tenha sido BLOQUEADO,
nem que a mudança tenha sido grande, e nem que o próprio plano, escrito por você, diga "rodada 2
antes do C0". Isso inclui não escrever no plano um gate de revisão repetida que o usuário não
pediu. Um revisor bloqueando não autoriza nada; quem autoriza nova rodada é o usuário. Os gates
**de implementação** do plano (ex.: S1, antes de migração e deploy) são outra coisa: estão no
plano que o usuário aprovou e rodam uma vez cada, com a mesma regra para repetição.

Medido em 22/09/2026: o usuário pediu uma revisão
adversarial da spec e do plano. Ela veio BLOQUEADA com 4 achados reais, todos incorporados. Em
seguida o coordenador escreveu no plano "rodada 2 antes do C0" e despachou sozinho uma segunda
revisão no modelo mais caro. O usuário interrompeu: *"eu não pedi pra rodar outra revisão, não
era pra você ter rodado"*. O certo era parar depois da incorporação, com o relato *"os 4 achados
entraram assim; quer uma segunda rodada?"*.

## Fase 4 — fecho

Escreva os passos do coordenador entre as ondas e depois da última: o que ele aplica, verifica, commita e deploya, em ordem, com o comando.

Termine com os portões de entrega do projeto. Descubra quais são (ver abaixo) em vez de assumir: pode ser deploy, migration, bundle OTA, build nativo, publicação em loja. E inclua a documentação que este projeto exige atualizar no mesmo commit da mudança, se exigir.

## Auto-revisão antes de entregar

Duas listas, e a primeira é a que faltava. Estrutura impecável em cima de fato falso continua
sendo plano falso.

**Pergunta de julgamento aprova o próprio texto; coluna vazia não.** Medido em 25/09/2026: dos
11 bloqueadores que a revisão externa achou num plano, **6 já eram cobertos por regras desta
skill** que o autor não aplicou (traçado, no-op, contrato mais restrito que o requisito). Mais
regra em prosa não teria pegado nenhum. O que pegou foram as verificações mecânicas: o `grep` de
FR e a tabela de afirmações de carga. Por isso, antes das listas: o plano tem as tabelas
obrigatórias preenchidas, sem célula vazia (afirmações de carga §0.1, ownership §3, traçado §3.1,
rastreabilidade §5.1)? Célula vazia é item aberto, não detalhe.

**Tamanho — o primeiro item, e é mecânico:** o plano mais a evidência que ele arquiva já passou do
tamanho do diff que ele planeja? Então ele está planejando mais de uma família, ou arquivando
sonda. Recorte antes de entregar (ver *Um pedido, uma família* e *Sonda não é evidência*).

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
- Para cada comportamento que o plano REMOVE: os emissores foram contados pelos três lados,
  chamadores da função, literal do texto **e** literal nos dados (template, configuração, seed)?
  Validação ou gate novo sobre saída existente contou como remoção, com a medição no histórico
  persistido? Os testes que hoje afirmam o comportamento têm dono e decisão na matriz?
- Toda tarefa que mexe em detector de texto tem a amostra de falso positivo medida e a lista de
  variações escrita no `Pronto quando`?
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
- Todo arquivo tocado aparece na matriz de ownership, com um dono só, e todo arquivo das
  células do traçado (§3.1) está na matriz?
- Toda célula da última coluna do traçado que descreve algo que uma pessoa vê (tela, painel,
  relatório) tem um arquivo e um dono, e não só uma frase?
- Nenhuma responsabilidade aparece em duas tarefas, mesmo sem colisão de arquivo?
- A ordem das ondas segue dependência de **comportamento**, com o que LIGA a mudança por
  último e reversível?
- Nenhum passo de validação tem item que você já sabe que vai falhar por causa de tarefa
  posterior?
- Todo contrato de que dois ou mais workers dependem está escrito literal e datado de antes da onda 1?
- Quando há coordenação assíncrona, o contrato inclui estados, identidade e confirmação
  entre donos? A tarefa indica peças reais/simuladas e quem executa a primeira prova integrada?
- Nenhum contrato é mais restrito que o FR que implementa? Se é, a decisão está na spec, com autoria?
- O gate é um por plano (ou um por produção, se o plano vai em etapas e diz por quê), antes do
  passo irreversível, sobre o candidato integrado, e nenhuma onda tem gate próprio?
- Todo par "não pode junto" tem a razão escrita?
- Com onda em worktree própria: há tabela de papéis, todo arquivo tocado por duas ondas está no
  "não pode junto" com o trecho de cada uma, e a ordem de integração está nos passos do
  coordenador?
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
- se branch e worktree só entram a pedido;
- como mudança de schema é aplicada, e o que a torna irreversível;
- quais são os portões de entrega;
- que documentação precisa acompanhar a mudança no mesmo commit;
- convenções de idioma, de commit e de nomeação.

Se o projeto não tiver esses arquivos, pergunte ao usuário estas coisas antes de escrever o plano. Elas mudam o grafo, não são detalhe.

## Onde salvar

Siga a convenção do projeto. Procure planos anteriores (`docs/plans/`, `docs/**/plans/`, `plans/`) e imite o caminho e o formato de nome que já existem. Se não houver nenhum, use `docs/plans/AAAA-MM-DD-<topico>.md` e diga ao usuário que você criou a convenção.

Se o projeto guarda planos em pastas por estado (a fazer / em validação / feito), o plano novo nasce em "a fazer", ao lado da spec. Quem o move para "em validação" é o fecho de `orchestrating-execute`; para "feito", quem obtém a prova que o plano promete. Plano que ainda não rodou fora de "a fazer" some da lista de trabalho.

Esqueleto pronto para copiar: `references/plan-template.md`.

Depois de escrever, commite o plano, ofereça a revisão externa em uma linha (Fase 3) e **pare**. Não suba worker. Se o usuário quiser executar, a skill é `orchestrating-execute`.

## Documentação viva

Esta skill melhora com o uso, e melhorá-la faz parte da implementação quando o ciclo mostrou um
furo **dela**: o achado da revisão adversarial que o plano deveria ter pegado, o desvio que a
execução pagou. É opcional, e só vale quando o furo custou e vai custar de novo.

- **Melhore antes de acrescentar.** Procure a seção que já cobre o assunto e aperte-a; linha nova
  só se nada cobre. Esta skill não cresce indefinidamente.
- **A regra fica aqui; o caso vai para `references/`.** Este arquivo é carregado inteiro em todo
  plano, inclusive no mínimo. Aqui entra a regra com uma linha de lastro (data e número); a
  narrativa do caso, quando precisa ser longa, vai para `references/classes-de-erro.md` ou para
  uma referência nova, com um ponteiro de uma linha.
- **Conceito, não caso.** Antes de escrever, leia o `AGENTS.md` da raiz do plugin: nada de nome de
  tabela, cliente, ciclo ou caminho do projeto onde a lição foi paga.
- **Escreva no clone git de onde a skill foi carregada** (a pasta deste arquivo). Se ela não é
  repositório git (cópia de cache de instalação), não edite: deixe o texto proposto no relatório.
- **Não commite nem dê push.** Avise o usuário no relatório final, como follow-up: arquivo, seção
  e uma linha do porquê. Quem confere e commita é ele.
