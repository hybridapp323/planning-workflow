# Despacho: mecânica, capacidade e brief

Referência da skill `orchestrating-execute`. Leia antes de escrever o primeiro brief e de despachar qualquer worker.

## Mecânica: use a skill `orchestration`

Não redocumente o Orca. Para criar run, criar task com dependência, despachar com preâmbulo injetado e esperar `worker_done` / `escalation` / `decision_gate`, siga a skill `orchestration`. Esta aqui só acrescenta o que é específico de executar um plano.

Sequência por worker, na ordem:

1. `run-create` uma vez, no começo. Sem run vinculada, `task-list` falha.
2. `task-create` para cada tarefa, com `--deps` refletindo o grafo do plano. O grafo vira estado, não fica só no documento.
3. `terminal create`, com o flag de bypass de permissão **e o `--model` e o esforço da tarefa** dentro da string de `--command`. Confira modelo e esforço no TUI antes do dispatch (ver *Portão de atribuição de modelo*).
4. `terminal wait --for tui-idle` antes de despachar. Terminal que ainda está subindo engole o dispatch.
5. `dispatch --inject` com o preâmbulo abaixo.
6. Arme a espera pela skill `orchestration`: `wave.sh wait 3600` numa chamada só dela, em background, e trate o retorno (`0` evento, `2` triagem, `4` nenhum worker trabalhando: despache agora). Não use `check --wait` cru: ele não lê o corpo antes de armar nem volta quando o evento já estava na caixa (incidente de 26/10/2026, documentado na skill `orchestration`).

Armadilhas medidas, que custam tempo quando descobertas na marra: `orca-traps.md`. Antes da primeira onda, leia o índice por sintoma e a lista *Leia sempre* (o começo do arquivo), não o arquivo inteiro; abra a seção quando o sintoma aparecer.

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

**Ferramenta que você entrega ao worker lê só o segredo de que precisa.** Um script de prova ou
wrapper que carrega o arquivo de segredos inteiro com o `source` do shell interpreta cada valor:
um `$` dentro de uma chave vira expansão de variável e, com `set -u`, o erro imprime o trecho da
chave no terminal. Esse terminal é o contexto do worker, e o contexto vai para o provedor do modelo
dele. Medido em 2026-09-30: o primeiro uso do wrapper expôs parte de uma chave de sandbox ao worker,
que escalou (corretamente) em vez de rodar de novo. Extraia a chave pelo nome com um parser (`sed`
na linha exata) e exporte só ela; teste o wrapper você mesmo antes do primeiro despacho.

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
- **Quem roda a verificação pesada, quando o Orca roda num servidor remoto.** Typecheck do projeto inteiro e suíte completa são do coordenador, uma por vez, no aceite (passo 2 de *O que fazer a cada `worker_done`*); o brief diz que o worker não as roda. Não é limite de workers: ver `references/orca-traps.md`, *Verificação pesada em N workers satura o host do Orca*.
- **Escalar em vez de improvisar.** Se a tarefa exigir sair do escopo, mudar contrato, ou tocar arquivo de outro, ele manda `escalation` e para. Um worker que improvisa custa mais que um worker que espera.
- **Pronto quando:** o critério da tarefa, **copiado do plano — que por sua vez copiou o cenário da spec**. Se o plano não tem esse critério, você não o escreve de cabeça: volte ao plano (ver *Preflight*). Coordenador improvisando critério de pronto é o defeito, não o conserto.
- **Quando a tarefa escreve teste ou cenário, o que o oráculo afirma.** O efeito que o requisito exige (o estado em que o sistema fica, o dado gravado, o que foi entregue), não o mecanismo que o produz hoje: qual função ou ferramenta foi chamada, por qual caminho, o texto literal de uma saída de modelo. O mecanismo só entra quando ele é o comportamento sob teste, e o brief diz isso. Se o projeto tem guia de escrita de cenário, o brief aponta o trecho; se o guia tem duas regras que puxam para lados opostos, o brief diz qual vale nesta tarefa. Medição em `power-plans`, `references/decompor.md`, *O oráculo afirma o efeito*.

Worker que recebe contrato por referência e não por valor inventa o contrato. Cole.

**Dado que um teste vai ler entra versionado, junto do código de teste, antes do despacho.**
Casos rotulados, amostras, fixtures que você gerou: numa pasta ignorada ou temporária, servem para
o worker ler, nunca para um teste carregar. Se um teste vai lê-los, versione-os como fixture antes
e passe o caminho versionado no brief. Nem pasta de documentos de planejamento: ela muda de lugar
quando o trabalho muda de estado, e pode ficar fora da cópia isolada em que a suíte se mede.

E a contraparte do portão acima: **proibição só se escreve depois de medida.** O que você não mediu entra como incerteza com um comando junto (*"não sei se há <capacidade> aqui; teste com `<comando>` e me diga o que voltou"*), nunca como um "você não tem isso".

### A prova de neutralização só pode tocar arquivo que o worker POSSUI

Peça sempre a prova de neutralização (neutralize o fix, confirme que o teste falha, restaure).
Ela é o que separa teste que trava o defeito de teste decorativo. Mas ela **muta o código de
produção por alguns minutos**, e é aí que mora a armadilha:

> **Se o alvo da neutralização não é um arquivo do worker, a prova é do COORDENADOR, numa cópia
> isolada — nunca do worker, nunca na árvore compartilhada.**

Medido em 2026-09-01. Um brief mandava "remova a chamada que mantém a tarefa de fundo viva e
confirme que a asserção falha" e, na mesma página, "não edite o arquivo de efeitos colaterais".
As duas instruções eram incompatíveis: uma extração anterior tinha **mudado aquela chamada de
arquivo**, e o brief foi escrito contra o mapa antigo. O worker fez o razoável, editou o arquivo
alheio, e **morreu no meio**.

O que ficou na árvore: produção sem a chamada, ou seja, o processo podendo morrer junto com a
resposta e engolir uma notificação. **E a suíte inteira passava verde**, porque
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
restauração, é intenção.** A contraparte disso na mecânica de terminais está em `orca-traps.md` (terminal que sobrevive
à liberação do worker), e a contraparte em dado é o cenário de teste que restaura o que desligou
sempre, inclusive quando falha.
