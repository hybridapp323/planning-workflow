# Varredura de cobertura

Segundo teste de fechamento, antes de declarar a fronteira vazia.

A árvore de decisões acha a pergunta **dependente**: uma resposta abre galho, o galho vira
pergunta. Ela não acha a pergunta **ortogonal**, aquela a que nenhum galho levava, e que por
isso ninguém fez. O teste de fechamento ("liste o que você decidiu sozinho") também não: ele
é introspectivo, e introspecção não encontra o que você não pensou.

Esta lista é externa. Percorra-a inteira uma vez por spec arquitetural.

## Como usar

1. Para cada categoria, marque **Claro / Parcial / Ausente** para a feature em questão.
2. Todo **Parcial** ou **Ausente** vira uma de duas coisas, e nenhuma terceira: pergunta na
   próxima rodada, ou uma linha explícita na spec, *"não se aplica porque X"*.
3. A marcação é sua e não entra na spec. Entra o que ela produziu: a pergunta feita, ou a
   linha de "não se aplica".

Custa cinco minutos, e o "não se aplica" custa segundos. O que ela evita é uma categoria
inteira descoberta na fase de plano, onde a mesma pergunta já custa uma reescrita.

## As categorias

### Escopo funcional

- objetivo, e o critério de sucesso com número
- o que está explicitamente fora
- papéis: quem pode, quem não pode, o que muda por papel

### Domínio e dado

- entidades, atributos, relações
- **identidade e unicidade**: o que faz duas linhas serem "a mesma coisa"; a chave que o
  código usa é a chave certa? E do outro lado: se o destino de um vínculo é único, conte alvos
  distintos, não itens com par (40 itens com par único eram 35 alvos, 2026-10-29)
- **ciclo de vida**: estados, transições, quem transita, o que é terminal
- **semântica de cada campo lido ou escrito**: o nome diz uma coisa e a linha real diz
  outra? (um `created_at` que significa "quando fechou"; uma flag que descreve o que o
  usuário *disse*, lida como o que o sistema *entregou*)
- **campo derivado de mais de uma origem**: uma medição por origem, com a coluna-fonte de
  cada uma, e a regra de derivação escrita por origem em §8.2. Medido em 2026-09-12: o "modo
  da corrida" foi medido num provedor e deduzido no outro; no outro, 149 sessões em esteira
  chegavam com elevação zero e a regra literal as lia como rua plana.
- volume: quantos hoje, quantos em um ano, e o que muda quando é zero

### Interação

- jornadas principais, em ordem
- estados de erro, vazio, carregando, parcial
- acessibilidade, idioma, fuso horário (se há interface)
- **referência visual, sempre que há tela:** uma de três condições tem de valer e ficar
  escrita no §8.3. (1) Protótipo ou tela existente aprovado **e exercitado** pelo usuário, com
  arquivo e versão, os aspectos que governa (composição, conteúdo, movimento) e as adaptações
  permitidas; (2) decisões visuais fechadas na entrevista: onde a tela vive, navegação, o que
  aparece em cada estado, ações e destaque, textos; (3) referência dispensada pelo usuário,
  com a razão. Código existente não autoriza substituir em silêncio uma decisão nova
  aprovada. Medido em 11/2026, em dois projetos: com protótipo aprovado e não conferido, uma
  área inteira foi refeita; em outras três features com protótipo, vieram de 10 a 13 commits
  de ajuste depois da entrega, parte por divergência do protótipo; e dez decisões de produto e
  reversões de um ciclo nasceram de o usuário ver a tela pronta. Aprovar olhando a primeira
  prancha não é exercitar: peça que ele percorra os estados.
- **posição e hierarquia das ações:** grupo ao qual pertencem, ordem, destaque e estados
  em que aparecem. "Dentro da tela" não define agrupamento nem peso visual.
- **transições, quando afetadas:** origem, destino, sequência, condição de conclusão e
  quais elementos podem aparecer juntos; interrupção, retorno e repetição explícita.
- **retorno com estado preservado:** sair e reabrir mantendo a sessão viva, além de abrir
  do zero. Dado salvo não é, por si só, autorização para repetir uma apresentação.

Preencha estes itens a partir da referência e do fluxo real; só lacunas e conflitos viram
perguntas. A prova deve observar a integração afetada: em 2026-10-09, testes que simulavam
transições passaram com duplicação visual e reinício indevido encontrados no app real.

### Não-funcionais

- latência e throughput, com número
- escala e limites
- disponibilidade e recuperação
- **observabilidade**: que log, métrica ou evento prova em produção que funcionou
- segurança e privacidade: autenticação, autorização, dado pessoal, o que vaza se der errado
- **"somente leitura" protege escrita, não sigilo**: para cada credencial dada a um agente ou job,
  liste o que ela LÊ (segredos, chaves, tokens de sessão) e por onde um texto produzido por ele sai
  (notificação, renderizador que carrega URL, log, provedor externo). Medido em 2026-10-04: o papel
  read-only escolhido para um agente lia o cofre de segredos e as chaves dos clientes; a spec o
  tratava como fronteira e só a revisão externa contou.
- conformidade, se houver

### Integrações e dependências externas

- cada serviço externo, e o que acontece quando ele falha, demora ou muda de versão
- **fato externo de que o desenho depende** (o que a API de terceiro aceita e devolve, o que um
  modelo gera): é sonda, não premissa. Uma chamada real agora, ou o primeiro passo do plano,
  antes do código que a consome. Documentação do fornecedor não substitui a chamada. Medido em
  11/2026: de nove fatos de API e de modelo que viraram correção num ciclo, quatro a sonda
  planejada teria pego; ela foi adiada na largada e os nove só apareceram no teste ponta a ponta.
- formatos de importação e exportação
- **quem mais consome e quem mais emite** o que muda (a matriz bidirecional da spec)

### Bordas e falhas

- cenários negativos
- limites, throttling, cota
- **concorrência e conflito**: duas ações ao mesmo tempo, retry, idempotência, ordem de eventos
- **posse abandonada**: todo job que reivindica um item (status "em andamento") precisa dizer o que
  acontece se o processo morrer depois de reivindicar; sem prazo de posse, o item fica preso para
  sempre e bloqueia os seguintes. Medido em 2026-10-04: um índice de "um aberto por conversa" teria
  travado a conversa depois de uma única queda.
- **idempotência é por SUPERFÍCIE DE ESCRITA, não por feature.** Enumere cada botão, endpoint e
  job que grava, e responda *"e se disparar duas vezes?"* para **cada um**. A resposta muda entre
  superfícies da mesma feature, e é por isso que a pergunta feita uma vez só engana: no botão
  principal, dois toques costumam ser duas intenções legítimas; no **"tentar de novo"** de um
  erro, dois toques são **uma** intenção. Medido em 2026-09-03: a spec respondeu a pergunta uma
  vez, para o botão principal, e concluiu "duas linhas, deliberado" — o que estava **certo**. A
  superfície de retry herdou essa resposta sem nunca ter sido perguntada, e dois toques gravaram
  o dobro do valor. Categoria respondida globalmente é categoria que passa; obrigação por
  artefato força a enumeração.
- **quem já está no meio do fluxo** quando a mudança entra

### Comportamento removido ou substituído

Só se a feature tira ou troca algo que existe. **Validação, filtro ou gate novo sobre uma saída
que já existe conta como remoção**, mesmo descrito como garantia nova: meça no histórico
persistido quanto da saída de hoje seria rejeitada. Medido em 2026-09-12: a spec descreveu um
gate de números como garantia; ninguém olhou as respostas atuais, 153 de 209 tinham dígito, e
o plano apertou a regra além da spec sem decisão de ninguém.

- **quantos lugares emitem** o comportamento antigo, contados de duas formas: pelos
  chamadores da função canônica e pelo texto literal emitido (os dois acham coisas diferentes)
- os **gatilhos** do módulo substituído: quando ele agia sem ninguém pedir, cada um com
  decisão escrita: mantido, removido porque X, coberto por Y

### Restrições e trade-offs

- restrição técnica: linguagem, storage, hospedagem, custo
- o que foi escolhido em vez de quê, e por quê

### Terminologia

- cada conceito tem um nome só na spec
- termo que o código usa com outro nome está mapeado

### Sinais de conclusão

- cada requisito tem cenário de aceitação que dá para executar
- cada critério de sucesso tem número e baseline

### Placeholders

- TBD, "a definir", "etc.", "e afins"
- adjetivo sem número: rápido, robusto, intuitivo, "em tempo real", grande, muitos, poucos
- "por padrão", "provavelmente", "algo como"

## O que a varredura não é

Não é questionário para o usuário. A maior parte das categorias se resolve olhando o código
e o dado (fato é trabalho seu), e o que sobra vira pergunta com recomendação, na rodada,
como qualquer outra. Categoria que não se aplica recebe uma linha e acabou; não infle a spec
com seção vazia para "cobrir" a lista.
