# Exemplo: plano de implementação (multi-agente)

**Spec:** `docs/specs/feito/exemplo-design.md`
**Evidência:** `docs/evidencia.md`
**Escala escolhida:** mínima, porque é um exemplo de teste
**Estado:** a fazer

## 0.1 Afirmações de carga

| # | Afirmação | Falsificador | Consulta ou grep que conta o falsificador | Contagem | Consequência |
|---|---|---|---|---|---|
| A1 | o alfa é a única porta | outra porta no módulo | `grep -rlE 'porta\|entrada' src/` | 0 | redesenho |

## 1. Níveis de complexidade

| Nível | Modelo | Critério |
| --- | --- | --- |
| Complexa | <MODELO_COMPLEXA> | erro caro |
| Média | <MODELO_MEDIA> | escopo claro |
| Gate / Advisor | <MODELO_GATE> | revisão adversarial |

## 2. Grafo de execução

Ondas: W1 e W2 não rodam juntas, porque mexem no mesmo módulo.

## 3. Ownership de arquivo (normativo)

| Arquivo | Dono |
| --- | --- |
| `app/functions/motor/_lib/alpha.ts` + `_test.ts` | T1 |
| NOVO `app/functions/motor/_lib/gamma.ts` (irmão: `_lib/beta.ts`; descoberto por `scripts/run-check.mjs`) | T2 |
| `src/modulo.ts` | T3 |
| NOVO `scripts/novo-cmd.mjs` (irmão: `scripts/run-check.mjs`) | T3 |

## 3.1 Traçado por requisito

| FR | Onde nasce | Quem transporta | Quem decide | Quem emite | Efeito observável |
| --- | --- | --- | --- | --- | --- |
| FR-1 | `app/functions/motor/_lib/alpha.ts:3` | `beta.ts:2` | `src/modulo.ts:2` | `gamma.ts:1` | o usuário vê a coisa um |
| FR-2 | `alpha.ts:5` | `beta.ts:3` | `src/modulo.ts:3` | — | o usuário vê a coisa dois |
| FR-10 | `alpha.ts:7` | `beta.ts:4` | `src/modulo.ts:4` | `gamma.ts:3` | o usuário vê a coisa dez |

## 5. Tarefas

### T1: alfa · **Média** · sem dependência

**Arquivos:** `alpha.ts`, `alpha_test.ts`.
**O que fazer:** cria o alfa.
**Cobre:** FR-1, FR-2.
**Assume que:** `[LIDO: app/functions/motor/_lib/alpha.ts:3-5]` o alfa tem a função; `[MEDIDO: grep -c alfa src/ -> 1]` há um único alfa.
**Pronto quando:** **Dado** um lead, **quando** o alfa roda, **então** a coisa um acontece.
**Não faça:** mexer no beta.
**Camada de prova:** unitário.

### T2 — gama · **Média** · depende de T1

**Cobre:** FR-10.
**Assume que:** `[LIDO: beta.ts:2]` o beta exporta a função; `[SUPOSTO: se o alfa mudar de assinatura, o gama quebra]`. Se der diferente, PARE e escale.
**Pronto quando:** **Dado** um lead, **quando** o gama roda, **então** a coisa dez acontece.

### T3 — módulo e comando · **Baixa** · sem dependência

**Cobre:** infra, sem FR
**Assume que:** `[LIDO: src/modulo.ts:4]` o módulo tem quatro linhas; `[LIDO: revisão, ensaio]` vale.
**Pronto quando:** o comando novo roda sem erro.

### S1 — Gate do candidato · **Gate / Advisor** (`<MODELO_GATE>`) · depende de T3 · **bloqueia C1**

**Mandato:** revisar, não corrigir.

### PV — Aprovação visual · passo manual

A pessoa responsável aprova o protótipo.

## 5.1 Rastreabilidade

| FR | Cenário que vira o "Pronto quando" | Tarefa |
| --- | --- | --- |
| FR-1 | dado um lead, quando o alfa roda, então a coisa um | T1 |
| FR-2 | dado um lead, quando o alfa roda, então a coisa dois | T1 |
| FR-10 | dado um lead, quando o gama roda, então a coisa dez | T2 |

## 6. Passos exclusivos do coordenador

### C0 — antes da onda 1

```bash
FOO=1 node scripts/run-check.mjs
bash scripts/deploy.sh
```

Depois, confira `scripts/novo-cmd.mjs`, que o T3 cria.
