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
  modelo, o laço de ondas, o advisor de rumo com orçamento, o que nunca se delega, e
  as armadilhas já pagas. Se o plano ainda não existe, a skill é `power-plans`, não esta.
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

Medido em 2026-09-03: a spec tinha 13 FRs com cenário executável; o plano citava **6 deles zero vezes** e não tinha nenhum `Pronto quando`. O coordenador escreveu o critério de cada briefing de cabeça, e um campo que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing — um valor inventado entrou na conta como se fosse medido, e o defeito só apareceu na revisão adversarial do fim. `plano=0` num FR é um requisito que nenhum worker vai ver.

Confirme também que a árvore está limpa do que interessa, e que você sabe quais arquivos modificados **não** são deste trabalho. Sessões paralelas deixam lixo, e ele acaba num commit errado.

**Revisão da spec ou do plano dentro do grafo não é passo de execução.** Se o plano traz uma
tarefa que revisa o próprio plano (um `S0 — revisão externa do plano`, "bloqueia a onda 1"), ela
só roda se o usuário pediu a revisão nesta sessão, com o modelo que ele nomeou. Sem pedido: pule,
diga em uma linha que pulou, e comece em C0 / onda 1. Medido em 2026-09-22: um executor abriu o
ciclo despachando o revisor do plano, uma task no run e nenhum worker, sem que o usuário tivesse
pedido revisão. Gate (`S<n>` sobre código escrito, antes de passo irreversível) é outra coisa e
segue a seção *Dois mecanismos de qualidade*.

## Portão de atribuição de modelo

**Antes de criar qualquer terminal**, pergunte ao usuário qual modelo vai em cada nível:

| Nível | Modelo |
| --- | --- |
| Complexa | ? |
| Média | ? |
| Baixa | ? |
| Gate / Advisor | ? |

O plano vem com `<MODELO_COMPLEXA>` / `<MODELO_MEDIA>` / `<MODELO_BAIXA>` / `<MODELO_GATE>` justamente para essa decisão ser tomada aqui, com o custo e a disponibilidade do dia na mesa. Nunca assuma, nunca herde do plano anterior, e não comece a onda 1 com um nível ainda em aberto.

**A linha `Gate / Advisor` é uma só, de propósito.** O advisor (seção *O advisor*, abaixo) roda
no mesmo modelo que o usuário escolheu para o gate, e não existe sem essa linha preenchida.
Peça-a quando o plano tem gate, ou quando o usuário pediu revisão; se ele já nomeou o modelo no
pedido ("use tal modelo para a revisão adversarial"), use esse e não pergunte de novo. Plano sem
gate e sem revisão pedida: deixe a linha vazia e pergunte só se um gatilho do advisor disparar.
Nunca herde o modelo de Complexa para esse papel.

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
(2026-09-02):

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

## Portão de capacidade: meça o que o worker ALCANÇA antes de escrever o brief

Um brief diz o que fazer e, quase sempre, o que **não** dá para fazer. A segunda metade costuma
ser escrita de cabeça, e é onde mora o erro que não tem conserto barato: a proibição inventada.

> **Nunca escreva no brief que o worker não pode fazer algo sem ter provado que ele não pode.**

O worker obedece. Ele não testa, não contradiz e não escala, porque uma proibição no brief se
parece com um fato do projeto. Se a capacidade proibida era necessária à tarefa, **você vira o
terminal dele**: ele escreve, manda para você, você executa, você cola a saída de volta, ele
corrige. Medido em 2026-09-21: 13 idas e voltas assim, ~3 h de uma onda, por uma capacidade que
existia desde o começo dos dois lados. O coordenador parou de coordenar.

Antes da primeira onda, para cada capacidade que a tarefa vai exigir — executar consulta, chamar
API, subir serviço, rodar a suíte — faça três coisas, nesta ordem:

1. **Rode o comando.** Um smoke de uma linha, contra o mesmo recurso que a tarefa usa. Alcance é
   a única prova de alcance; ler documentação não é medir.
2. **Leia a configuração do agente DO WORKER, não só a sua.** Cada CLI de agente tem o arquivo
   dele. O worker pode ter servidor de ferramenta que você não tem, e você pode ter o que ele não
   tem — as duas direções já custaram ciclo. A barra de status do TUI costuma mostrar quantos
   carregaram: contador diferente de zero é convite a descobrir qual.
3. **Escreva a capacidade e o comando exato no brief.** Nomear a ferramenta custa uma linha e
   poupa o turno que o worker gastaria procurando. Procurar às vezes termina em "não existe".

Duas regras de leitura, as duas pagas no mesmo ciclo:

- **`--help` truncado não é ausência.** Saída cortada por `head`, paginada, ou recortada por um
  cabeçalho que mudou de nome entre versões devolve "não achei" — e "não achei" não é "não tem".
  Rode o `--help` inteiro, ou procure o subcomando pelo nome, antes de concluir.
- **Medição que contradiz a documentação do projeto: desconfie da medição primeiro.** O documento
  pode estar velho, mas alguém o escreveu com aquilo funcionando. Enquanto o seu comando diz não
  e o documento diz sim, o ônus é seu: meça de outra forma antes de declarar o documento
  desatualizado. Inverter essa ordem é como uma medição errada vira proibição no brief.

Sintoma para reconhecer em uma linha: **você executou, em nome do worker, o mesmo tipo de comando
duas vezes.** Na segunda, pare e conserte o acesso dele em vez de repetir o serviço. Na terceira,
o problema já não é a tarefa.

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

E a contraparte do portão acima: **proibição só se escreve depois de medida.** O que você não mediu entra como incerteza com um comando junto (*"não sei se há <capacidade> aqui; teste com `<comando>` e me diga o que voltou"*), nunca como um "você não tem isso".

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

1. Suba todos os workers da onda **no mesmo momento**, pelo caminho que dá posse do terminal
   (`wave.sh spawn`, que é `worker-start`). Onda serializada é onda desperdiçada, e terminal sem
   dono registrado é terminal que ninguém consegue fechar com prova.
2. Espere as conclusões. Trate `escalation` na hora: worker escalando está parado.
3. **A cada `worker_done`, feche o ciclo daquele worker sem esperar que o usuário peça:** leia o
   relatório, aceite com casos seus, confira a task, feche o terminal. A sequência exata está na
   seção seguinte.
4. Rode os passos do coordenador daquela onda, você mesmo.
5. Verifique antes de abrir a próxima. Onda seguinte que começa em cima de passo do coordenador
   não confirmado propaga o erro para todos os workers de uma vez. E abra a próxima com a árvore
   limpa: todos os `worker_done` da onda aceitos, terminais fechados, e `wave.sh sweep`
   respondendo que não há terminal de task encerrada aberto.

Um `check --wait` que volta só com keepalive e sai não é falha: é ponto de checagem. Confirme que o worker está vivo e rearme a espera.

### O que fazer a cada `worker_done`: aceitar, conferir a task, fechar

O `worker_done` é o worker dizendo que terminou. O runtime marca a task `completed` (ou `failed`)
sozinho e preenche o `result` com o relatório dele; o que ele NÃO faz é o seu trabalho: aceitar
com casos seus e fechar o terminal. Isso é parte da coordenação, não favor que o usuário pede.
Relatado pelo usuário em 22/09/2026, nos três sistemas em que o plano roda: o coordenador só
fechava terminal quando mandavam, e a árvore do Orca acumulava os TUIs já entregues, cada um
segurando a RAM inteira do agente. Medido em 13/09/2026: dois workers entregues a ~900 MB cada,
e o aperto de memória matou uma tarefa de background do coordenador; em outra execução, 20+
terminais mortos na interface.

Para cada `worker_done`, nesta ordem, e nenhum passo pula o anterior:

1. **Leia o relatório e o diff.** `wave.sh report <task>` traz o corpo do `worker_done`, os
   arquivos e o diff; `dispatch-show` não traz o corpo.
   **Antes de ler o conteúdo, confira o ESCOPO, que é mecânico:** a lista de arquivos alterados
   pelo worker contra a lista de arquivos do brief. Numa árvore compartilhada por vários workers,
   o `git status` mistura as entregas: tire um retrato dos arquivos modificados (caminho e hash)
   ao despachar, e na entrega compare. Arquivo fora da lista é devolução, ou restauração sua a
   partir do HEAD, mesmo que o conteúdo pareça certo. Isso inclui arquivo gerado (lockfile,
   cache, saída de build) que o worker regravou ao rodar ferramentas: restaure, e não commite.
   Medido em 25/09/2026: um worker de nível médio sobrescreveu um arquivo de outra área com a
   cópia de um arquivo irmão, e outro deixou um lockfile regravado; os dois apareceram por acaso,
   lendo diff. A comparação de listas os pega na entrega, em segundos.
2. **Aceite com casos seus.** Rode o `Pronto quando` com casos que não são os do worker e confira
   a prova de neutralização (seção *Dois mecanismos de qualidade*). Tarefa que mexe em detector
   de texto: seus casos saem de frases reais do histórico e da lista de variações do plano
   (negação, erro de digitação, outra flexão, acento colado no termo), não da frase do relatório.
   Foi assim que o aceite pegou dois dos defeitos dessa família em 25/09/2026.
   - **Não passou:** a correção é uma **task nova** (`T<n>b`), despachada **para o mesmo
     terminal** (`dispatch --task <nova> --to terminal:<handle>`): o contexto do worker vale mais
     que refazer do zero. A task original já está `completed` e o terminal continua vivo de
     propósito. **Não feche nem varra esse terminal enquanto a continuação estiver viva:** o
     `sweep` lista a task antiga como encerrada, e o `close` dela mataria a nova. Feche no aceite
     da ÚLTIMA task daquele terminal. Medido em 20/09/2026: uma tarefa complexa levou três tasks
     no mesmo terminal até o aceite, e o terminal só fechou depois da terceira.
   - **Passou:** siga.
3. **Confira a task no `task-list`:** ela já está `completed`, com o `result` do próprio worker
   (`provenance: worker_report`). Não a reescreva com `task-update`: isso apaga a proveniência.
   `task-update` é para o worker que morreu sem `worker_done` (`--status failed --result
   '{"reason":…}'`); cancelar também é `--status failed`, com o motivo no `result`, porque não
   existe status `cancelled`. O seu aceite fica registrado no documento do ciclo, com o comando
   que o provou.
4. **Feche o terminal, a aba e a entrada na árvore:** `wave.sh close <task>`. Ele escolhe o
   caminho pela posse (`worker-release` para terminal que o `worker-start` criou; `terminal close
   --tab` para terminal que você criou pelo `wave create`), mata o processo do agente e confere
   que o handle sumiu. Ele recusa task fora de status terminal, o terminal do coordenador e
   qualquer terminal sem prova de posse: a sessão do usuário nunca é fechada por engano. Sem
   `wave.sh` na máquina, o comando cru é o mesmo nos três sistemas e vale só para terminal que
   VOCÊ criou: `orca terminal close --terminal <handle> --tab --json` (`--tab` fecha a aba
   inteira; sem ele o pane fica vivo consumindo memória; o primeiro `ok:false` é retry, não
   falha).
5. **Confira na lista, não no recibo:** o handle não aparece mais em `orca terminal list --json`.
   Se o `close` disse que fechou e o handle ainda aparece, a aba ficou na árvore: `orca terminal
   close --terminal <handle> --tab --json`, e registre o caso em `references/orca-traps.md`. Se
   ele disse que o release ficou pendente e o terminal continua vivo, siga o recibo; não force.

Quando TODOS os `worker_done` da onda estiverem aceitos e nenhuma continuação estiver viva, rode
`wave.sh sweep`: ele fecha o que sobrou e tem de responder que não há terminal de task encerrada
aberto. Não o rode no meio de uma correção.

Duas exceções, e só estas:

- **Continuação viva no mesmo terminal** (passo 2, "não passou"): fecha no aceite da última.
- **Terminal de gate que vai receber o fix mais complexo da própria lista:** reaproveitar o
  contexto do revisor já pagou; vale a mesma regra da continuação.

Fora disso, terminal de task aceita que continua aberto é erro seu, não pendência do usuário.

## Dois mecanismos de qualidade, e só um deles é o gate

**Aceite do coordenador** é contínuo, barato e sem orçamento. Todo `worker_done` passa por
você antes de contar como entregue: leia o diff, rode o `Pronto quando` com casos SEUS (nunca só
os do worker), confira a prova de neutralização. Não passou no rigor: devolva ao mesmo worker, no
mesmo terminal, com o que falta, quantas vezes precisar. Aceitou: confira a task e feche o
terminal na hora (*O que fazer a cada `worker_done`*, acima). Isso é coordenar, não é gate.
Medido em 20/09/2026: uma tarefa complexa aceita na terceira devolução custou duas devoluções ao
mesmo worker e nenhuma rodada de revisor.

**Gate** é uma cartada: um revisor read-only, em outro modelo, **uma vez**, sobre o candidato
integrado, imediatamente antes do passo irreversível que ele guarda (migration em produção,
deploy, publicação). Devolve PASSA ou BLOQUEIA, com a lista de achados provados. Decidido pelo
usuário em 12/09/2026 e reafirmado em 22/09/2026.

    ondas -> aceite por tarefa -> gate (uma vez) -> PASSA:    passo do coordenador
                                                 -> BLOQUEIA: correções com teste -> aceite -> suíte verde: passo do coordenador
                                                                                                    -> falhou: systematic-debugging -> teste

- **PASSA:** rode o passo do coordenador.
- **BLOQUEIA:** cada achado aceito vira correção com dono e com o teste que fica vermelho ao
  neutralizar; você confere cada achado antes de despachar e aceita cada correção com casos seus;
  suíte verde por nome: rode o passo do coordenador. **O gate não roda de novo.** Corrigir o que
  o gate listou nunca reabre o gate, e o revisor não é chamado para conferir a própria lista.
- **Teste falhou é investigação, não revisão.** Suíte ou E2E reprovando depois das correções entra
  em `systematic-debugging`: causa raiz, um conserto, teste de novo. Três consertos falhados no
  mesmo teste viram questão de arquitetura, como aquela skill já manda.

Segunda rodada existe em dois casos só, e você escreve qual em uma linha no documento do ciclo:

1. **O usuário pediu.**
2. **Entrou superfície que o gate não viu:** tarefa nova, módulo novo, contrato alterado depois
   do veredito. A rodada é sobre esse delta, com o diff do delta no brief, não sobre o candidato
   inteiro.

Quantos gates: **um por plano**, antes do primeiro passo irreversível, sobre tudo que foi
integrado até ali. Um segundo só quando existe um segundo passo irreversível com superfície
própria (uma publicação de frontend separada do deploy de backend, por exemplo). Nunca um por
onda: quem guarda a onda é o aceite do coordenador. Plano de escala parcial ou mínima não tem
gate; aceite mais suíte.

Medido em 20 e 21/09/2026, três planos no mesmo repositório: quatro ondas com um gate por onda
rodaram **cinco** gates (um deles repetido "sobre o delta") e nove tarefas de correção; doze
tarefas com três gates planejados rodaram dois deles, uma vez cada, e o terceiro nem rodou
porque a tarefa que ele guardava foi cancelada; seis tarefas com **um gate, uma rodada** acharam
quatro críticos, corrigiram com teste, e publicaram na mesma noite. Nos dois últimos, ninguém
chamou o revisor de novo depois da correção, e nada disso voltou como defeito. Antes disso,
12/09 (três gates, nove rodadas) e 14/09 (sete rodadas, quem parou foi o usuário). O gate acha
muito na primeira rodada e cada vez menos nas seguintes; o que não converge é o laço, não a
revisão.

Nunca rode o passo irreversível "enquanto o gate roda". O ganho é minutos; a perda é migration
aplicada em produção sem `git revert`, ou deploy que republica módulo compartilhado de uma branch
atrasada. Revisão que volta com achados **não autoriza você a corrigir por conta própria**:
sintetize, decida quem é o dono da correção, e despache. Decisão de negócio vai ao usuário, com
resumo e recomendação.

O que protege o passo irreversível nesse desenho é a forma da correção: estrutural, num ponto de
estrangulamento, com o teste que trava o defeito. Remendo por call site sem teste era o que fazia
o gate ser chamado de novo. Como despachar essa correção: seção seguinte.

## Como despachar a correção pós-gate

Uma linha por lição. O caso que pagou cada uma, com a medição, está em
`references/correcao-pos-gate.md`; leia antes de escrever o primeiro brief de correção.

- **Mesma família de achado em arquivos diferentes:** proíba o remendo por call site e exija um
  ponto de estrangulamento. Sintoma: você escreve "e este caminho também precisa propagar X" pela
  terceira vez.
- **Contraexemplos no brief são piso, não teto:** o worker entrega a vizinhança adversarial dele
  e os testes dela, e a sua verificação usa casos que não são os dele.
- **O revisor acusou o INSTRUMENTO** (o teste não consegue observar a classe do defeito): a onda
  seguinte é arreio, do coordenador, não correção. Arreio executa o artefato de produção e é
  provado por neutralização antes de ser usado.
- **Teste negativo sem controle positivo não prova nada.**
- **Contrato "exatamente um de A ou B" com todo teste passando A e B:** a cardinalidade não está
  testada.
- **Mudou enum, campo de contrato ou estado:** o entregável inclui o inventário dos consumidores
  por `grep`, com decisão por consumidor; rótulo novo não muda comportamento.
- **Requisito de FORMA marcado bloqueante** (avaliar uma vez, persistir antes de enviar) vem com
  o teste que fica vermelho quando ele é desfeito.
- **Toda afirmação sua no documento do ciclo sobre entrega alheia** carrega o comando que a
  provou; sem ele é `[SUPOSTO:]`.
- **Se o usuário pediu rodadas extras:** na terceira reprovação da mesma família, pare e leve
  decisão de ship (residuais com dono, prova fora do gate, custo da próxima rodada).

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
3. **Você vai levar uma decisão ao usuário e precisa montar as opções**: a questão de
   arquitetura depois de três consertos falhados no mesmo teste (`systematic-debugging`), ou a
   decisão de ship com residuais. O advisor ajuda a escrever as opções; quem decide é o usuário.

O que NÃO é advisor, mesmo quando parece decisão importante:

- redigir brief, escolher worker, responder `question` de worker;
- o que uma regra desta skill já decide (ownership, gate antes do irreversível, modelo por nível);
- decisão de negócio: vai ao usuário, com resumo e recomendação, sem passar pelo advisor;
- **confirmar o que você já decidiu.** Consulta cuja resposta você já sabe qual quer é
  deferência ao contrário, e gasta o orçamento de quem precisaria dele.

### Orçamento: uma consulta por veredito, e o contador é o `task-list`

- **Uma consulta por veredito de gate**, no máximo: a que decide por onde vai a correção. Com um
  gate por plano (seção *Dois mecanismos de qualidade*), isso costuma ser uma consulta no ciclo
  inteiro.
- **Uma por escalação que contradiz contrato congelado ou afirmação de carga** (gatilho 2), e uma
  para montar as opções de uma decisão que vai ao usuário (gatilho 3). Não existe segunda consulta
  sobre o mesmo veredito ou a mesma escalação: se a primeira não decidiu, o que falta é direção
  sua no brief, não outro advisor.
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
- Se o harness do coordenador tiver um advisor próprio (a ferramenta `advisor` do Claude Code,
  que lê a conversa inteira), ele é opinião extra e gratuita: **não substitui a task `ADV-n`**
  quando um gatilho dispara, e não conta no orçamento, porque o modelo dele não é o que o
  usuário escolheu. O que ele disser sobre uma decisão de rumo entra no mesmo registro, com a
  mesma exigência de divergência visível. Foi um advisor de harness que apontou aquela falha de idempotência.

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
2. **Mova plano e spec para "em validação"**, no mesmo commit do fecho. Se o projeto guarda
   planos em pastas por estado (a fazer / em validação / feito, ou o nome que o `CLAUDE.md` /
   `AGENTS.md` der), a execução termina tirando os dois de "a fazer" e pondo em "em validação".
   Reescreva toda referência ao caminho antigo: índices, outros planos, skills, scripts e
   comentário de código. Link relativo de dentro da pasta movida muda de profundidade junto.
   **Nunca mova para "feito" no fecho.** Feito exige a prova que o plano prometeu (medição em
   produção, teste pago, aceite do usuário), e ela quase sempre chega depois da execução; quem
   obtém a prova é quem move para "feito". No índice de planos, diga qual prova falta e quando
   ela cabe. Se o projeto não tem pastas de estado, pergunte uma vez se quer adotá-las; sem
   resposta, siga a convenção que existe.
3. Commite com caminhos explícitos.
4. Responda os portões de entrega do projeto, sem esperar o usuário perguntar. Se o projeto entrega por bundle ou build nativo, diga sim ou não para cada um.
5. Atualize a documentação que este projeto exige atualizar no mesmo commit.
6. Feche as tasks no Orca com o resultado real, e os terminais: `wave.sh sweep` tem de responder que não há terminal de task encerrada aberto, e o único terminal seu na árvore é o do coordenador. Task que fica aberta some do radar e reaparece como confusão na próxima sessão.
7. Confira que toda task `ADV-n` tem o bloco de registro (recomendou / decidi / divergência) no documento do ciclo, e que cada divergência está no relatório ao usuário com essas palavras.
8. Relate ao usuário o que ficou de fora, se ficou, e por quê.
9. Uma linha por skill do ciclo (`spec-interview`, `power-plans`, esta): o que entra, em qual
   arquivo, ou *"nada entra, porque X"*. Lição que fica só no relatório de revisão é lição que a
   próxima spec paga de novo. O que entrar segue a seção *Documentação viva*, no fim desta skill.

Se alguma armadilha nova aparecer durante a execução, acrescente-a a `references/orca-traps.md` no mesmo trabalho, pelas regras da seção *Documentação viva*. É a única forma de a próxima execução não pagar de novo.

### Prova ponta a ponta: o vermelho é na versão ANTIGA integrada

Neutralizar o fix no teste unitário prova a peça; não prova o fluxo. Quando o projeto tem
ambiente de homologação e cenário ponta a ponta, rode cada cenário do ciclo **duas vezes**: com a
versão anterior publicada lá (tem de falhar pela asserção do defeito, com a causa conferida) e
com o candidato (tem de passar). Só então publique em produção.

- O fluxo integrado acha o que a suíte não acha: um **segundo componente** que desfaz o fix
  depois dele, um teste unitário que **semeou** o estado que o fluxo real nunca produz, um
  caminho de dado que o teste isolado não percorre. Medido em 25/09/2026: quatro defeitos assim,
  todos com a suíte verde e o gate aprovado.
- Cenário que **não falha na versão antiga** não prova o fix. Refaça-o para exercitar o caminho
  do defeito; se o defeito depende de uma escolha do modelo que não se reproduz sob demanda,
  registre o cenário como regressão e diga que a prova é o teste unitário. Nunca o conte como
  vermelho/verde. No mesmo ciclo, 6 cenários não separavam as duas versões e foram refeitos, e
  outros 7 ficaram como regressão, com isso escrito no relatório.
- Cenário antigo que falha com o candidato por **exigir o comportamento que o ciclo removeu** é
  contrato velho: reescreva e renomeie (e registre por quê), nunca o apague nem o ignore.

### Medir com flag diferente da do gate é medir outra coisa

Mesmo ciclo. Rodei a suíte completa com `--allow-net` (herdado de um probe que eu mesmo tinha
escrito) e colhi **11 falhas em vez de 4**. As 8 extras eram todas de um teste que exige
**AUSÊNCIA** de permissão de rede, para provar que nenhum fetch cru escapa por um catch. Passei
alguns minutos tratando um run inválido como regressão.

**A regra:** antes da medição que decide alguma coisa, **leia o comando exato que o gate roda**
e use ele. Não o comando que você lembra, não o do documento: o do script.

```bash
grep -n "deno test\|npm test\|pytest" scripts/<script-de-deploy>.sh
```

E confira também **qual suíte** o gate roda. Nesse mesmo ciclo, o gate do deploy rodava só
o diretório de uma função, não a árvore inteira — e as 4 falhas pré-existentes viviam
**fora** dela. Eu tinha pedido ao usuário autorização para liberar a suíte vermelha com quatro nomes que,
medido, **não era necessário**. Saber o recorte do gate antes teria poupado a pergunta.

### Medir nas dependências do checkout compartilhado é medir outra coisa

Medido em 24/09/2026, no frontend. A suíte completa no checkout deu
**49 falhas** contra 6 da base, 42 delas "Test timed out in 5000ms" em arquivos que o ciclo não
tocou; isolados, os mesmos arquivos continuavam falhando. Parecia regressão. Não era: o
`node_modules` do checkout compartilhado estava **fora do lock** (Radix e vitest mais novos, com
`package.json` e lock intactos: alguma sessão rodou `install` sem respeitar o lock), e a base
tinha sido medida num `git archive` com `npm ci`. Duas medições em ambientes diferentes, uma
falsa regressão.

**A regra:** a medição que decide (a do aceite da onda e a do fecho) roda onde o deploy
instala, não onde você edita. No frontend, isso é uma cópia `git archive` com a instalação
pelo lock (`npm ci`), recebendo os arquivos do candidato por `rsync --files-from`; a base e o
candidato no MESMO ambiente. Antes de chamar de regressão uma falha em arquivo que o ciclo não
tocou, rode esse arquivo na base e no candidato lado a lado. E não "conserte" o `node_modules`
compartilhado sem pedir: outras sessões estão usando.

### Teste congelado tem de sobreviver à tarefa que vem depois

Mesmo ciclo. O plano congelava um teste de caracterização (o hook de hoje, antes da extração):
depois do aceite, ninguém edita. O teste esperava a carga com **30 microtarefas fixas**, e a
tarefa seguinte ia acrescentar buscas encadeadas ao hook, ou seja, ia quebrá-lo sem mudar
nenhum número. O coordenador percebeu na leitura do aceite e aumentou a margem ANTES de
congelar (e registrou a edição); depois de congelado, a única saída seria a tarefa seguinte
editar o teste que existia para vigiá-la.

**A regra:** no aceite de um teste que vai ser congelado, leia-o contra o que a PRÓXIMA tarefa
vai mudar: mock que responde por tabela e aplica os filtros (não por ordem de chamada), tabela
desconhecida devolvendo vazio, espera por condição ou com folga larga (não por contagem justa
de ticks), e asserção de rota só no que tem de sobreviver. O que precisar mudar muda antes do
congelamento, com o hash registrado.

### Lista de deploy calculada por UM método é hipótese

Mesmo ciclo. Escrevi um script para gerar o fecho transitivo dos importadores de um arquivo
`_shared/` alterado (o `grep` que o plano sugeria devolvia 70 de 70 funções, inútil). Ele deu
**12**. O gate adversarial, calculando por conta própria, deu **13**.

Quem estava errado era o meu script: ele reconhecia `from "./x.ts"` e `import "../y.ts"`, mas
**não** `import("../z.ts")` dinâmico. A função que sumia alcançava o arquivo alterado por uma
cadeia de sete saltos terminando num import dinâmico. Deployar sem ela deixaria uma cópia velha
do `_shared/` embutida em produção, silenciosamente.

**A regra:** quando o brief do gate pede uma lista fechada (funções a deployar, arquivos a
tocar, chamadores a atualizar), peça-a **recalculada de forma independente** e escreva no brief
que **as duas têm de bater**. Divergência não é discordância de opinião: é um dos dois métodos
com ponto cego, e vale mais que a revisão de código que veio junto.

## Documentação viva

Esta skill melhora com o uso, e melhorá-la faz parte da implementação quando o ciclo mostrou um
furo **dela**: a armadilha que a execução pagou na marra, o passo que o laço de ondas não
previa, a regra que um worker ou o gate desrespeitou porque ela estava ambígua aqui. É opcional, e só vale quando o furo custou e vai custar de novo.

- **Melhore antes de acrescentar.** Procure a seção que já cobre o assunto e aperte-a; linha nova
  só se nada cobre. Esta skill não cresce indefinidamente.
- **Conceito, não caso.** Antes de escrever, leia o `AGENTS.md` da raiz do plugin: nada de nome de
  tabela, cliente, ciclo ou caminho do projeto onde a lição foi paga.
- **Escreva no clone git de onde a skill foi carregada** (a pasta deste arquivo). Se ela não é
  repositório git (cópia de cache de instalação), não edite: deixe o texto proposto no relatório.
- **Não commite nem dê push.** Avise o usuário no relatório final, como follow-up: arquivo, seção
  e uma linha do porquê. Quem confere e commita é ele.
