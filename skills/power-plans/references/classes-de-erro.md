# Classes de erro que já custaram caro, e as duas lições de prova ponta a ponta

Referência da skill `power-plans` (Fase 0.5). Texto movido sem reescrita do `SKILL.md`, onde ficou
um checklist de uma linha por classe. Leia a classe inteira quando ela se aplicar ao plano que você
está escrevendo: é aqui que estão o mecanismo e a medição que a sustentam.

Referências internas: "afirmação de carga" e "etiqueta de procedência" são as seções *A carga do
plano* e *Etiqueta de procedência* do `SKILL.md`.

### As classes que morderam de verdade — confira estas por nome

1. **Semântica de coluna, flag ou campo. NUNCA infira pelo nome.** `created_at` de uma tabela
   de auditoria parece "quando aconteceu" e significa "quando fechou". Abra a linha e compare
   com um caso conhecido. Um projeto medido tinha uma família inteira de bugs assim
   (um booleano cujo nome descreve o que o cliente **disse**, lido como "o que o estágio
   **entregou**"). O plano de 26/08 reproduziu, na
   camada de planejamento, exatamente o defeito que ele fora escrito para corrigir.

   A verificação inteira é **uma query**, e ela devolve o veredito sem interpretação:

   ```sql
   select a.created_at, a.processing_time_ms,
          a.created_at - (a.processing_time_ms||' ms')::interval as turno_comecou,
          (select max(m.created_at) from messages m
             where m.conversation_id = a.conversation_id
               and m.direction = 'inbound' and m.created_at < a.created_at) as ultimo_inbound
   from ai_audit_logs a
   where a.conversation_id = '<a conversa do caso>' order by a.created_at;
   ```

   Resultado real do turno auditado: `created_at 22:58:15.38`, `processing_time_ms 14493`,
   `turno_comecou 22:58:00.888`, e o inbound engolido em `22:58:02.586`. Ou seja: o inbound é
   **posterior ao início** do turno (logo invisível ao motor, e recuperável) mas **anterior ao
   `created_at`** por 13,0 s — cortar no `created_at` o classificaria como "já visto" e o fix
   não faria nada. Nos seis turnos da conversa o atraso variou de 6,5 s a 36,3 s, e dois vieram
   com `processing_time_ms = 0`, caso de borda que sozinho já obriga a exigir que a linha de
   auditoria **emoldure** o outbound.

2. **O fix é no-op?** Antes de escrever a tarefa, pergunte: com o código de hoje, esta
   mudança altera alguma coisa? Um corte que já exclui o alvo, um guard que já não dispara,
   um campo que já vem preenchido. **No-op passa verde** — é a pior falha possível, porque
   produz teste, relatório e commit sem produzir efeito.
3. **O caso prometido realmente dispara o critério novo?** Se o plano diz "o registro X vai
   aparecer na flag Y", rode os critérios de Y contra X **agora**. Foi assim que o registro
   entrou num item de gate que ele não satisfazia.
4. **Caminho, comando e nome existem?** `ls` no script, `--help` no subcomando, `\d` na
   tabela. Custa segundos e aparece no passo do coordenador, que é onde ninguém testa antes.
   **Arquivo NOVO não tem `ls`:** o caminho dele cita o irmão existente do mesmo tipo e a
   configuração que o descobre (diretório de testes, `include`, glob), os dois com `[LIDO:]`.
   Caminho novo deduzido de uma norma escrita é `[SUPOSTO]`. Medido em 2026-09-12: o plano
   pôs o teste ponta a ponta novo no diretório de artefatos que a documentação do projeto
   mandava usar, fora do diretório de testes do runner; o runner listaria zero testes e a
   tarefa entregaria um arquivo que nunca roda. Havia dezenas de irmãos no diretório certo.
   **E saída de `--help` cortada não prova ausência:** `| head -N` trunca a lista, e o cabeçalho
   que você usa para recortar pode não existir naquela versão. Rode o `--help` inteiro ou `grep`
   pelo nome do subcomando. Medido em 2026-09-21: concluir "esse comando não existe" a partir de
   um recorte fez o plano proibir, no brief de TODAS as tarefas, uma capacidade que o executor
   tinha — e o coordenador passou a executá-la à mão por ele, 13 vezes.

5. **Invariante que você promete PRESERVAR.** "A mudança mantém a garantia G" é afirmação
   de carga (ver *A carga do plano*, no `SKILL.md`). O comentário do código **não é** evidência de G: comentário envelhece,
   e a contradição entre o comentário e o código é justamente onde o bug mora. Evidência de G é
   o caminho de exceção que você procurou e não achou, mais o teste que hoje trava G.
6. **Emissores de um comportamento que você vai REMOVER.** Quando a tarefa é "a partir de
   agora o sistema não pergunta mais X", a pergunta não é "onde está o X que eu achei", é
   **"quantos lugares conseguem emitir X?"**. Enumere todos antes de dimensionar a tarefa, e
   procure de duas formas, porque elas acham coisas diferentes: pelos **chamadores** da função
   canônica, e pelo **literal do texto** emitido. Emissor que escreve a frase inline não
   aparece na busca por chamador, e é o que sobrevive ao fix. Medido no mesmo ciclo: o plano
   mapeou 1 emissor, existiam 5, e 2 dos que faltavam eram literais escritos dentro de um
   guard. Um teste por emissor, não um teste da função canônica.
   **Emissor que mora em DADO não aparece em nenhuma das duas buscas.** Texto de instrução,
   template, configuração ou seed guardado no banco (ou num snapshot dele) manda fazer o
   comportamento que o código deixou de fazer, e o `grep` no repositório devolve zero. A terceira
   busca é uma consulta pelo literal nas tabelas de template e configuração, e a tarefa que
   remove o comportamento é dona também da mudança nesses dados (migração, não edição à mão).
   Medido em 25/09/2026: a revisão externa achou instruções guardadas no banco mandando executar
   exatamente a ação que o plano removia; custou uma tarefa de migração que o plano não tinha.
   **Validação, filtro ou gate novo sobre uma saída que já existe É remoção**, mesmo que a
   spec o descreva como garantia nova. A medição é no histórico persistido: quanto da saída
   de hoje o gate rejeitaria, em uma consulta. Medido em 2026-09-12: um contrato do plano
   proibia número fora de fatos autorizados num campo de texto livre; os prompts em produção
   mandavam citar números, e 153 de 209 respostas do mês tinham dígito. Nenhum documento
   tinha olhado a saída atual, e duas tarefas paralelas teriam implementado contratos
   incompatíveis.
7. **Receita copiada de outro contexto.** Reaproveitar um procedimento documentado é certo, e
   ele vem com pré-condições que ninguém reescreve junto. Antes de colar, escreva o que a
   receita **assumia** e confirme que vale aqui. Medido: um `update ... set stage_id = null`
   copiado de uma receita onde os estágios eram **apagados**, aplicado a um caso onde eles
   apenas ficavam inativos. Na receita original o nulo era obrigatório; no caso novo travava o
   fluxo.
8. **Passo novo dentro de pipeline existente.** Escolher a posição pelo nome da abstração
   ("é um guard, vai na cadeia de guards") é como o passo entra cedo demais ou tarde demais.
   **Leia do seu ponto de inserção até o fim do fluxo** e liste tudo que ainda pode mutar o que
   você produziu, ou produzir o estado que você observa. Medido: um passo de fechamento
   colocado "no fim da cadeia" não via as transferências criadas depois dela, e era
   sobrescrito por uma reescrita posterior.
9. **Tarefa que ADIA, SEGURA ou BLOQUEIA uma ação que já existe.** Antes de escrevê-la, ache o
   **ponto único onde a ação acontece, ANTES dos efeitos colaterais**. Se os efeitos já
   ocorreram quando o seu código consegue observar a ação, você não está adiando nada: está
   mentindo para o usuário final e deixando o sistema em estado inconsistente. Se esse ponto
   único não existe, a tarefa não é uma feature, é uma máquina de estado nova. Diga isso e
   corte, ou promova a frente própria.
   **Ação com vários executores:** quando a mesma ação sai de mais de um caminho (o decisor
   principal, um timeout, uma rede de segurança, um portão anterior), a enumeração da classe 6
   vale para ela. Escreva a matriz "caminho → lê a trava? → dono → teste", e cada caminho lê a
   MESMA trava com o MESMO input (classe 12). Um caminho que recebe menos contexto que os outros
   decide diferente com o mesmo nome de função. Medido em 26/09/2026: o plano pôs a trava no
   decisor principal e no portão que roda antes dele; a revisão externa achou mais dois caminhos
   que executavam a mesma ação sem ler a trava (o timeout do estágio e a rede de segurança
   pós-modelo), e o portão recebia só a última mensagem enquanto o decisor lia o turno inteiro.

10. **Tarefa que SUBSTITUI um módulo por outro (receita própria no lugar da compartilhada).**
    A ordem de resolução do alvo não é o inventário do módulo. O módulo substituído tem
    **gatilhos** (quando ele age sem ninguém pedir), e cada um é um item da matriz de
    consumidores, com decisão escrita: "mantido", "removido porque X", "coberto por Y".
    Medido em 2026-09-01/02, num ciclo que isolava uma vertical de negócio nova: o plano do
    pré-LLM próprio da vertical listou a ordem do alvo (vínculo → opção ativa → texto) e os
    gatilhos de pedido de foto e de nome no texto, e omitiu o gatilho "interesse já vinculado"
    do módulo da vertical antiga que estava sendo substituído (contato já vinculado + zero opção
    → apresentar). Um gate adversarial, sete tarefas, suíte
    verde por nome e três cenários novos pagos passaram; quem achou foi o cenário de REGRESSÃO
    da vertical, que reprovou no turno 3 porque uma flag de entrega só era gravada por um
    caminho que a mudança tornara raro. A lista
    de gatilhos custa um `grep` por `reason:` no módulo antigo; a omissão custou um run pago,
    uma onda de correção e um redeploy.

11. **Tarefa que INSERE uma peça nova dentro de tela, página ou módulo que já existe.** A matriz
    de consumidores registra o ponto de inserção ("`X.tsx` — novo consumidor: uma linha") e isso
    *parece* resolver o item. Não resolve: **o que você insere herda o estado do hospedeiro**, com
    os defeitos dele junto. Antes de dimensionar a tarefa, leia o que o hospedeiro já faz com os
    valores que a sua peça vai consumir — a data, o fuso, o usuário, o filtro, a unidade.
    Medido em 2026-09-03: a spec descrevia a virada de meia-noite **corretamente** (*"a data é
    resolvida a cada consulta pelo fuso do aparelho"*), e a tela hospedeira fixava a data no
    `mount` desde muito antes da branch. O card novo nasceu certo e herdou o defeito: com o app
    aberto na virada, o registro ia para o dia anterior. Nenhum FR falhou, nenhum contrato foi
    violado — o hospedeiro é que não tinha sido lido. Custa um `git show <merge-base>:<arquivo>`.

12. **"Importar a mesma função" não é paridade quando a ENTRADA mora no chamador.** Reaproveitar
    o predicado puro do motor num consumidor externo parece eliminar a duplicação; se a seleção,
    o filtro ou o enriquecimento do dado acontecem antes de a função ser chamada, o consumidor
    reproduz o veredito só se reproduzir também a entrada. Medido em 2026-09-04: o plano mandava
    o coletor da auditoria diária importar a função de avaliação do motor; a revisão externa
    mostrou que o motor descarta as mensagens geradas pela IA, exclui notas internas e **enriquece
    as opções com preço do catálogo** antes de chamá-la, e reproduziu um
    veredito invertido só pela ausência do preço. Antes de prescrever "importe X", leia quem
    prepara o argumento de X e faça a preparação ser exportada junto.

13. **Teste do consumidor que fabrica o campo que o produtor real não emite.** Um fake que
    monta `{ sent: false, error: "..." }` e um worker que lê exatamente isso passam verdes
    enquanto o corpo HTTP real nunca carrega `error`. Medido em 2026-09-04: o corpo final da
    função tinha `sent` e não tinha `error`, e o early-exit não devolvia nem
    `sent`; o contrato do plano dependia dos dois. Regra: o teste do consumidor recebe a saída
    **do produtor real** (fixture gerada pelo teste do produtor), e o `Pronto quando` diz de onde
    ela vem. O contrato congela o shape produzido, não o shape desejado.

    **O produtor pode ser a rodada anterior do próprio sistema.** Um cenário de várias rodadas
    com estado persistido entre elas ("acima, sem leitura, acima → abre na terceira") testado no
    módulo puro, com a leitura de cada rodada injetada, nunca exercita o estado que a rodada 2
    grava e a rodada 3 relê. Medido em 2026-09-30: a regra de decisão passava o cenário no teste
    dela; de ponta a ponta ele falhava, porque a rodada sem leitura gravava o estado dos
    contadores como nulo e a seguinte perdia a taxa. O contrato congelado mandava gravar os
    contadores em bloco (tudo ou nada), o que desfazia o parse por campo feito para que uma
    métrica ausente não cegasse as outras. Nenhum aceite pegou; o gate pegou, com o contrato já
    congelado, e a correção reabriu o contrato. Três regras:
    - cenário de várias rodadas vai no `Pronto quando` da camada que grava e relê o estado, não
      só no do módulo puro;
    - estado composto de campos que falham sozinhos é guardado por campo, cada um com a própria
      hora; um bloco "tudo ou nada" propaga a falha de um para os outros;
    - valor carregado de uma rodada para outra mantém a hora em que foi **medido**, nunca a da
      rodada que o carregou: renovar a hora encurta o intervalo e infla a taxa (o dobro, numa
      rodada perdida), o que vira alarme falso.

14. **Remover um evento/linha de log exige procurar leitores por TEMPO, não só por chave.** O
    grep pela chave que só a linha "duplicada" carregava (`idempotent_skip_notify`) deu zero
    leitores, e a afirmação de carga "ninguém consome a segunda linha" passou. O consumidor real
    lia `order by triggered_at desc limit 1` — a **última** linha, qualquer que fosse
    (`evolution-webhook/index.ts:1005`, referência de abandono para reativar; reproduzido na
    fronteira das 24 h). Regra: para toda linha que o plano deixa de gravar, procure `order by
    … desc`, `limit 1`, `max(`, `last` e `lag(` sobre a tabela, além dos campos da linha.


15. **Plano que promete um ESCRITOR ÚNICO ("ponto de estrangulamento").** "A partir daqui toda
    escrita sai de um lugar só" é afirmação de carga, e ela se sustenta com a lista dos lugares
    que escrevem **hoje** — não com o lugar que você enxergou lendo o fluxo principal.
    Inventariar de verdade é listar os **sites de escrita** no alvo: todos os chamadores da
    função que você vai proteger, mais as rotinas que o próprio armazenamento executa sozinho
    (gatilhos, jobs, hooks). Conferir que os arquivos existem não é inventário.
    Medido em 2026-09-21: o plano reconheceu a família já na primeira rodada do gate e exigiu o
    ponto único — mas sobre o caminho visível. Existia um segundo escritor, um auxiliar privado
    que fazia a própria escrita e decidia a própria autorização, e ele só apareceu na rodada 2:
    custou uma rodada de gate mais uma onda inteira de correção. Se o inventário acusa N
    escritores, a tarefa nasce exigindo **um**; se você não consegue enumerá-los, o plano não
    pode prometer o ponto único, e dizer isso é mais barato que descobrir no gate.

16. **Linha nova em tabela de template, seed ou catálogo GLOBAL tem um consumidor que ninguém
    lista: o PROVISIONAMENTO.** "Só vale para o cliente X" é afirmação de carga quando a peça mora
    numa tabela que a rotina de criação de tenant copia inteira. Antes de pôr qualquer linha
    "global mas inerte", leia a função que cria tenant/conta/workspace e conte o que ela copia.
    Medido em 2026-09-23 (onboarding de um cliente de nicho): o plano punha o texto de uma etapa
    nova num template global "usado só onde a etapa existe"; a função de criação de workspace
    copiava **todo** template da vertical, e todo cliente criado depois ganharia a etapa. Achado
    pela revisão externa; custou uma decisão revogada e uma tarefa reescrita. No mesmo plano, a
    suposição "cabe mais uma posição na ordem" foi medida só em `pg_constraint` e passou:
    **unicidade pode morar num índice, não numa constraint** (`pg_indexes` mostrou UNIQUE em
    `(workspace_id, sort_order)`). Para qualquer "cabe" ou "é único", consulte os dois.

17. **Tarefa que cria ou muda um DETECTOR DE TEXTO** (regex, lista de palavras, classificador por
    padrão sobre o que uma pessoa escreveu). O autor testa as frases que imaginou; quem escreve de
    verdade nega, erra a digitação, conjuga em outro tempo, abrevia, acentua, e junta duas
    intenções na mesma frase. O detector passa em toda fixture e erra na primeira semana. Antes de
    congelar a tarefa, duas medições e uma lista:
    - **Falso positivo:** rode o detector novo contra uma amostra do texto real já persistido e
      leia o que ele passa a pegar que o antigo não pegava. É a consulta que diz se a mudança
      rouba casos de outra regra.
    - **Falso negativo:** as frases reais do defeito, e as vizinhas delas no histórico, entram na
      fixture de aceite, e não só a frase do relatório.
    - **A lista de variações vai no `Pronto quando`**, escrita, para o worker e para quem aceita:
      negação ("não quero X"), erro de digitação do termo-chave, outra flexão do verbo (presente,
      gerúndio, perífrase), pergunta × afirmação, termo-chave dentro de pedido educado, token curto
      ou ambíguo, e letra acentuada colada no termo. Esta última é mecânica: em várias linguagens
      o limite de palavra (`\b`) é ASCII, e a palavra acentuada vira fronteira no meio.
    Medido em 25/09/2026, num ciclo de 31 requisitos: **nove defeitos da mesma família**, achados
    em quatro momentos diferentes (revisão do plano, aceite do coordenador, gate, E2E), todos
    variações que nenhuma fixture tinha. Foi a maior causa de devolução ao worker do ciclo. Cada um
    custava uma consulta de amostra ou uma linha na lista de variações.

### Cenário de teste escrito e não executado é HIPÓTESE, não cobertura

Medido em 2026-08-27. Dois cenários E2E foram escritos junto
com o código, revisados como especificação, e **passaram por quatro rodadas de gate
adversarial sem nunca terem rodado**. Na primeira execução, os cinco runs pagos expuseram
**cinco defeitos** — e três deles estavam no próprio cenário ou no harness, não no motor:

- o cenário abria com uma frase que disparava um early-exit determinístico, então provava o
  early-exit e não o comportamento alvo;
- usava um número de telefone que o validador rejeita como lixo, e o turno falharia
  parecendo bug de código;
- o runner exigia um job agendado para provar que algo **não** acontece;
- o runner filtrava o atendente por um critério mais estrito que o da produção;
- e o motor tinha um defeito que só aparece na frase real: um ponto final no fim da frase
  matava a extração do número.

**A regra:** um plano não pode contar um cenário não executado como evidência. Ou o cenário
roda antes do gate, ou ele entra no plano com a etiqueta `[SUPOSTO:]` e o passo do
coordenador diz explicitamente "rodar ANTES de considerar coberto". Uma tabela de cenários
com a coluna "a executar" é uma lista de promessas.

**Corolário para o orçamento:** reserve execuções pagas para *descobrir*, não só para
*confirmar*. O ciclo gastou 9 execuções onde o plano previa 5, e as 4 extras foram as que
acharam os defeitos — o custo estava no lugar certo.

### Vermelho pelo motivo errado também não é cobertura

Medido em 2026-09-14: quatro dos sete cenários E2E novos
deram o primeiro vermelho pelo motivo ERRADO, e dois chegaram a dar verde sem
provar nada:

- a LLM **reparava** o defeito no mesmo turno (lia as duas mensagens no
  histórico e sobrescrevia a cidade fundida via tool) — verde no código velho;
- o abridor do cenário **invalidava o próprio fixture** (`"sobre isso?"` e
  `"ele"` sem contexto supersediam a atribuição do anúncio) — vermelho de
  setup, não de defeito;
- o turno anterior já entregava a foto, e o lock anti-spam segurava o reenvio
  mesmo com o fix — o sinal "foto enviada" não discriminava nada;
- fraseado da LLM variava (faixa vs mínimo, nome do empreendimento, paráfrase
  da promessa) e quebrava asserções que pinavam texto, não comportamento.

**A regra:** vermelho/verde de cenário E2E só conta com a CAUSA inspecionada.
No vermelho, abra o report e confirme que a falha é a asserção do defeito (tool
call, estado, sinal determinístico) — não derailment de setup, transferência
discricionária ou fraseado. No verde contra código velho, desconfie primeiro do
cenário, não comemore: confira se o caminho do defeito realmente engajou. E ao
escrever a asserção, prefira o sinal que nenhum agente discricionário pode
reescrever (efeito de guard, flag, tool sintética) ao texto da resposta ou ao
estado final que a LLM pode reparar.
