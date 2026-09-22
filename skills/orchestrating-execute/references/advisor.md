# Advisor: brief, mandato, task e registro

Complemento da seção *O advisor* do `SKILL.md`. Aqui fica o que se entrega, o que se pede, como a
consulta vira task do Orca e como ela deixa rastro. A regra (quando chamar, orçamento, palavra
final) está no `SKILL.md`; este arquivo é a mecânica.

## Antes de despachar: três testes

1. **O gatilho é um dos três da lista fechada?** Escreva qual, no título da task. Se não cabe em
   nenhum, não é advisor: é brief, é `question`, é regra da skill, ou é decisão do usuário.
2. **Você já escreveu a direção que pretende tomar, com o motivo?** Sem isso não há o que
   discriminar, e o advisor refaz o gate.
3. **O orçamento permite?** `orca orchestration task-list --json` e conte os títulos `ADV-`.
   Uma por veredito de gate, uma por escalação que contradiz contrato, uma para montar opções ao
   usuário. Já existe `ADV-` para este veredito ou esta escalação: não há segunda.

## Mecânica

```bash
orca orchestration task-create --task-title "ADV-1: gatilho <1|2|3> — <a decisão em cinco palavras>" \
  --display-name "ADV-1" --json
# terminal no modelo da linha Gate / Advisor do portão; confira o rodapé antes de despachar
orca orchestration dispatch --task <id> --to terminal:<handle> --return-preamble --json
```

A task não tem `--deps` de código: ela nasce da reprovação ou da escalação que a motivou, e você a
fecha com o resultado real (recomendação recebida, decisão tomada, registro escrito). O terminal
fecha no `worker_done`, como o de qualquer worker.

**Tempo:** uma consulta é leitura dirigida de 10 a 20 minutos, não uma revisão. Se o advisor
começa a varrer o repositório inteiro, ele está fazendo o trabalho do gate, e o sinal é que o
brief não trouxe a direção pretendida.

## O que entregar

Caminhos absolutos, sem colar valor de credencial:

1. A spec e o plano.
2. **O relatório do gate**, ou a `escalation`/`question` do worker copiada literal, e **quais
   achados** motivam a consulta. Não a lista inteira: os que decidem rumo.
3. **A direção que você pretende tomar**, em até dez linhas, com o motivo e com o que ela custa.
4. **As alternativas que você considerou e descartou**, uma linha cada, com o motivo do descarte.
   Alternativa que você não escreveu o advisor não tem como reabilitar.
5. Os contratos congelados que a decisão toca, colados literal.
6. O que você não conseguiu verificar, e por quê, e quais caminhos de leitura ele tem (MCP, CLI,
   banco só leitura).
7. O bloco de registro (abaixo), com o pedido de preencher a linha `Recomendou`.

## As perguntas, nesta ordem

1. Entre a direção pretendida e as alternativas, **qual restrição discrimina?** Não "qual é
   melhor": qual fato, se verdadeiro, decide.
2. **O que tornaria a minha direção errada**, e como eu veria isso antes de despachar?
3. Isto é decisão de rumo (do coordenador) ou decisão de negócio (do usuário)? Se de negócio,
   diga e pare.
4. **O que está faltando aqui que eu não teria como notar, porque fui eu que escrevi?**

Escreva a pergunta com o critério dentro. Num ciclo de cobrança a pergunta feita foi "isso
é seguro?" quando a decisão era "isso é idempotente por estado observado?": pergunta larga recebe
resposta larga, e resposta larga é a que se descarta sem perceber.

## Mandato read-only

O mesmo de `power-plans/references/external-review.md` § *O mandato read-only*, copiado literal no
brief: nenhum arquivo do repositório, nenhum comando de git, nenhuma escrita em banco, nenhum
deploy; exatamente um arquivo, o relatório, fora do repositório. Guarde o pré-estado da árvore e
confira o pós-estado como aquele documento manda. Enquanto o advisor lê, a árvore é dele, como
com qualquer gate.

## Formato da resposta

Peça exatamente isto:

```
Recomendação: <direção pretendida | alternativa N | outra, nomeada>
Critério que discrimina: <o fato ou restrição, com arquivo:linha ou query quando houver>
O que derrubaria a recomendação: <uma frase>
Risco que o coordenador não viu: <ou "nenhum além dos listados">
Fora do meu alcance: <o que não conseguiu verificar>
```

Recomendação sem critério é palpite, e você já tem o seu.

## O registro

No documento do ciclo (o congelamento, ou o §7 do plano), **no mesmo turno em que a resposta
chegar**:

```
ADV-n · onda <k> · gatilho <1|2|3>
Recomendou: <a direção e o critério, em duas linhas>
Decidi: <a direção tomada>
Divergência: <por que diferem> | seguiu a recomendação
```

E no relatório da onda ao usuário, quando divergir, com estas palavras: *"divergi do advisor em X
porque Y"*. Não em nota de rodapé. Se o plano tem gate posterior, o brief dele recebe os blocos
`ADV-n` e o pedido de julgar a divergência: evidência que confirma o advisor é bloqueante.

## Armadilhas já pagas

- **Descartar em silêncio.** 12/09/2026, num ciclo de cobrança: o advisor apontou uma falha de
  idempotência na rodada 1; o coordenador descartou; o gate redescobriu duas rodadas
  depois. O registro com divergência visível existe por causa disto.
- **Chamar para confirmar.** Se você já sabe a resposta que quer, a consulta é deferência ao
  contrário e gasta o orçamento de quem precisaria dele.
- **Trocar o modelo "porque estava à mão".** O advisor roda na linha `Gate / Advisor`; no de
  Complexa ele viola a atribuição do portão, e o usuário descobre pela fatura.
- **Deixar o advisor revisar.** Brief sem direção pretendida vira segundo gate, custa o mesmo
  que o primeiro e não decide nada.
