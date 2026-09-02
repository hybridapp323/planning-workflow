# Esqueleto da spec

Copie a estrutura, não o conteúdo. Corte seções que a feature não usa, e diga que cortou.
Só existe no caminho arquitetural; sonda e limitada não ganham arquivo de spec.

---

```markdown
# <Feature> — spec de design

**Data:** AAAA-MM-DD · **Status:** rascunho | aprovada em AAAA-MM-DD
**Plano:** `<caminho do plano, preenchido quando ele existir>`

## 0. Como ler esta spec

Requisito tem id (`FR-n`) e cenário de aceitação. Critério de sucesso tem id (`SC-n`) e
número. Decisão tem autoria. Fato tem etiqueta de procedência. O plano cita os ids: um
requisito removido fica marcado *removido*, nunca renumera os outros.

## 1. Problema

O que dói hoje, para quem, em que condição, e por que agora. Com a medição que sustenta:
`[MEDIDO: <query ou comando> -> <resultado cru>]`. Sem medição, `[SUPOSTO: <o que
provaria que não é assim>]`.

## 2. Critérios de sucesso

Como se mede que funcionou, do ponto de vista de quem usa, não do sistema. Número, prazo,
taxa ou contagem, com a baseline de hoje.

| ID | Critério | Baseline hoje | Como se mede |
| --- | --- | --- | --- |
| SC-1 | <ex.: "a primeira resposta chega em menos de 60 s"> | <ex.: "p50 = 4 min"> | <query, métrica, evento> |

## 3. Fora de escopo

O que esta feature explicitamente NÃO faz, um item por linha. Item que alguém pode achar
que está incluído vem com a razão.

- <o que não faz>: <por quê>

## 4. Requisitos

Um por bloco, testável, com id estável, e pelo menos um cenário de aceitação cada.

### FR-1 — <título>

<o que o sistema faz, em uma frase que dá para testar>

- **Dado** <estado inicial>, **quando** <ação>, **então** <resultado observável>.
- **Dado** <outro estado>, **quando** <ação>, **então** <resultado>.

### FR-2 — <título>

...

## 5. Casos de borda e caminho ruim

Erro, vazio, offline, timeout, sem permissão, dado que já existe, duplicado, concorrência,
limite. Cada caso diz o que acontece, ou aponta o FR que já cobre.

| Caso | O que acontece | FR |
| --- | --- | --- |
| <ex.: "a integração externa não responde"> | <comportamento> | FR-n |

## 6. Estado anterior

O que acontece com quem já usa a versão de hoje: dado legado, migração,
retrocompatibilidade, flag, janela em que o velho e o novo convivem.

## 7. Quem mais consome (bidirecional)

Quem **lê** o dado, campo, tela ou arquivo que isto muda; e quem mais **escreve ou emite**
o comportamento que isto altera. Feature nova morre em consumidor esquecido; feature que
remove comportamento morre em emissor esquecido.

| Quem | Lê / emite | O quê | Decisão |
| --- | --- | --- | --- |
| <job, tela, exportação, função> | lê | <campo> | mantido / adaptado / removido porque <razão> |

## 8. Design

Arquitetura, componentes, tratamento de erro. Uma unidade por bloco: o que faz, como se
usa, de que depende.

### 8.1 Fluxo do dado

    onde nasce  ->  quem transporta  ->  quem decide  ->  quem emite  ->  quem consome

Cada salto é um lugar que pode descartar o que você criou.

### 8.2 Contrato de dados

Formato no nível do comportamento: campos, tipos, semântica, o que é obrigatório, o que
pode ser nulo e o que nulo significa. O plano congela o literal em código a partir daqui.
Esta seção é a fonte do contrato congelado, não o substitui.

## 9. Decisões, com autoria

| # | Decisão | Autoria | Rodada / razão |
| --- | --- | --- | --- |
| D1 | <decisão> | usuário | <rodada n> |
| D2 | <decisão> | assumida por mim | <por quê, e o que muda se for outra> |

As assumidas são a lista de revisão do usuário.

## 10. Alternativas descartadas

Sempre inclui a mais simples e a de não fazer.

| Alternativa | Por que foi descartada |
| --- | --- |
| Não fazer / fazer menos: <o que seria> | <razão> |
| <abordagem B> | <razão> |

## 11. Premissas

Fato de que o design depende, um por linha, com `[MEDIDO:]`, `[LIDO: arquivo:linha]` ou
`[SUPOSTO: <o que o falsifica>]`. Premissa `[SUPOSTO:]` de que um FR depende vira medição
na fase de evidência do plano.

## 12. Como se prova

Para cada FR: tipo de prova (unitário, integração, ponta a ponta, medição em produção) e o
que ela tem que demonstrar. Prova que só existe escrita é hipótese.

| FR | Tipo de prova | O que demonstra |
| --- | --- | --- |
| FR-1 | <tipo> | <o que tem que falhar se o FR não valer> |

## 13. Decisões em aberto

Só existe se o usuário mandou parar com decisão aberta. Cada linha: a decisão, o default
assumido, o que muda se for outro.
```

---

## Notas sobre o esqueleto

**Ids são estáveis.** `FR-n` e `SC-n` são o que o plano, o gate e o teste vão citar. Requisito
que sai fica marcado *removido* com a razão; renumerar quebra toda referência que já existe.

**Cenário de aceitação é de onde nasce o "Pronto quando".** Cada tarefa do plano termina num
critério verificável, e o lugar mais barato de escrevê-lo é aqui, antes de existir tarefa. Um
FR sem cenário é um requisito que ninguém sabe como provar.

**Contrato aqui, contrato no plano: são dois níveis, não duplicação.** §8.2 fixa o contrato no
nível do comportamento (o que o campo significa, quando é nulo). O plano congela o literal em
código (tipo, interface, fixture) antes da primeira onda. Não tente fundir os dois: o da spec
sobrevive a uma mudança de linguagem; o do plano é o que dois workers em paralelo precisam.

**§5 e §7 são a matriz de consumidores que o plano hoje conserta a posteriori.** Escritas aqui,
elas chegam ao plano prontas, em vez de aparecerem na validação da spec como lacuna.

**A etiqueta de procedência é a mesma do plano** (`[MEDIDO:]`, `[LIDO:]`, `[SUPOSTO:]`, ver
`power-plans`). Uma spec que já etiqueta as premissas diz à fase de evidência do plano o que
ainda precisa ser medido, sem obrigar a reler tudo.

**Seção que não se aplica é cortada, e o corte é dito.** Seção preenchida com enchimento para
"completar o template" é o defeito que este esqueleto existe para evitar: ela parece rigor e
esconde o que faltou perguntar. Duas linhas honestas ("não há estado anterior: a tabela é nova")
valem mais que um parágrafo genérico.
