# O advisor: quando chamar, orçamento e registro

Referência da skill `orchestrating-execute`. Leia antes de qualquer consulta de rumo. O brief e o mandato estão em `advisor.md`.

## O advisor: segunda opinião de RUMO, com orçamento e rastro

Medido em dois ciclos seguidos. Num ciclo de cobrança (12-13/09/2026) o advisor apontou uma falha
de idempotência **na rodada 1**; o coordenador descartou o aviso, e o gate redescobriu o mesmo
defeito duas rodadas depois. Num ciclo de auditoria (14/09) o coordenador decidiu sozinho, a
cada uma das sete rodadas, se a correção ia para o call site ou para o mecanismo, e o mesmo
arquivo voltou nas sete (`references/correcao-pos-gate.md`, *O brief que lista contraexemplos*). Os dois têm o mesmo
formato: **a decisão de rumo depois de uma reprovação é a mais
cara do ciclo, e é tomada pelo agente com menos distância dela.** No primeiro caso não faltou
segunda opinião; faltou rastro. Por isso a regra de carga desta seção é o registro, não o teto.

**O que o advisor é.** Um agente read-only, no modelo da linha `Gate / Advisor` do portão, que
recebe a reprovação (ou a escalação), **a direção que você pretende tomar** e as alternativas que
você descartou, e devolve o critério que discrimina entre elas. Ele não revisa código: isso é o
gate. Não escreve brief, não corrige, não decide.

> **Gate diz o que está errado. Advisor diz por onde consertar. O coordenador decide.**

Sem a direção pretendida no brief, o advisor refaz o gate, e você paga duas revisões pelo preço
de nenhuma decisão.

### Quando chamar: lista fechada

Só nestes três pontos, e em nenhum outro:

1. **A lista do gate chegou e a correção que você pretende muda o MECANISMO**, não remenda os
   call sites citados: a lista traz a mesma família em arquivos diferentes e você precisa
   escolher entre dois pontos de estrangulamento, ou entre estrangular e enumerar; ou o gate
   acusou o instrumento do teste e você vai desenhar o arreio.
2. **Um achado ou uma escalação contradiz um contrato congelado ou uma afirmação de carga do
   plano.** Isso é redesenho, e redesenho no meio da execução é onde a pressa erra. Chame antes
   de reescrever o contrato.
3. **Um freio técnico disparou:** segunda reprovação da mesma família ou limite de candidatas,
   tentativas ou esforço do plano/runner. Suspenda novos candidatos e gastos do lote; consulte
   automaticamente o advisor do gate sobre causa, mecanismo e instrumento. O coordenador
   retoma dentro da spec/autorização depois de contraprova offline, sem perguntar ao usuário
   só pela contagem. Se a saída exigir requisito novo, aceite de residual, ação não autorizada
   ou saldo pago adicional, essa decisão continua com o usuário.

O que NÃO é advisor, mesmo quando parece decisão importante:

- redigir brief, escolher worker, responder `question` de worker;
- o que uma regra desta skill já decide (ownership, gate antes do irreversível, modelo por nível);
- decisão de negócio: vai ao usuário, com resumo e recomendação, sem passar pelo advisor;
- **confirmar o que você já decidiu.** Consulta cuja resposta você já sabe qual quer é
  deferência ao contrário, e gasta o orçamento de quem precisaria dele.

### Orçamento: uma consulta por veredito ou episódio de freio

- **Uma consulta por veredito de gate**, no máximo: a que decide por onde vai a correção. Com um
  gate por plano (seção *Dois mecanismos de qualidade*), isso costuma ser uma consulta no ciclo
  inteiro.
- **Uma por escalação que contradiz contrato** e uma por episódio de freio técnico. Consuma
  o parecer existente antes de abrir consulta idêntica; outra exige evidência ou decisão nova.
- Retomar exige causa confirmada, decisão de mecanismo, caso vermelho antes/verde depois,
  controles preservados e próximo lote delimitado. Mais uma frase reconhecida ou justificativa
  em prosa não satisfaz isso. O advisor não zera contadores, não concede quota nem substitui o gate.
- **Cada consulta é uma task do Orca chamada `ADV-1`, `ADV-2`, …**, read-only, no run do ciclo. O
  `task-list` é o contador; ninguém conta de cabeça. Gate posterior do plano, se houver, recebe
  os blocos `ADV-n` no brief.
- Orçamento não é meta. Ciclo que fecha com zero consulta não fez nada errado.

Teto em prosa já falhou nesta skill mais de uma vez; o `task-list` é o que torna este auditável
sem depender de memória. **Sem Orca**, o contador são os blocos `ADV-n` do documento do ciclo
(seção seguinte): a consulta só existe depois de o bloco existir, numerado.

### O registro é a regra de carga

Toda consulta produz, no documento do ciclo (o congelamento, ou o §7 do plano), este bloco, no
mesmo turno em que a resposta chega:

```
ADV-n · onda <k> · gatilho <1|2|3>
Recomendou: <a direção e o critério, em duas linhas>
Decidi: <a direção tomada>
Divergência: <por que diferem> | seguiu a recomendação
```

E o descarte tem de ser **visível para o usuário**: toda divergência entra no relatório da onda
com estas palavras ("divergi do advisor em X porque Y"), não em nota de rodapé. Se o plano tem um
gate posterior (um gate de deploy depois do gate de contratos, por exemplo), o brief dele recebe
os blocos `ADV-n` e o pedido de julgar a divergência: se a evidência confirmar o advisor, é
bloqueante.

A palavra final é do coordenador, e é dele porque ele tem o contexto inteiro. Palavra final sem
rastro é a falha de idempotência que o gate teve de achar de novo.

### Modelo e forma

- O advisor roda **no modelo da linha `Gate / Advisor`**, o mesmo do gate, escolhido pelo usuário
  no portão. Linha vazia: pergunte antes da primeira consulta; nunca herde o de Complexa nem
  introduza modelo não listado.
- Brief, mandato read-only, formato da resposta, mecânica da task e o registro:
  `references/advisor.md`.
- Advisor interno do harness só serve a esse papel com identidade de modelo e esforço
  comprovadamente igual à linha `Gate / Advisor`. Não suponha identidade ou gratuidade e não
  substitua a task `ADV-n` por consulta opaca. Reutilize atribuição conhecida sem nova pergunta.
