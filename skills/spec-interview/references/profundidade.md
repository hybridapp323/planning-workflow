# Caminho, profundidade e parada da entrevista

Referência da skill `spec-interview` (Fase 2). Leia antes da primeira rodada (o caminho) e quando achar que a entrevista acabou (a profundidade).

### Regra das rodadas

Uma resposta do usuário quase sempre abre galho novo — ele escolhe uma opção e aquela opção traz três decisões que não existiam antes. **Só pare quando uma rodada inteira não abrir nenhum galho novo.** Uma rodada só e acabou é sinal de que você tratou a árvore como lista.

**No caminho arquitetural, uma rodada é sempre pouco.** Se você chegou ao fim da primeira rodada achando que entendeu tudo, você entendeu a superfície: a primeira rodada estabelece o quê, a segunda descobre o como e o que quebra, a terceira encontra o que ninguém tinha visto. Não é cerimônia — é onde a spec para de mentir.

### Sinais de que você parou cedo

- Você escreveu "por padrão", "provavelmente" ou "algo como" no design.
- Você conseguiria implementar de duas formas bem diferentes sem violar nada do que foi conversado.
- Você não sabe dizer o que a feature **não** faz.
- Você não sabe o que acontece com quem já é usuário hoje.
- O usuário respondeu com "acho que", "sei lá" ou "tanto faz" — isso é uma decisão em aberto disfarçada de resposta, não um aval. Ofereça a sua recomendação e feche.
- Uma opção do modal contradiz um requisito que o usuário já enunciou, e o texto da opção não diz isso. Medido em 2026-09-18: o usuário escolheu a opção que não entregava o requisito dele, porque a descrição não dizia; custou uma rodada inteira de reconciliação. **A contradição vai dentro do texto da opção, não em prosa antes do modal.**

### Quando parar mesmo assim

Duas exceções, e só elas: o usuário dizer explicitamente para tocar ("chega, escreve"), ou o caminho ser **sonda** ou **limitada**. Nesses, raso quer dizer sem varredura de cobertura e sem arquivo de spec. Não quer dizer decisão em aberto.

### O caminho leve não fecha decisão por omissão

Os passos 1 a 3 do teste de fechamento valem em todo caminho, inclusive na mudança que se faz direto: o que você decidiria sozinho e muda o que o usuário vê, o dado gravado ou o custo vira pergunta **antes** da implementação. O caminho escolhe quanto documento se escreve, não quantas perguntas se fazem. Limitada com seis perguntas continua limitada; o que a faz subir é o tamanho da obra (o design não cabe em dez linhas de chat, aparece um segundo dono), nunca o número de perguntas.

Conte as decisões antes de escolher o caminho leve. Um pedido de capacidade nova costuma chegar em uma ou duas frases, às vezes com uma única dúvida declarada, e a dúvida declarada esconde as outras: quanto custa, qual é o limite, o que acontece quando falha, o que muda para quem já usa. Medido em 11/2026, num ensaio de roteamento com doze pedidos de amostra: um pedido assim foi tratado como "uma pergunta e faz" nas duas rodadas de um modelo intermediário, e as decisões restantes ficariam para a implementação, que é onde decisão não tomada custa mais caro.

O tamanho do documento se decide pela obra, depois de entender o pedido, e não pelo número de perguntas. Medido no mesmo ensaio, com uma mudança pequena de regra de processo que escondia quatro ou cinco decisões: com o critério "escopo ainda aberto", ela saiu arquitetural (spec e plano) em 3 de 3 rodadas do modelo mais forte, porque quanto melhor a entrevista, mais decisões aparecem; com o critério "tamanho da obra", saiu limitada em 3 de 3 (as mesmas perguntas, design curto no chat), e três capacidades novas continuaram arquiteturais, com três rodadas ou mais.

"Chega, escreve" com decisão em aberto **não** autoriza spec com decisão aberta. Liste numa mensagem só cada decisão restante com a sua recomendação ("fecho Q3 com X, Q4 com Y") e peça um aval único. Com o aval, elas estão fechadas, registradas na spec como *decididas pelo usuário ao mandar seguir*, e a spec começa. Sem o aval, nada de spec.

## Questione o caminho antes de abrir a árvore

O pedido costuma chegar como um **caminho** ("portar a tela X para a plataforma Y"), não como um **objetivo** ("usar a tela X no lugar Z"). Se você monta a árvore de decisões do caminho, toda pergunta da entrevista refina um plano que talvez não devesse existir.

Depois de ler o contexto e antes da primeira rodada, escreva em uma linha o objetivo por trás do pedido e pergunte se o caminho pedido é o mais barato até ele. Se existir caminho que chega no mesmo objetivo com uma fração do esforço, ou se o pedido contraria uma decisão já registrada no projeto, pare e apresente **antes de qualquer pergunta sobre o como**: "Você pediu X. O objetivo parece ser Y. Z chega em Y com uma fração do esforço, mas perde W. Recomendo Z porque…". Se não der para deduzir o objetivo, a primeira pergunta da entrevista é o "para quê".

Não fabrique alternativa para parecer crítico: se o caminho pedido já é o melhor, siga sem comentar. Se o usuário reafirma o caminho depois de ver o trade-off, a decisão é dele: registre na spec como decisão com a alternativa descartada e siga.

Vale no caminho **arquitetural** sempre e na **limitada** quando o pedido contraria um fato do projeto. Sonda não passa por aqui.

**Se o pedido tem vários subsistemas independentes** ("uma plataforma com chat, arquivos, cobrança e analytics"), diga isso imediatamente, antes de gastar perguntas refinando detalhe. Ajude a decompor: quais são as peças independentes, como se relacionam, em que ordem. Cada peça ganha o próprio ciclo spec → plano → implementação.

**"Quero tudo junto" decide a entrega, não o número de specs.** Quando o usuário pede as peças
entregues de uma vez, pergunte as duas coisas em separado, com a sua recomendação: a publicação é
única? E o trabalho segue em uma spec ou em uma por peça, com a entrega combinada no fim? Diga o
custo de cada opção: uma spec só reparte a entrevista, a conferência e a revisão por todas as
peças, e a peça mais delicada recebe a mesma atenção que a mais simples. O mesmo vale quando a
spec, já no meio, passa de uns dez requisitos ou você se pega escrevendo "trilhas independentes":
pare e pergunte antes de continuar. Se o usuário mantém tudo numa spec, registre a decisão e rode
a conferência do construtor por trilha.

Medido em 11/2026: o usuário respondeu "tudo junto, em paralelo se for seguro" sobre a entrega, e
isso foi lido como uma spec e um plano. Saíram cerca de 30 requisitos em cinco trilhas e um plano
de 51 tarefas e mais de 5 mil linhas, escrito em menos de quatro horas. O pré-voo e a revisão
externa devolveram 58 achados, e as correções caíram em outros requisitos; os dois requisitos que
depois custaram correção em cadeia passaram por todas as leituras sem achado nenhum.
