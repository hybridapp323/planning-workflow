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

### Validar a spec, e consertá-la se precisar

A spec passou pela aprovação do usuário, mas quem a escreveu não estava tentando paralelizar. Três lacunas só aparecem agora, e as três quebram execução paralela:

- **Contratos ausentes.** A spec descreve comportamento mas não fixa formato. Dois workers vão inventar dois formatos.
- **Matriz de consumidores ausente.** Quem mais lê o dado, o campo ou o arquivo que essa feature muda? Um resolver, um job agendado, uma exportação, uma tela secundária. Feature nova quase sempre morre num consumidor esquecido, não na feature.
- **Decisões sem o que foi descartado.** Sem isso, o primeiro worker que achar a alternativa "melhor" vai implementá-la.

Se faltar, conserte a spec, e diga ao usuário exatamente o que você mudou nela. Planejar em cima de spec furada só adia o furo.

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

## Fase 3 — gates

Um gate não é uma revisão. Revisão acontece depois e informa; gate acontece antes e bloqueia.

Posicione gate imediatamente **antes** de cada passo irreversível: aplicar migration em produção, deployar, publicar. Migration aplicada não tem `git revert`, e uma revisão que chega depois disso só documenta o estrago.

Um gate é uma tarefa como as outras, com nível, dono e dependência. O que o distingue é que o passo do coordenador que ele guarda não pode acontecer sem o resultado dele. Escreva isso no plano com essas palavras.

### Revisão externa, opcional

Quando o usuário pedir, ou quando a feature for grande o bastante para valer, ofereça uma revisão externa read-only antes de executar. Ofereça; não imponha, e não fixe qual agente ou modelo faz.

Procedimento, mandato read-only, e como verificar depois que o revisor realmente não escreveu: `references/external-review.md`.

**Ao receber o relatório, não valide os bloqueadores por deferência.** Verifique cada um você mesmo, separe o que é buraco real do que é decisão de negócio, e leve as decisões de negócio ao usuário com resumo e recomendação. Um revisor competente ainda erra de tamanho: superdimensiona o que não tem usuário e subdimensiona o que já está quebrado.

## Fase 4 — fecho

Escreva os passos do coordenador entre as ondas e depois da última: o que ele aplica, verifica, commita e deploya, em ordem, com o comando.

Termine com os portões de entrega do projeto. Descubra quais são (ver abaixo) em vez de assumir: pode ser deploy, migration, bundle OTA, build nativo, publicação em loja. E inclua a documentação que este projeto exige atualizar no mesmo commit da mudança, se exigir.

## Auto-revisão antes de entregar

- Toda tarefa tem nível, dono e dependências explícitas?
- Todo arquivo tocado aparece na matriz de ownership, com um dono só?
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
