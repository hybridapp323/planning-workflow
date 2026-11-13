# Decompor (Fase 1)

Referência da skill `power-plans`. Leia ao dividir o trabalho: níveis, ownership de arquivo, contratos congelados e critério de pronto.

## Fase 1 — decompor

### Níveis de complexidade

Três níveis. O critério é **custo do erro somado à profundidade de raciocínio**, nunca tamanho. Uma tarefa de dez linhas que decide precedência entre regras é complexa. Uma de trezentas linhas de tradução é baixa.

- **Complexa** — o erro é caro ou difícil de detectar: invariante, concorrência, segurança, dado de produção, irreversível. Ou exige segurar muito contexto ao mesmo tempo.
- **Média** — solução conhecida, escopo claro, o erro aparece em teste ou na tela.
- **Baixa** — mecânica, verificável por inspeção, sem decisão de design.

Rubrica completa com exemplos e casos de fronteira: `references/complexity-rubric.md`.

Na dúvida entre dois níveis, suba. O modelo mais forte numa tarefa média custa menos que o retrabalho de uma complexa mal feita.

**O plano nunca nomeia modelo.** Escreve `<MODELO_COMPLEXA>`, `<MODELO_MEDIA>`, `<MODELO_BAIXA>` e `<MODELO_GATE>` como placeholder. Quem atribui é o usuário, na hora de executar, porque a escolha depende de custo, disponibilidade e humor do dia, não do plano.

### Ownership de arquivo

Um arquivo, um dono. É isto que impede dois workers paralelos colidirem, e é o item mais barato de esquecer e mais caro de descobrir tarde.

Se duas tarefas precisam do mesmo arquivo, você tem três saídas legítimas e nenhuma quarta:

1. Junte as duas numa tarefa só.
2. Parta o arquivo, e o corte vira parte do plano.
3. Serialize com dependência explícita no grafo.

"As duas mexem e depois a gente concilia" não é saída. Escreva a matriz como tabela, caminho por caminho, e marque-a como normativa.

A única exceção existe entre ondas paralelas em worktrees separadas (Fase 2): ali o arquivo que as
duas tocam entra na tabela do que não roda junto, com o trecho de cada onda nomeado, e quem
concilia é a onda que integra depois. Dentro de uma onda, nenhuma exceção.

Arquivos que várias tarefas **leem** mas ninguém escreve não entram no conflito. Diga isso explicitamente, senão alguém serializa à toa.

**A matriz não sai da memória, sai de um traçado.** Listar os arquivos que você leu enquanto
desenhava produz uma matriz que parece completa e não é: ela contém a origem e o destino, e
perde o meio. Para cada dado ou comportamento novo, siga o caminho inteiro e anote **cada
salto**, porque cada salto é um arquivo com dono:

```
onde nasce  ->  quem transporta  ->  quem decide  ->  quem emite  ->  quem consome
```

O salto mais esquecido é o transporte: um objeto de contexto reconstruído no meio do caminho
**descarta silenciosamente** todo campo que ninguém encaminhou de propósito, e aí a sua flag
nova chega `undefined` no destino com todos os testes verdes. Medido em 2026-08-26: uma
matriz de 22 arquivos saiu com 5 faltando, e o que mais doía era exatamente um desses
transportes.

**O traçado é uma TABELA do plano, não um exercício de cabeça:** uma linha por requisito que
move dado ou comportamento, uma coluna por salto, `arquivo:linha` em cada célula (esqueleto, §3.1).
Conselho em prosa é aplicado quando o autor lembra; célula vazia fica visível para quem revisa, e
a matriz de ownership passa a ser derivada das células, não da memória. Medido em 25/09/2026:
3 dos 11 bloqueadores da revisão externa eram saltos sem dono (decisão no chamador errado,
comportamento sem ponto de emissão, dado que não chegava a um dos canais de saída), num plano cuja
skill já mandava traçar. A regra existia; a coluna, não.

**A última coluna também é salto, e é a que mais sai em prosa.** Quando o efeito observável de um
requisito é uma superfície (uma tela, um painel, um relatório, uma linha de log que alguém vai
ler), a célula leva o arquivo que a renderiza e o dono dele, não uma frase como "aparece para o
administrador". Frase na última coluna passa pela auto-revisão, porque a célula não está vazia, e
chega à execução sem dono: o coordenador descobre no meio da onda que ninguém desenha aquilo, e
fecha o buraco com contrato novo e responsabilidade dividida entre tarefas já despachadas.
Medido em 29/09/2026: um requisito cujo critério era "depois de N falhas, aparece como pendente
no painel do admin" tinha na última coluna só "pendência visível"; nenhuma tarefa possuía o
painel, e o contrato do dado, a visão e a tela foram repartidos entre três tarefas na segunda
onda.

**Teste existente que trava o comportamento antigo é arquivo da matriz.** Quando o plano muda ou
remove um comportamento, os testes que o afirmam hoje (unitários **e** cenários ponta a ponta)
entram na matriz com dono único e a decisão escrita: reescrever e renomear, nunca apagar. Procure
pelo literal do comportamento nos diretórios de teste, e não só pelo nome do arquivo que muda.
Sem isso, duas tarefas paralelas reescrevem o mesmo teste, ou o teste que exige o comportamento
removido aparece só na bateria antes do deploy. Medido em 25/09/2026: as duas coisas no mesmo
ciclo, uma achada pela revisão externa e a outra só na véspera da publicação.

**Arquivo GERADO não tem dono sozinho: o dono é a fonte.** Quando um arquivo do plano é saída de
um gerador (uma tabela derivada de um inventário, tipos derivados de um schema, um mapa derivado de
um documento), a linha da matriz é a **fonte**, mais o comando que regenera e o teste que compara
saída com fonte. Editar só a saída faz o teste de frescor reprovar, e regenerar depois desfaz a
edição. Procure o gerador antes de atribuir: um teste que compara byte a byte é a pista. Os testes
que consomem a saída (navegação, links) entram na matriz junto. Medido em 2026-10-10: um plano
atribuiu a mudança de um mapa de rotas e não o inventário que o gera; a revisão externa achou o
teste de frescor e mais três testes consumidores que quebrariam no aceite.

**Linha NOVO cita o irmão.** Arquivo que ainda não existe entra na matriz com o irmão existente
do mesmo tipo e a configuração que o descobre, os dois com `[LIDO:]`. Sem isso o caminho é
`[SUPOSTO]`, e o `ls` da auto-revisão não tem o que conferir (classe 4, `references/classes-de-erro.md`).

**Depois de escrever a matriz, releia as descrições das tarefas e procure responsabilidade
repetida.** Duas tarefas podem não colidir em arquivo e ainda assim receberem a mesma frase
("resolve a config no bootstrap"). Colisão de responsabilidade é colisão, e aparece mais tarde
e mais cara que a de arquivo.

### Contratos congelados

Este é o item que faz o paralelismo existir. Workers não divergem na ordem das coisas, divergem no formato delas.

Congele, antes da primeira onda: tipos e interfaces compartilhadas, shape de request e response, nomes de chave de i18n, props na fronteira entre dois componentes, e a fixture de casos que serve de fonte da verdade de uma regra de negócio.

**Ordem de eventos também é contrato.** Quando duas tarefas dividem uma transição ou
operação assíncrona, congele estados, identidade da execução, quem inicia/confirma/cancela
e a condição que libera a próxima etapa. Inclua interrupção e retorno com estado vivo.
Flag alterada não prova efeito observado: indique qual confirmação a fronteira requer.
Para interface com referência aprovada, vincule esse contrato ao §8.3 da spec.

Quem escreve é o coordenador, num passo próprio antes de despachar qualquer worker, e commita. Não delegue a um worker o contrato de que os outros dependem.

Escreva literal, em bloco de código completo. Contrato descrito em prosa é contrato não congelado.

**Campo derivado tem tabela de derivação por origem.** Todo campo do contrato que não é cópia
1:1 de uma coluna vem com a regra por origem, e cada origem com a sua medição na linha real.
Medido em 2026-09-12: o contrato tinha `mode: outdoor | treadmill | unknown` sem dizer de onde
vinha; a spec tinha medido esteira num provedor e não olhado o sinal de esteira do outro, onde
149 corridas em esteira chegavam com ganho de elevação zero e virariam "rua plana" pela regra
literal, formando par com corridas de rua.

**Contrato não é mais restrito que o FR que implementa.** Se o plano aperta uma regra que a
spec enuncia mais solta, isso é decisão com autoria na spec, não detalhe técnico do plano.
Confira lendo a frase do requisito ao lado da frase do contrato: toda condição que o contrato
tem e o requisito não tem ("quando o usuário pede", "só no estado X", "na primeira vez") é
aperto. Aperto que muda o que o usuário vê volta a ele como pergunta **antes** de congelar; não
se resolve no plano nem num conserto da spec feito por você. O cenário de aceitação não é o
teto do requisito: se a frase do FR é mais larga que o exemplo, vale a frase.

**Contrato tem de ser executável inteiro: leia cada regra contra as outras antes de congelar.**
Worker obediente não resolve contradição, escala, e cada escalação é um worker parado esperando o
coordenador. Quatro formas que pararam workers, cada uma pegável em segundos na releitura:

- **Ação exigida sob uma condição que, por definição, já não vale.** "Toda escrita exige ser o dono
  do lease" mais "ao perder o lease, grave o motivo na linha": a segunda regra é inexecutável pela
  primeira. Decida onde o efeito vai (log, outra tabela) no contrato.
- **Duas exigências literais sobre o mesmo campo.** Formato fixo do texto e, em outra seção, "inclua
  o valor original nesse texto quando X". Escreva o formato com a variação dentro.
- **Comportamento de API externa citado como documentado sem a documentação dizer.** "Trate o erro
  documentado de recurso já cancelado como sucesso", sem código nem corpo na doc. Ou meça, ou
  congele a verificação que dispensa saber (ler o recurso de volta e conferir o estado).
- **Linha de risco ou watchlist com ação de código.** "A tarefa X registra erro quando Y" numa tabela
  de riscos, contradizendo o contrato que trata Y como válido. Ação de código em risco é requisito
  escondido: vira contrato, ou sai do risco.

Medido em 2026-10-29: plano de 7 tarefas com contratos literais e uma revisão externa já aplicada;
na execução, **5 escalações**, todas uma destas quatro formas, nenhuma defeito de worker. Cada uma
custou um worker parado e uma ida e volta; duas vieram em dobro (escalação e pergunta bloqueante
com o mesmo texto).

### Critério de pronto: é contrato também, e cola literal

O `Pronto quando` de cada tarefa **é o cenário de aceitação do FR**, copiado da spec, não uma
paráfrase escrita agora. Vale aqui a frase da seção acima, sem mudar uma palavra: descrito em
prosa, ele é reinventado por quem despacha.

**"Verificável" não basta.** *"Quando `<runner> x.test.ts` passar"* é verificável e não diz
**o que** o teste tem de afirmar — quem escreve o teste decide, pelo que entendeu. *"Dado o aviso
visível, quando tocar Desfazer, então **aquela linha** é apagada"* é o mesmo critério com a
semântica dentro, e é a diferença entre apagar por identidade e apagar por predicado.

**O oráculo afirma o efeito que o requisito exige, não o mecanismo que o produz hoje.** Tarefa
que escreve teste ou cenário diz o que cada um afirma em termos de efeito: o estado em que o
sistema fica, o dado gravado, o que foi entregue. Qual função ou ferramenta foi chamada, por
qual caminho, e o texto literal de uma saída de modelo só entram quando são o comportamento
sob teste. Nome que designa duas coisas (um estado e uma ferramenta com o mesmo nome) é escrito
por extenso no plano. E cenário pago novo roda uma vez sozinho, com o vermelho ou o verde lido,
antes de entrar num lote. Medido em 11/2026: de seis correções de oráculo num ciclo, três
exigiam a ferramenta ou o estado do caminho antigo, e reprovaram o comportamento novo correto
quando a correção passou a produzir o mesmo efeito por outro caminho; duas exigiam o texto
literal do modelo e reprovaram paráfrase correta; uma misturava as duas coisas. Cada uma custou
uma rodada no ambiente pago.

Medido em 2026-09-03: a spec tinha 13 FRs, cada um com cenário
executável, e cobria corretamente virada de meia-noite, duplicação de fórmula e semântica de
campo nulo. O plano citava **6 dos 13 FRs zero vezes** e não tinha **nenhum** `Pronto quando` —
porque as tarefas foram compactadas numa tabela (`| id | tarefa | nível | dono | arquivos |`), e
coluna que não existe não é preenchida. O coordenador então escreveu o critério de cada briefing
de cabeça, relendo a spec. Foi nessa releitura que nasceu o defeito mais caro do ciclo: um campo
que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing, e dias de
descanso ganharam 300 ml que não existiam.

> **Coordenador improvisando critério de pronto É o defeito.** E ele só improvisa quando não há
> o que copiar. O lugar de consertar isso é aqui, não lá.

Compactar tarefas em tabela é legítimo, densidade ajuda. Mas então **a tabela carrega as colunas
`FR` e `Pronto quando`**. O formato é escolha sua; as duas colunas não são.

**O `Pronto quando` diz também a CAMADA de prova, da mais barata para a mais cara.** Primeiro a
que exercita o consumidor real sem custo por execução: teste de unidade ou replay do fluxo sobre o
caso real, e comparação da decisão velha com a nova sobre o histórico persistido (mede o alcance:
quantos casos reais mudariam). Prova que chama modelo pago ou envia algo para fora só para o que as
baratas não alcançam: trajetória de vários passos, comportamento do modelo, envio, persistência. E
só o cenário afetado, não a bateria. Paridade de predicado não prova correção de contexto: a
comparação sobre o histórico mostra o alcance, e quem prova é o caso que passa pelo consumidor.
Medido: no mesmo projeto, testes ponta a ponta pagos foram de 29% a 43% dos tokens gastos com o modelo no fluxo principal
num mês.

**A camada precisa preservar o mecanismo sob risco.** Liste as peças reais e as simuladas;
simular a peça que causa o risco deixa aquele cenário pendente, mesmo com teste verde.
Se o risco depende de interação ou ordem de eventos, planeje uma primeira prova do percurso
crítico assim que suas dependências existirem, antes de ampliar variantes. Use a integração
real e separe os eventos como acontecem nela; registre candidato, resultado e limitações.
Esta é prova no aceite do coordenador, não outro gate adversarial, e respeita as autorizações
do projeto. Medido em 2026-10-09: testes com etapas agrupadas passaram com falhas de transição
e reabertura na aplicação real; a prova tardia exigiu novas rodadas de correção.
