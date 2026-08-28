# Esqueleto do plano

Copie a estrutura, não o conteúdo. Corte seções que a feature não usa, e diga que cortou.

---

```markdown
# <Feature> — plano de implementação (multi-agente)

**Spec:** `<caminho da spec>`
**Evidência:** `<caminho do snapshot da fase 0>` (diagnóstico) + `<fase 0.5>` (prescrição)
**Escala escolhida:** completa | parcial | mínima — <por quê>

## 0. Como ler este plano

Cada tarefa é autocontida: dá para executá-la lendo a spec, esta seção e a tarefa.
Nenhuma tarefa toca arquivo de outra (§3). Nenhuma tarefa inventa formato que
já esteja congelado (§4).

Um worker que precisar sair do seu escopo escala, não improvisa.

## 0.1 Afirmações de carga (o que derruba este plano se for falso)

Cada linha é uma afirmação que sustenta uma decisão ESTRUTURAL, com a refutação que foi
tentada e o resultado. Quem executar e descobrir que uma delas é falsa **para e escala**: não
é ajuste de tarefa, é redesenho.

| # | Afirmação | Como tentei derrubar | Resultado |
|---|---|---|---|
| A1 | <ex.: "desativar Z é seguro porque Z é a única porta"> | <o falsificador que busquei, com `arquivo:linha`> | `[LIDO:]` / `[MEDIDO:]` |

**Revisão externa:** <quem revisou, quando, caminho do relatório> · <N bloqueadores, N aceitos>
· <o que foi recusado e por quê>. Se ainda não houve revisão, escreva "não revisado" em vez de
deixar o campo em branco.

## 1. Níveis de complexidade

| Nível    | Modelo            | Critério |
| -------- | ----------------- | -------- |
| Complexa | <MODELO_COMPLEXA> | erro caro ou difícil de detectar; precedência, invariante, concorrência, segurança, dado de produção |
| Média    | <MODELO_MEDIA>    | solução conhecida, escopo claro, erro aparece em teste ou na tela |
| Baixa    | <MODELO_BAIXA>    | mecânica, verificável por inspeção, sem decisão de design |

O usuário preenche a coluna Modelo na hora de executar.

## 2. Grafo de execução

    C0 (coordenador: congela contratos)
     |
     +-- T1 [Média]     ----+
     +-- T2 [Complexa]  ----+--> S1 [gate] --> C1 (coordenador) --+
     +-- T3 [Média]     ----+                                     |
                                                                  v
                                              T5 [Complexa] --+
                                              T6 [Média]  ----+--> C2 ...

**Caminho crítico:** C0 → T2 → S1 → C1 → T5 → C2

### 2.1 O que roda junto

| Onda | Tarefas | Por quê é seguro |
| ---- | ------- | ---------------- |
| 1    | T1, T2, T3 | arquivos disjuntos (§3), contratos já congelados em C0 |

### 2.2 O que NÃO roda junto

| Par | Razão |
| --- | ----- |
| T5 antes de C1 | T5 importa tipos gerados pela migration que C1 aplica |
| T2 antes de C0 | a fixture é a fonte da verdade da regra; sem ela T2 e T3 inventam regras diferentes |

## 3. Ownership de arquivo (normativo)

Um arquivo, um dono. Ninguém edita arquivo de outro.

| Arquivo | Dono |
| ------- | ---- |
| `caminho/a.ts` | T2 |
| `caminho/b.tsx` | T9 |

**Somente leitura para todos:** `caminho/c.ts`, `caminho/d.ts`.

## 4. Contratos congelados

Escritos em C0, antes da onda 1. Ninguém altera sem passar pelo coordenador.

### 4.1 <Tipos / interfaces>

    <bloco de código literal e completo>

### 4.2 <Shape de request e response>

    <bloco de código literal e completo>

### 4.3 <Chaves de i18n / props de fronteira / fixture>

    <bloco de código literal e completo>

## 5. Tarefas

### T<n> — <título> · **<Nível>** · <dependências ou "sem dependência">

**Arquivos:** `<caminhos que esta tarefa possui>`

**O que fazer:** <objetivo, em uma ou duas frases>

**Contratos que ela consome:** §4.1, §4.2

**Assume que:** <um fato por linha, cada um com `[MEDIDO: cmd -> resultado]`, `[LIDO:
arquivo:linha]` ou `[SUPOSTO: o que o falsifica]`. Nenhum `[SUPOSTO:]` pode sustentar a
implementação: se sustentar, o primeiro passo desta tarefa e medi-lo, e "se der diferente,
PARE e escale">

**Pronto quando:** <critério verificável, não "quando funcionar">

**Não faça:** <o que pertence a outra tarefa e vai dar vontade de fazer aqui>

### S<n> — Gate de <o quê> · **Complexa** · depende de T<x>, T<y> · **bloqueia C<z>**

**Mandato:** revisar, não corrigir. Devolve aprovação ou lista de problemas.

**Cobre:** <o que exatamente é revisado>

**C<z> não acontece sem o resultado deste gate.**

## 6. Passos exclusivos do coordenador

Só o coordenador roda estes. Nenhum worker.

### C0 — antes da onda 1
1. <verificar árvore limpa>
2. <escrever os contratos congelados de §4>
3. <commitar spec, plano e contratos, com caminhos explícitos>

### C1 — depois de S1 (nunca antes)
1. <aplicar migration>
2. <regenerar tipos>
3. <verificar>

### C<n> — fecho
1. <lint, testes>
2. <commit>
3. Portões de entrega deste projeto: <deploy? bundle? build nativo? publicação?>
4. Documentação viva que precisa acompanhar: <quais arquivos>

## 7. Riscos de orquestração

| Risco | Mitigação |
| ----- | --------- |
| <worker sai do escopo> | ownership normativo em §3 e "não faça" em cada tarefa |
| <contrato divergente> | §4 congelado antes da onda 1 |
```

---

## Notas sobre o esqueleto

**"Pronto quando" tem que ser verificável.** "Quando a tela funcionar" não é critério. "Quando `bunx vitest run caminho/x.test.ts` passar com os 6 casos da fixture" é.

**"Não faça" evita mais colisão que qualquer tabela.** O worker que termina cedo procura o que fazer a seguir. Diga a ele o que é dos outros.

**Gate é tarefa e bloqueio ao mesmo tempo.** Escreva o "bloqueia C<z>" no título, não só no corpo, senão ele vira revisão pós-fato.

**A seção 7 é onde vai o aprendizado operacional da execução anterior.** Se algo custou caro na última vez, ele mora aqui, com a mitigação junto.
