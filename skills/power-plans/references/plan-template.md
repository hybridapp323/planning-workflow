# Esqueleto do plano

Copie a estrutura, não o conteúdo. Corte seções que a feature não usa, e diga que cortou.

---

```markdown
# <Feature> — plano de implementação (multi-agente)

**Spec:** `<caminho da spec>`
**Evidência:** `<caminho do snapshot da fase 0>` (diagnóstico) + `<fase 0.5>` (prescrição)
**Escala escolhida:** completa | parcial | mínima — <por quê>
**Estado:** a fazer | em validação desde AAAA-MM-DD (falta: <prova>) | feito em AAAA-MM-DD (<prova obtida>)

## 0. Como ler este plano

Cada tarefa é autocontida: dá para executá-la lendo a spec, esta seção e a tarefa.
Nenhuma tarefa toca arquivo de outra (§3). Nenhuma tarefa inventa formato que
já esteja congelado (§4).

Um worker que precisar sair do seu escopo escala, não improvisa.

## 0.1 Afirmações de carga (o que derruba este plano se for falso)

Cada linha é uma afirmação que sustenta uma decisão ESTRUTURAL, com a refutação que foi
tentada e o resultado. Quem executar e descobrir que uma delas é falsa **para e escala**: não
é ajuste de tarefa, é redesenho.

| # | Afirmação | Falsificador, em uma frase | Consulta ou grep que CONTA o falsificador | Contagem | Consequência |
|---|---|---|---|---|---|
| A1 | <ex.: "desativar Z é seguro porque Z é a única porta"> | <ex.: "existe outra porta"> | <a query ou o `grep`, literal> | <número, mesmo que 0> | <o que muda se não for 0> |

A linha só fecha com a contagem do falsificador. Contagem que confirma a afirmação mede outra
coisa e não fecha a linha.

**Revisão externa:** <quem revisou, quando, caminho do relatório> · <N bloqueadores: n documentais, n decisão do usuário, n redesenho; N aceitos>
· <o que foi recusado e por quê>. Se o usuário não pediu revisão, escreva "não solicitada". O
campo é registro, não pendência: revisão da spec ou do plano não é tarefa do grafo (§2).

## 1. Níveis de complexidade

| Nível    | Modelo            | Critério |
| -------- | ----------------- | -------- |
| Complexa | <MODELO_COMPLEXA> | erro caro ou difícil de detectar; precedência, invariante, concorrência, segurança, dado de produção |
| Média    | <MODELO_MEDIA>    | solução conhecida, escopo claro, erro aparece em teste ou na tela |
| Baixa    | <MODELO_BAIXA>    | mecânica, verificável por inspeção, sem decisão de design |
| Gate / Advisor | <MODELO_GATE> | revisão read-only adversarial (S<n>) e consulta de rumo (`ADV-n`, no máximo uma por veredito de gate); um modelo só para os dois papéis |

O usuário preenche a coluna Modelo na hora de executar.

## 2. Grafo de execução

    C0 (coordenador: congela contratos)
     |
     +-- T1 [Média]     ----+
     +-- T2 [Complexa]  ----+--> C1 (coordenador: integra e aceita) --+
     +-- T3 [Média]     ----+                                         |
                                                                      v
                                                  T5 [Complexa] --+
                                                  T6 [Média]  ----+--> S1 [gate] --> C2 (migration, deploy)

**Caminho crítico:** C0 → T2 → C1 → T5 → S1 → C2

O gate é um só, antes do primeiro passo irreversível, sobre tudo que foi integrado até ali. A
onda 1 não tem gate: quem a guarda é o aceite do coordenador em C1.

### 2.1 O que roda junto

| Onda | Tarefas | Por quê é seguro |
| ---- | ------- | ---------------- |
| 1    | T1, T2, T3 | arquivos disjuntos (§3), contratos já congelados em C0 |

### 2.2 O que NÃO roda junto

| Par | Razão |
| --- | ----- |
| T5 antes de C1 | T5 consome o contrato que a onda 1 entrega e C1 aceita |
| T2 antes de C0 | a fixture é a fonte da verdade da regra; sem ela T2 e T3 inventam regras diferentes |

## 3. Ownership de arquivo (normativo)

Um arquivo, um dono. Ninguém edita arquivo de outro.

| Arquivo | Dono |
| ------- | ---- |
| `caminho/a.ts` | T2 |
| `caminho/b.tsx` | T9 |
| NOVO `caminho/c.test.ts` (irmão: `caminho/d.test.ts`; descoberto por `config:linha`) | T4 |

**Somente leitura para todos:** `caminho/c.ts`, `caminho/d.ts`.

| `testes/x.test.ts` (afirma o comportamento que FR-4 remove: **reescrever e renomear**) | T3 |

Linha NOVO cita o irmão existente do mesmo tipo e a configuração que o descobre, os dois com
`[LIDO:]`. Caminho novo deduzido de norma escrita é `[SUPOSTO]`. Teste existente que afirma
comportamento que o plano muda ou remove (unitário ou ponta a ponta) é linha desta tabela, com a
decisão escrita.

### 3.1 Traçado por requisito

Uma linha por FR que move dado ou comportamento. Cada célula é `arquivo:linha` com `[LIDO:]`; os
arquivos das células alimentam a matriz acima. Célula vazia é salto sem dono.

| FR | Onde nasce | Quem transporta | Quem decide | Quem emite (código **e** dados) | Efeito observável |
| --- | --- | --- | --- | --- | --- |
| FR-1 | `a.ts:40` | `contexto.ts:210` | `b.ts:88` | `c.ts:15`; template `<tabela>.<chave>` | <o que o usuário ou o teste vê> |

## 4. Contratos congelados

Escritos em C0, antes da onda 1. Ninguém altera sem passar pelo coordenador.

### 4.1 <Tipos / interfaces>

    <bloco de código literal e completo>

### 4.2 <Shape de request e response>

    <bloco de código literal e completo>

### 4.3 <Chaves de i18n / props de fronteira / fixture>

    <bloco de código literal e completo>

### 4.4 <Campo derivado: regra por origem>

    | Origem | Sinal na linha real | Valor do campo |
    | --- | --- | --- |

Todo campo que não é cópia 1:1 de uma coluna tem esta tabela, e cada origem uma medição própria.

## 5. Tarefas

### T<n> — <título> · **<Nível>** · <dependências ou "sem dependência">

**Arquivos:** `<caminhos que esta tarefa possui>`

**O que fazer:** <objetivo, em uma ou duas frases>

**Cobre:** FR-<n>, FR-<m> — ou *"infra, sem FR"* dito com essas palavras

**Contratos que ela consome:** §4.1, §4.2

**Assume que:** <um fato por linha, cada um com `[MEDIDO: cmd -> resultado]`, `[LIDO:
arquivo:linha]` ou `[SUPOSTO: o que o falsifica]`. Nenhum `[SUPOSTO:]` pode sustentar a
implementação: se sustentar, o primeiro passo desta tarefa e medi-lo, e "se der diferente,
PARE e escale">

**Pronto quando:** <o cenário de aceitação do FR, COPIADO da spec: dado / quando / então. Não
parafraseie — o worker recebe esta frase literal no briefing. Se não existe cenário para copiar,
o buraco é na spec, e é lá que se conserta. Tarefa que mexe em detector de texto acrescenta aqui
a lista de variações e a amostra real de falso positivo (`SKILL.md`, classe 17)>

**Não faça:** <o que pertence a outra tarefa e vai dar vontade de fazer aqui>

### S<n> — Gate de <o quê> · **Gate / Advisor** (`<MODELO_GATE>`) · depende de T<x>, T<y> · **bloqueia C<z>**

**Mandato:** revisar, não corrigir. Uma rodada. Devolve PASSA ou BLOQUEIA com a lista de achados
provados.

**Cobre:** <o candidato integrado até aqui: tudo que C<z> vai tornar irreversível>

**C<z> só depois de este gate ter rodado e das correções aceitas passarem na suíte. BLOQUEIA não
repete o gate; superfície nova depois do veredito, sim, só sobre o delta.**

## 5.1 Rastreabilidade (mecânica, não decorativa)

Preencha **depois** de escrever as tarefas, e **rode o grep** — não confie na leitura, que é
justamente o que aprova o próprio texto.

| FR | Cenário que vira o "Pronto quando" | Tarefa |
| --- | --- | --- |
| FR-1 | <dado / quando / então, resumido> | T2 |
| FR-2 | <...> | T5 |

```bash
for n in $(grep -o 'FR-[0-9]\+' <spec> | sort -u -V); do
  printf '%-6s plano=%s\n' "$n" "$(grep -cw "$n" <plano>)"
done
```

Qualquer `plano=0` é um requisito que nenhum worker vai ver. **`-w` não é enfeite:** sem ele `FR-1` casa dentro de `FR-10`, e o requisito que ninguém
citou aparece como coberto. Medido no próprio ciclo que originou este item.

E os **casos de borda da spec (§5 de lá) são itens de trabalho, não documentação**: cada linha
recebe uma tarefa dona, ou a marca *"sem código, já coberto por FR-n"*. Linha de borda sem dono é
comportamento que a spec descreveu certo e ninguém implementou.

## 6. Passos exclusivos do coordenador

Só o coordenador roda estes. Nenhum worker.

### C0 — antes da onda 1
1. <verificar árvore limpa>
2. <escrever os contratos congelados de §4>
3. <commitar spec, plano e contratos, com caminhos explícitos>

### C1 — entre as ondas
1. <integrar as entregas da onda 1 e aceitar cada uma com casos seus>
2. <conferir que os contratos de §4 não mudaram>

### C2 — depois de S1 (nunca antes)
1. <aplicar migration>
2. <regenerar tipos>
3. <verificar>

### C<n> — fecho
1. <lint, testes>
2. <commit>
3. Portões de entrega deste projeto: <deploy? bundle? build nativo? publicação?>
4. Documentação viva que precisa acompanhar: <quais arquivos>
5. Mover plano e spec para <em validação> (pastas de estado do projeto, se houver) e reescrever as referências ao caminho antigo
6. Prova que leva a <feito>, e quando ela cabe: <medição / E2E / aceite do usuário, com data>

## 7. Riscos de orquestração

| Risco | Mitigação |
| ----- | --------- |
| <worker sai do escopo> | ownership normativo em §3 e "não faça" em cada tarefa |
| <contrato divergente> | §4 congelado antes da onda 1 |
| <correção pós-gate vai para o call site quando o defeito é de mecanismo> | advisor `ADV-n` (modelo `<MODELO_GATE>`) antes de despachar a onda de correção; no máximo uma consulta por veredito de gate; registro recomendou / decidi / divergência aqui neste §7 |
```

---

## Notas sobre o esqueleto

**"Pronto quando" é cópia, não paráfrase.** Verificável não basta: *"quando `bunx vitest run
caminho/x.test.ts` passar"* é verificável e ainda assim não diz **o que** o teste tem de afirmar —
quem escreve o teste decide isso, pelo que entendeu. Cole o cenário da spec dentro do critério e as
duas coisas viram a mesma. E se você compactar as tarefas numa tabela em vez de um bloco por
tarefa, a tabela precisa carregar as colunas `FR` e `Pronto quando`: **coluna que não existe não é
preenchida**, e foi assim que um plano inteiro saiu com zero critérios de pronto.

**"Não faça" evita mais colisão que qualquer tabela.** O worker que termina cedo procura o que fazer a seguir. Diga a ele o que é dos outros.

**Gate é tarefa e bloqueio ao mesmo tempo.** Escreva o "bloqueia C<z>" no título, não só no corpo, senão ele vira revisão pós-fato. E é um por plano, antes do primeiro passo irreversível: a onda é guardada pelo aceite do coordenador, não por gate.

**Revisão da spec e do plano não é tarefa do grafo.** Ela é opcional, quem decide é o usuário, e
acontece antes de o plano ser entregue (`SKILL.md`, Fase 3). Não existe `S0` que bloqueia a onda 1:
o executor despacha o que está no grafo, e despacharia o revisor sem ninguém ter pedido. `S<n>` é
gate: revisa código escrito, antes de um passo irreversível.

**A seção 7 é onde vai o aprendizado operacional da execução anterior.** Se algo custou caro na última vez, ele mora aqui, com a mitigação junto.
