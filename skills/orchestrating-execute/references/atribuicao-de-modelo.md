# Portão de atribuição de modelo

Referência da skill `orchestrating-execute`. Leia antes de criar o primeiro terminal e sempre que for despachar um reparo.

## Portão de atribuição de modelo

**Antes de criar qualquer terminal**, pergunte ao usuário qual modelo vai em cada nível:

| Nível | Modelo | Esforço |
| --- | --- | --- |
| Complexa | ? | ? (vazio: você decide por tarefa) |
| Média | ? | ? (vazio: você decide por tarefa) |
| Baixa | ? | ? (vazio: você decide por tarefa) |
| Gate / Advisor | ? | ? (sempre do usuário) |
| Coordenador de onda | ? (só com ondas em worktrees separadas) | |

O plano vem com `<MODELO_COMPLEXA>` / `<MODELO_MEDIA>` / `<MODELO_BAIXA>` / `<MODELO_GATE>` justamente para essa decisão ser tomada aqui, com o custo e a disponibilidade do dia na mesa. Nunca assuma, nunca herde do plano anterior, e não comece a onda 1 com um nível ainda em aberto.

**A linha `Gate / Advisor` é uma só, de propósito.** O advisor (seção *O advisor*, abaixo) roda
no mesmo modelo que o usuário escolheu para o gate, e não existe sem essa linha preenchida.
Peça-a quando o plano tem gate, ou quando o usuário pediu revisão; se ele já nomeou o modelo no
pedido ("use tal modelo para a revisão adversarial"), use esse e não pergunte de novo. Plano sem
gate e sem revisão pedida: deixe a linha vazia e pergunte só se um gatilho do advisor disparar.
Nunca herde o modelo de Complexa para esse papel.

Se o usuário atribuir um modelo por tarefa em vez de por nível, aceite: a granularidade é dele.

### Esforço: do usuário quando ele nomeia, seu por tarefa quando não

Esforço alto paga exploração e decisão. Quando o worker começa, a spec já decidiu, o plano já
explorou e os contratos estão congelados; o que sobra é escopo fechado, e o seu aceite confere o
resultado de graça. Esforço máximo num worker paga de novo um raciocínio já feito. Decidido pelo
usuário em 07/10/2026, depois de ver coordenadores pondo toda tarefa complexa em `xhigh` e
workers em `max`.

1. **Esforço nomeado pelo usuário vale para o ciclo inteiro**, reparos inclusive, como o modelo.
   "Tudo em `xhigh`" é `xhigh` em tudo, sem você rebaixar.
   **Esforço fixado por modelo também é esforço nomeado, mesmo que o pedido do ciclo não o repita.**
   Se o usuário já fixou o esforço de um modelo (na memória, na configuração do CLI ou no catálogo
   da skill `orchestration`, ex.: "esse modelo só em `xhigh`"), ele vale para toda tarefa daquele
   modelo, de qualquer nível; a tabela abaixo nunca o rebaixa. Medido em 04/11/2026: com o pedido
   nomeando só o modelo das médias, o coordenador aplicou "Média: `medium`" a um modelo que o
   usuário só aceitava em `xhigh`, aceitou o worker pelo rodapé e teve de refazer a tarefa.
2. **Sem esforço nomeado, você escolhe por tarefa, entre `medium` e `xhigh`.** Nunca `low`, nunca
   `max` ou acima num worker.
   - **Baixa:** `medium`.
   - **Média:** `medium`; `high` se a tarefa produz um contrato que outras tarefas consomem.
   - **Complexa:** `high`. `xhigh` só quando ela carrega o que o plano não pôde resolver de
     antemão: precedência ou invariante que vale em vários pontos, concorrência, dado de produção
     ou passo irreversível, ou muitos arquivos e contratos segurados ao mesmo tempo. Ser grande
     ou difícil não basta; o plano já a desmontou.
   - **Reparo:** volta no esforço da tarefa original. Sobe um degrau uma vez, com o motivo
     escrito na task, se a tarefa já voltou duas vezes no aceite.
3. **Gate e advisor ficam fora disso:** o esforço deles é do usuário, e pode ser `max` ou acima.
   Rodam uma ou duas vezes por ciclo, e o trabalho deles é achar o que ninguém decidiu; é aí que
   o esforço máximo se paga (`references/correcao-pos-gate.md`). Linha vazia: pergunte.

O esforço sobe pelo argumento que o CLI do worker aceita (alguns embutem no id do modelo; ver
`references/orca-traps.md`) e se confere no rodapé do TUI junto com o modelo, na mesma leitura.

### A atribuição vale para a execução INTEIRA, não só para a onda 1

O time que o usuário definiu governa **toda tarefa que você despachar até o fim do ciclo**: as
ondas seguintes, os gates, e principalmente os **reparos** — worker que morreu, tarefa refeita,
correção de achado, continuação de trabalho parcial. Uma tarefa complexa refeita continua
complexa: ela volta no modelo de complexa, não no que estiver à mão.

Nunca introduza um modelo que o usuário não listou. Se o time não cobre um caso (um revisor
read-only, por exemplo, quando só foram nomeados implementadores), **pergunte** em vez de
escolher: acrescentar um modelo por conta própria é decisão do usuário sendo tomada por você,
e ele descobre depois, pela fatura ou pela qualidade.

### Antes de criar o primeiro terminal, faça um smoke de cada modelo atribuído

Um modelo listado no catálogo do CLI não é um modelo que responde. Antes da onda 1, rode **uma
chamada headless de uma linha** para cada modelo do portão, no mesmo CLI que o worker vai usar,
e só crie terminal depois de ler a resposta. As duas falhas medidas aqui eram invisíveis até o
primeiro request:

- **O CLI instalado é mais velho que o modelo.** O id aparece no catálogo local, o TUI sobe e
  mostra o modelo no rodapé, e o primeiro request volta recusado. O conserto é atualizar o CLI,
  não trocar de modelo.
- **A rota do provedor está sobrecarregada, e o mesmo modelo responde por outra.** Um CLI que
  agrega provedores pode servir o mesmo modelo por duas rotas; uma devolve sobrecarga e timeout
  enquanto a outra responde. Trocar de rota mantém a atribuição do usuário (mesmo modelo), mas
  diga a ele em uma linha e registre no documento do ciclo. Trocar de MODELO continua proibido
  sem perguntar.

Medido em 29/09/2026: dois dos quatro modelos atribuídos falharam no smoke, um por versão do CLI
e outro por rota. Os dois foram resolvidos antes de qualquer despacho, em minutos. Descobertos
depois do despacho, teriam custado um worker parado parecendo vivo cada. Os comandos e as
mensagens exatas estão em `references/orca-traps.md`.

### `--model` é OBRIGATÓRIO no `--command`, e você tem que CONFERIR

Esta é a forma mais fácil de violar a regra acima sem perceber, e ela já aconteceu
(2026-09-02):

```bash
# ERRADO — sobe no default do CLI, seja ele qual for
orca terminal create --command "claude --permission-mode bypassPermissions"

# CERTO — modelo explícito
orca terminal create --command "claude --model <id do modelo> --permission-mode bypassPermissions"
```

Sem `--model`, o TUI sobe no **default da instalação** e nada avisa. No caso medido, três
workers de tarefa complexa rodaram no modelo padrão da instalação enquanto o coordenador
**relatava ao usuário que estavam no modelo pedido**, porque confundiu a própria intenção com o
que tinha digitado. Quem descobriu foi o usuário, olhando os terminais.

Por isso o `--model` não basta: **confira o modelo no TUI depois de `terminal wait`, antes de
despachar.** É o mesmo cuidado de todo CLI em que um id de modelo incompleto sobe e só falha no primeiro
request (`orca-traps.md`), e ele vale para todo provedor:

```bash
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 120000
orca terminal read --terminal <handle>    # o rodapé/cabeçalho tem que mostrar o modelo pedido
```

Se o que aparecer não for o que o usuário pediu, **feche o terminal e recrie**. Não despache
"só para não perder o boot": um worker no modelo errado produz trabalho que você vai ter de
descartar, e descartar custa mais que recriar.

**Quando descobrir tarde**, com o worker já trabalhando: pare o worker, **salve o diff** no
scratchpad antes de reverter (ele pode conter achados reais que valem para o brief novo),
restaure os arquivos, e refaça a tarefa no modelo certo com um brief que já incorpore o que
foi aprendido. Feche a task antiga com o motivo escrito — `task-list` é a fonte de verdade da
invariante de fim de turno, e uma task fechada sem motivo vira confusão na próxima sessão.
