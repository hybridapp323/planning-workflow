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

Medido em 2026-09-03 (ciclo `contador-agua`): a spec tinha 13 FRs com cenário executável; o plano citava **6 deles zero vezes** e não tinha nenhum `Pronto quando`. O coordenador escreveu o critério de cada briefing de cabeça, e um campo que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing — dias de descanso ganharam 300 ml que não existiam, e o defeito só apareceu na revisão adversarial do fim. `plano=0` num FR é um requisito que nenhum worker vai ver.

Confirme também que a árvore está limpa do que interessa, e que você sabe quais arquivos modificados **não** são deste trabalho. Sessões paralelas deixam lixo, e ele acaba num commit errado.

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
Peça-a mesmo num plano sem gate previsto: o advisor pode ser chamado em qualquer plano, e sem a
linha o coordenador herda o modelo de Complexa e chama de gate.

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

### O brief que lista contraexemplos produz fixes do tamanho dos exemplos

Medido no ciclo `2026-09-14-auditoria-da23`: sete rodadas de gate, todas com
achados reais, e o arquivo `video-request-policy.ts` voltou em TODAS — janela,
números da janela, composição, recência, tópico com dois-pontos, quebra de
linha, só-emoji. Cada brief nomeava os contraexemplos exatos, cada worker
corrigiu exatamente eles (com testes que repetiam as mesmas formas), e o gate
seguinte achou a topologia vizinha. O mecanismo novo fechava os casos listados
e abria as bordas do próprio mecanismo.

**A regra, e ela vale para o brief que VOCÊ escreve, não só para o worker:**
contraexemplos no brief são o PISO, nunca o teto. Todo brief de correção traz,
como entregável explícito: (1) a vizinhança adversarial gerada PELO WORKER
(variações que o brief não listou, com o resultado antes/depois de cada uma);
(2) os testes commitados dessas variações, não só dos casos do brief; (3) a
proibição de ampliar lista lexical pela terceira vez seguida — na terceira, o
mecanismo tem de mudar (ponto de estrangulamento) ou o worker escala dizendo
por que o domínio não fecha por enumeração. E a verificação do coordenador usa
casos INDEPENDENTES (os seus, nunca só os do worker): aceitar correção
re-rodando os testes do worker é aceitar a forma que ele imaginou.

### Todo gate tem orçamento: a terceira reprovação da mesma família é decisão de ship

Medido no mesmo ciclo: as rodadas 5–7 continuaram achando defeito real, mas
cada vez mais exótico (anáfora parentética, rótulo só-emoji, `transferred` +
`deferred` simultâneos). O custo por rodada ficou constante e o risco residual
encolheu — e quem parou o loop foi o usuário, não o plano. Nenhuma skill dizia
quando parar.

Este ciclo rodou sete rodadas **contra** a regra *Um gate, uma rodada* (seção *Gates*,
decidida pelo usuário em 12/09/2026): pelo desenho vigente a rodada dois de um gate só
existe por pedido explícito dele. O que segue vale para esse caso, quando o usuário pediu
as rodadas extras, e para o laço `teste → systematic-debugging`, onde a "família" é o mesmo
teste voltando vermelho pela terceira vez.

**A regra:** na terceira reprovação da MESMA família, pare de despachar
correção e leve ao usuário uma decisão de ship, com três itens: o que falta
corrigir (arquivo:linha + cadeia de cada residual), o que prova cada residual
fora do gate (unitário determinístico? telemetria de produção? nada?), e o
custo da próxima rodada. Residual aceito vira watchlist com dono e
falsificador, não dívida silenciosa. "Reprovado pela sétima vez" sem essa
decisão é o coordenador trocando o julgamento do usuário por persistência.

### Quando o revisor acusa o MECANISMO do teste, pare de despachar correção

Medido em 2026-09-12, ciclo `cobrancas-asaas`. O gate reprovou duas vezes. Na
segunda ele não listou só achados: nomeou a causa comum, que não era nenhum
deles.

> "os testes não interpretam SQL de produção: extraem substrings, comparam
> posições, testam regexes e reimplementam pequenas decisões em TypeScript. Não
> executam PL/pgSQL, constraints, rollback, MVCC, RLS ou a cadeia RPC pública →
> helper. B1, B2, B3 e B5 permanecem verdes exatamente por essa limitação."

Isso é categoricamente diferente de "a mesma invariante vazou por outro emissor".
Ali o fix vai para um ponto de estrangulamento no código. **Aqui não existe fix
no código: o instrumento que julga o código não consegue observá-lo.** Uma
terceira rodada de correção produziria um quarto BLOQUEADO, com relatórios cada
vez mais convincentes sobre um verde que não significa nada.

**A regra:** quando a reprovação aponta o instrumento e não o objeto, a onda
seguinte não é de correção. É de **arreio**, e ela é do COORDENADOR, não de um
worker — porque o arreio define o que "pronto" passa a significar para todas as
tarefas seguintes.

Quatro coisas que o arreio precisa ter para valer a parada:

1. **Ele executa o artefato de produção**, não uma reimplementação dele. No caso
   medido: a migration aplicada de verdade num Postgres da mesma versão da
   produção (17.6), e os testes em pgTAP com `begin; … rollback;`.
2. **As dependências de ambiente são EXTRAÍDAS, não escritas.** As funções de
   identidade saíram de produção por `pg_get_functiondef`. Stub escrito à mão
   faria o teste de RLS provar a coisa errada, que é pior que não ter teste.
3. **Ele é provado por neutralização antes de ser usado.** Quebre o invariante
   numa CÓPIA, rode, confirme o vermelho. Arreio que nunca ficou vermelho é uma
   segunda camada de verde decorativo.
4. **Ele aceita apontar para uma cópia mutada** (aqui, `BILLING_MIGRATION=<path>`).
   Sem isso, todo worker vai neutralizar editando o arquivo de produção numa
   árvore compartilhada, e um worker que morrer no meio deixa o defeito lá.

E a decisão de escopo que economiza o dobro do tempo: **não persiga fidelidade
máxima se o barato cobre o que a tarefa toca.** A primeira tentativa foi subir a
stack local inteira; ela morre replicando 429 migrations, numa
`cron.alter_job(6, …)` cujo job id só existe em produção. O schema em revisão
dependia de cinco objetos externos. Meça a superfície de dependência ANTES de
escolher o caminho: `grep` das referências externas custa um minuto e decide
entre vinte minutos e a tarde inteira.

### Reprovação que o instrumento ACHOU não é a mesma que a que ele não viu

Medido em 2026-09-12, mesmo ciclo. Depois de trocar o mecanismo (acima), o gate
reprovou **de novo**. A leitura ingênua é "três rodadas, nada melhorou". Está
errada, e confundir as duas custa a decisão seguinte.

| rodada | por que reprovou | o que fazer |
|---|---|---|
| 1 e 2 | o teste **não conseguia ver** a classe inteira do defeito | trocar o mecanismo |
| 3 | o teste viu, e o revisor **achou** o que ele ainda não cobria | corrigir e ampliar a cobertura |

O sinal que separa as duas: na rodada 3 o revisor achou um defeito **executando**
(criou dois contratos e chamou a RPC com os ids trocados) e um segundo **mutando
o código e observando a suíte seguir verde**. Nenhum dos dois é possível quando o
teste lê texto. A reprovação mudou de natureza junto com o instrumento.

Diga isso ao usuário com essas palavras. "Bloqueado pela terceira vez" e
"bloqueado por um defeito que só apareceu porque agora sabemos olhar" levam a
decisões opostas sobre continuar ou parar.

**E o corolário de projeto, que é o achado mais caro deste ciclo:** mover uma
decisão de um lado da fronteira para o outro **cria uma fronteira nova**. Ali, o
cálculo saiu do SQL e foi para o domínio, que era a correção certa; o resultado
passou a viajar como `jsonb` do chamador para a RPC, e a RPC aplicava por id sem
provar que os ids eram dela. Resultado: mutação financeira **entre clientes**.

> Toda vez que um refactor faz um dado atravessar um processo, pergunte quem
> valida do outro lado. "O chamador monta certo" não é validação: é a suposição
> que a fronteira existe para não precisar fazer.

### Todo teste negativo precisa de controle positivo

Mesmo ciclo, medido na prática. Um teste que afirma "o vendedor do workspace
bloqueado não lê nada" fica verde quando a tabela não tem `GRANT`, quando não tem
policy nenhuma, e quando está simplesmente vazia — porque nos três casos **todo**
chamador lê zero, bloqueado ou não.

A prova é o par, sempre no mesmo arquivo:

- **positivo:** o ator SAUDÁVEL lê / escreve / consegue. Sem isto, o negativo não
  tem significado.
- **negativo:** o ator bloqueado não.

Isso vale muito além de RLS: fila que "não entrega", webhook que "não dispara",
guard que "não deixa passar". Se você não escreveu o caso em que a coisa
FUNCIONA, você não sabe se a que falhou foi bloqueada ou se nunca esteve viva.

### O teste que nomeia a mesma coisa duas vezes esconde a asserção que falta

Medido em 2026-09-12, e é o defeito mais sutil que este ciclo produziu, porque
sobreviveu a uma revisão adversarial que o aprovou explicitamente.

Um contrato dizia: *"`transferred` exige **exatamente um** `targetObligationId`
local **ou** `targetProviderPaymentId`"*. Uma rodada de correção endureceu
"valide o payment id" em "**sempre** exija o payment id", o que recusa um caminho
que o contrato permite. O revisor marcou aquele achado como fechado, com
neutralização que ficou vermelha.

Por que ninguém viu: **todos os testes daquele bloco passavam OS DOIS
identificadores**. Com os dois sempre presentes, a diferença entre "exatamente
um" e "sempre os dois" não produz nenhuma observação diferente. A asserção que
faltava era invisível por construção, não por descuido.

**O sinal para procurar, e ele é sintático:** quando o contrato diz *"exatamente
um de A ou B"*, *"um ou outro"*, *"ao menos um"*, e todo teste passa A **e** B, a
regra de cardinalidade **não está testada**. Vale igual para campos mutuamente
exclusivos, para "pelo menos um destes três", e para union types em que os testes
sempre constroem o mesmo membro.

O par que fecha isso é de três, não de dois:

1. **ambos** → recusado (dois jeitos de nomear a mesma coisa são duas chances de
   nomear coisas diferentes);
2. **nenhum** → recusado;
3. **cada um sozinho** → aceito. É o **controle positivo**, e é o que estava
   faltando: sem ele, "é recusado" fica satisfeito por um caminho que nunca
   funciona.

E a lição de revisão: **neutralização vermelha prova que o teste observa o que
ele afirma, não que ele afirma a coisa certa.** As duas perguntas são diferentes,
e a segunda se responde lendo o contrato ao lado do teste, não rodando a suíte.

### Documento de ciclo: toda afirmação precisa do comando que a produziu

Mesmo ciclo, medido quando dois workers derrubaram duas afirmações minhas no
documento de congelamento. Eu tinha escrito que uma tarefa tornara um parâmetro
obrigatório em três transportes, e que um varredor estava vermelho por ter achado
um vazamento real. Nenhuma das duas era verdade: o parâmetro entrou em dois dos
três, e o varredor estava vermelho por `NotFound` de caminho URL-encoded.

A causa não foi descuido de redação. Eu escrevi **o que a tarefa deveria ter
feito**, a partir do brief que eu mesmo redigi, em vez do que a árvore mostrava.
É o mesmo erro que a Fase 0.5 do `power-plans` existe para impedir, e as duas
afirmações mereciam `[SUPOSTO:]`, não `[MEDIDO:]`.

> No registro de um ciclo, toda frase sobre o estado do código carrega, implícita,
> a promessa de que alguém olhou. "O worker entregou X" é suposição até um `grep`
> dizer o contrário. Documento errado é pior que documento ausente: a próxima
> sessão confia nele e não tem motivo para conferir.

Barato de evitar: ao fechar uma onda, releia as suas próprias afirmações sobre
entregas alheias e rode o comando de cada uma. São segundos por linha, e foi o
que os workers acabaram fazendo por mim, gastando uma rodada de escalação.

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

## O advisor: segunda opinião de RUMO, com orçamento e rastro

Medido em dois ciclos seguidos. No `cobrancas-asaas` (12-13/09/2026) o advisor apontou a falha
de idempotência do CC-10 **na rodada 1**; o coordenador descartou o aviso, e o gate redescobriu o
mesmo defeito duas rodadas depois. No `auditoria-da23` (14/09) o coordenador decidiu sozinho,
a cada uma das sete rodadas, se a correção ia para o call site ou para o mecanismo, e o mesmo
arquivo voltou nas sete (seção *O brief que lista contraexemplos*, acima). Os dois têm o mesmo
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

### Orçamento: 1 por onda, 3 por plano, e o contador é o `task-list`

- **Onda** aqui é qualquer conjunto de tarefas despachadas juntas, inclusive a onda de correção
  pós-gate. Uma consulta por onda, no máximo.
- **Três por plano**, contadas do C0 ao fecho, correções e reparos incluídos. Não existe a
  quarta. Se um gatilho disparar com o orçamento zerado, a decisão vai ao usuário com as opções
  que você conseguir montar sozinho, e ter faltado é sinal de que o plano tem problema
  estrutural, não de que faltou advisor.
- **Cada consulta é uma task do Orca chamada `ADV-1`, `ADV-2`, `ADV-3`**, read-only, no run do
  ciclo. O `task-list` é o contador; ninguém conta de cabeça. Gate posterior do plano, se
  houver, confere no brief que há no máximo três.
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
rastro é o CC-10.

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
  mesma exigência de divergência visível. Foi um advisor de harness que apontou o CC-10.

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
6. Confira que toda task `ADV-n` tem o bloco de registro (recomendou / decidi / divergência) no documento do ciclo, e que cada divergência está no relatório ao usuário com essas palavras.
7. Relate ao usuário o que ficou de fora, se ficou, e por quê.
7. Uma linha por skill do ciclo (`spec-interview`, `power-plans`, esta): o que entra, em qual
   arquivo, ou *"nada entra, porque X"*. Lição que fica só no relatório de revisão é lição que a
   próxima spec paga de novo.

Se alguma armadilha nova aparecer durante a execução, acrescente-a a `references/orca-traps.md` no mesmo trabalho. É a única forma de a próxima execução não pagar de novo.
