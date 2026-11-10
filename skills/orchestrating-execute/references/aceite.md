# Laço de ondas e aceite de cada entrega

Referência da skill `orchestrating-execute`. Leia ao abrir uma onda e a cada entrega de worker. Contém a regra de tela: comparação lado a lado com a referência aprovada.

## O laço de ondas

**Espera longa é visível.** Ao armar uma espera que pode passar de 15 minutos, diga ao usuário em
uma linha o que você espera, de quem, e quando olha de novo. Enquanto espera, adiante o que não
depende dela: a próxima etapa que pode rodar em paralelo, um aceite pendente, o registro do
ciclo. Medido em 11/2026, em três execuções: o usuário cobrou o coordenador por estar parado; em
uma delas, 336 de 390 minutos de silêncio eram espera legítima de worker que ninguém via, e em
outra havia de fato uma etapa paralela que não tinha sido começada.

Para cada onda:

1. Suba **no mesmo momento** todos os workers da onda cujas dependências já foram aceitas, pelo
   caminho que dá posse do terminal (`wave.sh spawn`, que é `worker-start`). Onda serializada é
   onda desperdiçada, e terminal sem dono registrado é terminal que ninguém consegue fechar com prova.
2. Espere as conclusões. Trate `escalation` na hora: worker escalando está parado.
3. **A cada `worker_done`, feche o ciclo daquele worker sem esperar que o usuário peça:** leia o
   relatório, aceite com casos seus, confira a task, feche o terminal. A sequência exata está na
   seção seguinte. Logo depois do aceite, suba as tarefas que ele destravou; elas não esperam o
   resto da onda.
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
   No diff dos testes, confira também os caminhos de arquivo que eles leem: caminho ignorado
   (`git check-ignore` responde) ou fora do repositório é devolução, porque só existe nesta árvore.
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

### Entrega de front com protótipo aprovado: comparação lado a lado, sempre

Se a spec ou o plano cita um protótipo aprovado pelo usuário (artefato, Figma, HTML, pranchas),
**toda** tarefa que entrega tela só é aceita com a comparação lado a lado contra ele. Não é
opcional, não depende de o plano repetir a exigência e não se troca por "revisei os screenshots".

1. **Uma linha por estado de cada prancha que a tarefa toca:** a captura da implementação ao lado
   da prancha aprovada, no mesmo estado (carregando, vazio, erro, resultado; computador e
   celular). Interação e animação também entram: clique, seleção, progresso, transição e o que
   aparece depois do clique. Para o que se mexe, grave (vídeo ou GIF) ou capture a sequência de
   quadros, nos dois lados.
2. **Confira composição, não só defeito:** layout e onde a tela vive (dentro do app ou fora),
   navegação e destaque do item atual, imagens e exemplos que a prancha mostra, ordem e textos.
   Revisar captura procurando bug (plural, transbordo) não é comparar com o protótipo: os dois
   passam juntos e a tela sai diferente.
3. **Diferença é devolução.** Cada divergência vira correção (`T<n>b`) ou adaptação aceita pelo
   usuário por escrito, registrada no documento do ciclo com o motivo. Divergência que só você
   aceitou é desvio do protótipo, não adaptação.
4. **Guarde as comparações num arquivo por tarefa**, na pasta do plano (`comparacao-T<n>.md`:
   para cada estado, o caminho da captura, a prancha e a versão do protótipo, e a lista de
   divergências com o destino de cada uma), e mande ao usuário na entrega. Sem ele, a tarefa de
   front não está aceita.
5. **O arquivo é a trava da integração.** O passo que integra ou publica o front começa
   listando os arquivos de comparação das tarefas de tela; faltou um, o passo não roda. Uma
   aprovação do usuário sobre outra coisa (as artes, o backend, "pode integrar o seu trabalho")
   não substitui a comparação: diga que a tela ainda não foi comparada e faça antes de integrar.
   Regra em prosa já existia no plano quando o caso abaixo aconteceu; o que faltava era a trava.

O brief do worker de front leva o caminho das pranchas e esta exigência no `Pronto quando`; quem
roda e julga a comparação final é você, no aceite.

Medido em 09/11/2026: o plano mandava comparar com o protótipo, o aceite só revisou capturas
procurando defeito, e a área foi para produção fora do layout do app, com abas sem destaque,
itens de uma lista sem as imagens da prancha, opções de escolha sem o exemplo visual e um
progresso diferente do aprovado. O usuário reprovou a UI inteira, e o redesign custou um ciclo
novo.
