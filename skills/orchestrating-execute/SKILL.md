---
name: orchestrating-execute
description: >-
  Executa um plano de implementação multi-agente já escrito: pergunta ao usuário
  qual modelo vai em cada nível de complexidade, roda os passos que só o
  coordenador pode rodar, sobe os workers onda por onda respeitando o grafo de
  dependências, e para nos gates antes de qualquer passo irreversível. USE
  SEMPRE que existir um plano pronto e o usuário disser "vamos executar",
  "executa o plano", "sobe os workers", "dispara os agentes", "começa a onda 1",
  "roda isso em paralelo", "manda pros agentes", "toca o plano X". Usa a skill
  `orchestration` do Orca para a mecânica de task, dispatch e espera, e
  acrescenta o que é específico de executar um plano: o portão de atribuição de
  modelo, o laço de ondas, o que nunca se delega, e as armadilhas já pagas. Se o
  plano ainda não existe, a skill é `power-plans`, não esta.
---

# Executar um plano multi-agente

## Preflight

Leia o plano inteiro antes de qualquer comando. Ele precisa ter, no mínimo:

- nível de complexidade em cada tarefa;
- matriz de ownership de arquivo;
- contratos congelados escritos literal;
- grafo com dependências e passos do coordenador;
- **um `Pronto quando` por tarefa, copiado de um cenário de aceitação da spec.**

Faltando qualquer um, **pare e volte para `power-plans`**. Executar um plano sem ownership é combinar colisão; sem contrato congelado é combinar divergência; **sem critério de pronto é combinar que o coordenador invente um — e ele vai inventar relendo a spec, que é exatamente onde o sentido se perde.** Custa menos consertar o documento agora.

O quinto item tem uma verificação mecânica, e ela custa segundos:

```bash
for n in $(grep -o 'FR-[0-9]\+' <spec> | sort -u -V); do
  printf '%-6s plano=%s\n' "$n" "$(grep -cw "$n" <plano>)"
done
```

**`-w` não é enfeite:** sem ele `FR-1` casa dentro de `FR-10`, e o requisito que ninguém
citou aparece como coberto. Medido no próprio ciclo que originou este item.

Medido em 2026-09-03 (ciclo `contador-agua`): a spec tinha 13 FRs com cenário executável; o plano citava **6 deles zero vezes** e não tinha nenhum `Pronto quando`. O coordenador escreveu o critério de cada briefing de cabeça, e um campo que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing — dias de descanso ganharam 300 ml que não existiam, e o defeito só apareceu na revisão adversarial do fim. `plano=0` num FR é um requisito que nenhum worker vai ver.

Confirme também que a árvore está limpa do que interessa, e que você sabe quais arquivos modificados **não** são deste trabalho. Sessões paralelas deixam lixo, e ele acaba num commit errado.

## Portão de atribuição de modelo

**Antes de criar qualquer terminal**, pergunte ao usuário qual modelo vai em cada nível:

| Nível | Modelo |
| --- | --- |
| Complexa | ? |
| Média | ? |
| Baixa | ? |

O plano vem com `<MODELO_COMPLEXA>` / `<MODELO_MEDIA>` / `<MODELO_BAIXA>` justamente para essa decisão ser tomada aqui, com o custo e a disponibilidade do dia na mesa. Nunca assuma, nunca herde do plano anterior, e não comece a onda 1 com um nível ainda em aberto.

Se o usuário atribuir um modelo por tarefa em vez de por nível, aceite: a granularidade é dele.

### A atribuição vale para a execução INTEIRA, não só para a onda 1

O time que o usuário definiu governa **toda tarefa que você despachar até o fim do ciclo**: as
ondas seguintes, os gates, e principalmente os **reparos** — worker que morreu, tarefa refeita,
correção de achado, continuação de trabalho parcial. Uma tarefa complexa refeita continua
complexa: ela volta no modelo de complexa, não no que estiver à mão.

Nunca introduza um modelo que o usuário não listou. Se o time não cobre um caso (um revisor
read-only, por exemplo, quando só foram nomeados implementadores), **pergunte** em vez de
escolher: acrescentar um modelo por conta própria é decisão do usuário sendo tomada por você,
e ele descobre depois, pela fatura ou pela qualidade.

### `--model` é OBRIGATÓRIO no `--command`, e você tem que CONFERIR

Esta é a forma mais fácil de violar a regra acima sem perceber, e ela já aconteceu
(2026-09-02, ciclo `corrida-frequencia-e-ritmo-alvo`):

```bash
# ERRADO — sobe no default do CLI, seja ele qual for
orca terminal create --command "claude --permission-mode bypassPermissions"

# CERTO — modelo explícito
orca terminal create --command "claude --model claude-opus-5 --permission-mode bypassPermissions"
```

Sem `--model`, o TUI sobe no **default da instalação** e nada avisa. No caso medido, três
workers de tarefa complexa (T7, T7b, T8) rodaram em Fable enquanto o coordenador **relatava ao
usuário que estavam em Opus 5** — porque ele confundiu a própria intenção com o que tinha
digitado. Quem descobriu foi o usuário, olhando os terminais.

Por isso o `--model` não basta: **confira o modelo no TUI depois de `terminal wait`, antes de
despachar.** É o mesmo cuidado que a armadilha do Codex já exigia (`gpt-5.6` puro sobe e só
falha no primeiro request), e ele vale para todo provedor:

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

## Mecânica: use a skill `orchestration`

Não redocumente o Orca. Para criar run, criar task com dependência, despachar com preâmbulo injetado e esperar `worker_done` / `escalation` / `decision_gate`, siga a skill `orchestration`. Esta aqui só acrescenta o que é específico de executar um plano.

Sequência por worker, na ordem:

1. `run-create` uma vez, no começo. Sem run vinculada, `task-list` falha.
2. `task-create` para cada tarefa, com `--deps` refletindo o grafo do plano. O grafo vira estado, não fica só no documento.
3. `terminal create`, com o flag de bypass de permissão **e o `--model` do nível** dentro da string de `--command`. Confira o modelo no TUI antes do dispatch (ver *Portão de atribuição de modelo*).
4. `terminal wait --for tui-idle` antes de despachar. Terminal que ainda está subindo engole o dispatch.
5. `dispatch --inject` com o preâmbulo abaixo.
6. `check --wait --types worker_done,escalation,decision_gate`.

Armadilhas medidas, que custam tempo quando descobertas na marra: `references/orca-traps.md`. Leia antes da primeira onda.

**Sem Orca disponível**, o plano continua válido: é um grafo com níveis, donos e contratos. Execute com o mecanismo de subagente que houver, mantendo ownership, ordem e gates. O que não se pode perder é o grafo, não a ferramenta.

## O preâmbulo de todo dispatch

Todo worker recebe, sem exceção:

- **Onde está a verdade:** caminho da spec e do plano, e a instrução de ler os dois.
- **Sua tarefa, pelo identificador:** "você é a T5, e só a T5".
- **Seus arquivos, listados.** Mais a frase: nenhum arquivo fora desta lista, nem para "corrigir de passagem".
- **Os contratos que ele consome**, colados literal no dispatch, não por referência. Worker não deve depender de achar a seção certa.
- **O que este projeto proíbe delegar.** Tipicamente git. Diga com essas palavras: não rode comando de git, quem commita é o coordenador.
- **Escalar em vez de improvisar.** Se a tarefa exigir sair do escopo, mudar contrato, ou tocar arquivo de outro, ele manda `escalation` e para. Um worker que improvisa custa mais que um worker que espera.
- **Pronto quando:** o critério da tarefa, **copiado do plano — que por sua vez copiou o cenário da spec**. Se o plano não tem esse critério, você não o escreve de cabeça: volte ao plano (ver *Preflight*). Coordenador improvisando critério de pronto é o defeito, não o conserto.

Worker que recebe contrato por referência e não por valor inventa o contrato. Cole.

### A prova de neutralização só pode tocar arquivo que o worker POSSUI

Peça sempre a prova de neutralização (neutralize o fix, confirme que o teste falha, restaure).
Ela é o que separa teste que trava o defeito de teste decorativo. Mas ela **muta o código de
produção por alguns minutos**, e é aí que mora a armadilha:

> **Se o alvo da neutralização não é um arquivo do worker, a prova é do COORDENADOR, numa cópia
> isolada — nunca do worker, nunca na árvore compartilhada.**

Medido em 2026-09-01. Um brief mandava "remova o `EdgeRuntime.waitUntil` e confirme que a
asserção falha" e, na mesma página, "não edite `handoff-side-effects.ts`". As duas instruções
eram incompatíveis: uma extração anterior tinha **mudado o `waitUntil` de arquivo**, e o brief
foi escrito contra o mapa antigo. O worker fez o razoável, editou o arquivo alheio — e **morreu
no meio** (print mode, `timeout waiting for response`).

O que ficou na árvore: produção sem o `waitUntil`, ou seja, o isolate podendo morrer com a
resposta HTTP e engolir a notificação ao atendente. **E a suíte inteira passava verde**, porque
o único teste que observava aquilo era o que o próprio worker estava escrevendo. Só a medição
isolada do coordenador denunciou.

Três consequências para quem escreve o brief:

1. **Antes de mandar neutralizar, confira em qual arquivo o alvo mora HOJE.** Depois de uma
   extração ou refatoração, o mapa da sua cabeça está velho. Um `grep` resolve.
2. **Neutralização e ownership têm de bater.** Se não batem, o brief está errado — não é o
   worker que tem de escolher qual das duas instruções obedecer.
3. **Trate a árvore como suja até provar o contrário** quando um worker morre. Não confie no
   verde: rode a suíte numa cópia do HEAD limpo mais só os arquivos daquele worker, e compare
   por nome. Verde numa árvore que contém uma neutralização esquecida é verde pelo motivo
   errado.

A regra maior, e ela vale além disto: **restauração que depende de alguém lembrar não é
restauração, é intenção.** A contraparte disso na mecânica de terminais está em
[`references/orca-traps.md`](references/orca-traps.md) (terminal que sobrevive ao
`worker-release`), e a contraparte em dado é `deactivate_stages` nos cenários de E2E, que
restaura sempre, inclusive quando o cenário falha.

## O laço de ondas

Para cada onda:

1. Suba todos os workers da onda **no mesmo momento**. Onda serializada é onda desperdiçada.
2. Espere as conclusões. Trate `escalation` na hora: worker escalando está parado.
3. Rode os passos do coordenador daquela onda, você mesmo.
4. Verifique antes de abrir a próxima. Onda seguinte que começa em cima de passo do coordenador não confirmado propaga o erro para todos os workers de uma vez.

Um `check --wait` que volta só com keepalive e sai não é falha: é ponto de checagem. Confirme que o worker está vivo e rearme a espera.

## O gate adversarial tem um teto, e ele se chama "mesmo emissor de novo"

Medido no ciclo `2026-08-27-canais-sociais-whatsapp`: o gate (revisor read-only, modelo forte,
esforço máximo) **reprovou quatro vezes**, e as quatro acharam defeito real que a suíte verde
não pegava. Mas a rodada 4 reprovou justamente as correções da rodada 3, e **três dos seis
bloqueantes novos eram a MESMA invariante vazando por emissores diferentes**.

Isso não é sinal de que faltava mais revisão. É sinal de que o fix estava indo para o lugar
errado: call site por call site, quando o problema é que existem N emissores. Cada rodada
consertava o emissor citado e o seguinte nascia intacto.

**Quando a lista do gate traz a mesma família de achado em arquivos diferentes, não despache
correção pontual.** O brief da onda de correção tem de proibir o remendo por
call site e exigir um **ponto de estrangulamento**: um único lugar, o mais tarde possível no
fluxo, que decide sobre o ESTADO já persistido em vez de depender de cada emissor ter
lembrado de propagar um sinal. Foi o que fechou o ciclo em uma onda.

Sintoma para reconhecer cedo: você se pega escrevendo, pela terceira vez, "e este caminho
também precisa propagar X".

### O caso mais barato de prevenir: mudou um TIPO compartilhado

Medido em 2026-08-28. Uma tarefa acrescentou um valor a um enum (`execution_status`) para
consertar uma MÉTRICA. Esse enum era lido por **cinco** lugares por igualdade literal; a entrega
verificou um. As revisões seguintes acharam os outros quatro, e dois eram defeito de produção —
um deles invertia exatamente o dedupe que o sistema existe para garantir.

A prevenção não é mais revisão, é uma linha no spec. Quando a tarefa acrescenta valor a um enum,
campo a um contrato, ou estado a uma máquina de estados, exija como ENTREGÁVEL:

> O inventário dos consumidores, obtido por `grep`, com a decisão explícita para cada um.
> `grep -rn '"<valor-antigo>"' <raiz> --include=*.ts`

E prefira, quase sempre, a regra que torna o inventário inofensivo:

> **Rótulo novo não muda comportamento.** Se o valor existe para relatório ou telemetria, o
> sistema tem de se comportar byte a byte como antes; quem responde a pergunta semântica é um
> predicado único, e as igualdades literais que sobrarem são exceções DECLARADAS, com o motivo
> escrito ao lado.

Com essa regra, achar um sexto consumidor depois vira anotação; sem ela, vira incidente.

E a nota que fecha o ciclo: **o quinto consumidor foi encontrado pela DOCUMENTAÇÃO.** Ao
atualizar a skill do projeto no fim do trabalho, o coordenador leu uma frase que ela já afirmava
e que nomeava um leitor fora do inventário. Atualizar documentação no mesmo ciclo não é só
higiene: é uma passada de revisão sobre uma descrição do sistema que ninguém tinha relido.

**E há um custo de tempo real:** cada rodada de gate custou ~20-40 min de revisão mais uma
onda de correção. Duas rodadas a mais do que o necessário é meia sessão. Por isso o gate
roda uma vez (seção *Gates*, abaixo): quem julga a correção é o teste que ela traz, e a correção
tem de ser ESTRUTURAL para um teste valer por todos os emissores.

## Gates

Um gate tem `worker_done` como qualquer tarefa, mas o que ele autoriza é um passo **seu**, não a próxima onda.

- Gate aprovou: rode o passo do coordenador que ele guardava.
- Gate reprovou: **não rode**. Despache cada correção como tarefa nova, com dono e com o teste que
  falha antes do fix e passa depois. O gate **não roda de novo**: a rodada seguinte é a suíte.

Nunca rode o passo irreversível "enquanto o gate roda". O ganho é minutos; a perda é migration aplicada em produção sem `git revert`, ou deploy que republica módulo compartilhado de uma branch atrasada.

Revisão que volta com achados **não autoriza o coordenador a corrigir por conta própria**. Sintetize, decida quem é o dono da correção, e despache. Se a decisão for de negócio e não técnica, leve ao usuário com resumo e recomendação.

### Um gate, uma rodada

"Executa, gate, corrige, gate de novo" não tem fim natural: revisar é achar, e cada rodada acha.
Decidido pelo usuário em 2026-09-12, depois de ciclos em que esse laço não convergia. O ciclo
fechado tem um sentido só:

    execução -> gate (uma vez) -> correções -> teste -> passou: passo do coordenador
                                                     -> falhou: systematic-debugging -> teste

1. **O gate roda uma vez** e devolve a lista de achados com prova. Segunda rodada do mesmo
   gate só por pedido explícito do usuário, nunca por decisão do coordenador.
2. **Correção não volta ao gate; vai para o teste.** Cada achado aceito vira tarefa com dono, e
   o `Pronto quando` dela é um teste que falha antes do fix e passa depois. Confira cada achado
   você mesmo antes de despachar, e cada correção contra o achado depois. O revisor não é
   chamado para conferir a própria lista.
3. **Teste falhou é investigação, não revisão.** Suíte ou E2E reprovando depois das correções
   entra em `systematic-debugging`: causa raiz, um conserto, teste de novo. Três consertos
   falhados no mesmo teste viram questão de arquitetura, como aquela skill já manda.
4. **Passou: rode o passo irreversível que o gate guardava.** Gates diferentes do plano
   (contratos, segurança) têm cada um a sua rodada única; o que não existe é a rodada dois de
   um gate que já rodou.

O que protege o passo irreversível nesse desenho é a forma da correção: estrutural, num ponto
de estrangulamento (seção acima), com o teste que trava o defeito. Remendo por call site sem
teste era o que fazia o gate ser chamado de novo.

## Passos que são sempre seus

Descubra no `CLAUDE.md` / `AGENTS.md` do projeto o que não se delega. Quase sempre inclui:

- git: `add` com caminhos explícitos, `commit`, `push`;
- aplicar mudança de schema;
- deploy de função ou serviço;
- publicação para usuário.

Estes são os passos que definem onde as ondas quebram. Se você se pegar delegando um deles, o grafo do plano estava errado, não o projeto.

Ao commitar, estage caminho por caminho e confira o que está estagiado. Em checkout compartilhado por sessões paralelas, `add -A` varre trabalho alheio para dentro do seu commit, e ninguém acha depois pelo histórico.

## Fecho

1. Rode lint e testes do projeto, você mesmo.
2. Commite com caminhos explícitos.
3. Responda os portões de entrega do projeto, sem esperar o usuário perguntar. Se o projeto entrega por bundle ou build nativo, diga sim ou não para cada um.
4. Atualize a documentação que este projeto exige atualizar no mesmo commit.
5. Feche as tasks no Orca com o resultado real. Task que fica aberta some do radar e reaparece como confusão na próxima sessão.
6. Relate ao usuário o que ficou de fora, se ficou, e por quê.
7. Uma linha por skill do ciclo (`spec-interview`, `power-plans`, esta): o que entra, em qual
   arquivo, ou *"nada entra, porque X"*. Lição que fica só no relatório de revisão é lição que a
   próxima spec paga de novo.

Se alguma armadilha nova aparecer durante a execução, acrescente-a a `references/orca-traps.md` no mesmo trabalho. É a única forma de a próxima execução não pagar de novo.
