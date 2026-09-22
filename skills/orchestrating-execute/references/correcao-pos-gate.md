# Correção pós-gate: as lições medidas

Complemento da seção *Como despachar a correção pós-gate* do `SKILL.md`. A regra está lá, em uma
linha por lição; aqui fica o caso que a pagou, com a medição. O desenho vigente é o gate como
cartada única (`SKILL.md`, seção *Dois mecanismos de qualidade*): estas seções falam de "rodada
2" e "rodada 7" porque foram medidas antes dessa regra, ou em ciclos em que o usuário pediu
rodadas extras. O mecanismo que cada uma descreve vale igual na única rodada que existe: ele
decide a FORMA da correção que você despacha depois do veredito.

## O gate adversarial tem um teto, e ele se chama "mesmo emissor de novo"

Medido em 27/08/2026, num ciclo de canais de mensagem: o gate (revisor read-only, modelo forte,
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

## O brief que lista contraexemplos produz fixes do tamanho dos exemplos

Medido em 14/09/2026, num ciclo de auditoria: sete rodadas de gate, todas com
achados reais, e o mesmo arquivo de política de pedido de mídia voltou em TODAS — janela,
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

## Todo gate tem orçamento: a terceira reprovação da mesma família é decisão de ship

Medido no mesmo ciclo: as rodadas 5–7 continuaram achando defeito real, mas
cada vez mais exótico (anáfora parentética, rótulo só-emoji, dois estados
terminais marcados ao mesmo tempo). O custo por rodada ficou constante e o risco residual
encolheu — e quem parou o loop foi o usuário, não o plano. Nenhuma skill dizia
quando parar.

Este ciclo rodou sete rodadas **contra** a regra do gate como cartada única (`SKILL.md`, seção
*Dois mecanismos de qualidade*, decidida pelo usuário em 12/09/2026): pelo desenho vigente a rodada dois de um gate só
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

## Quando o revisor acusa o MECANISMO do teste, pare de despachar correção

Medido em 2026-09-12, num ciclo de cobrança. O gate reprovou duas vezes. Na
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
4. **Ele aceita apontar para uma cópia mutada** (aqui, uma variável de ambiente com o caminho da migration).
   Sem isso, todo worker vai neutralizar editando o arquivo de produção numa
   árvore compartilhada, e um worker que morrer no meio deixa o defeito lá.

E a decisão de escopo que economiza o dobro do tempo: **não persiga fidelidade
máxima se o barato cobre o que a tarefa toca.** A primeira tentativa foi subir a
stack local inteira; ela morre replicando 429 migrations, numa
`cron.alter_job(6, …)` cujo job id só existe em produção. O schema em revisão
dependia de cinco objetos externos. Meça a superfície de dependência ANTES de
escolher o caminho: `grep` das referências externas custa um minuto e decide
entre vinte minutos e a tarde inteira.

## Reprovação que o instrumento ACHOU não é a mesma que a que ele não viu

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

## Todo teste negativo precisa de controle positivo

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

## O teste que nomeia a mesma coisa duas vezes esconde a asserção que falta

Medido em 2026-09-12, e é o defeito mais sutil que este ciclo produziu, porque
sobreviveu a uma revisão adversarial que o aprovou explicitamente.

Um contrato dizia: *"o estado transferido exige **exatamente um** identificador: o da
obrigação local **ou** o do pagamento no provedor"*. Uma rodada de correção endureceu
"valide o identificador do provedor" em "**sempre** exija o identificador do provedor", o que
recusa um caminho que o contrato permite. O revisor marcou aquele achado como fechado, com
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

## Documento de ciclo: toda afirmação precisa do comando que a produziu

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

## O caso mais barato de prevenir: mudou um TIPO compartilhado

Medido em 2026-08-28. Uma tarefa acrescentou um valor a um enum de status de execução para
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
roda uma vez (`SKILL.md`, seção *Dois mecanismos de qualidade*): quem julga a correção é o teste
que ela traz, e a correção tem de ser ESTRUTURAL para um teste valer por todos os emissores.

## Requisito que você marca como BLOQUEANTE tem de vir com o teste que o falsifica

Medido em 21/09/2026, num ciclo de atribuição de atendente. O mandato do gate dizia, com
essas palavras, que uma checagem de reativação tinha de ser **avaliada uma vez** e o valor já
computado repassado adiante, e marcava isso como bloqueante. O worker implementou. A suíte
fechou **61/61 verde**. O gate adversarial então **apagou o repasse** (reavaliou em vez de reusar o valor) e a
suíte continuou **61/61 verde**: nenhum teste observava o repasse, só o resultado, que era o
mesmo nos dois caminhos naquele fixture.

Um requisito que ninguém consegue violar num teste não é um requisito, é uma intenção.

**A regra:** todo item que o brief marca como bloqueante entrega **duas** coisas, e a segunda
é a que vale: (1) a implementação; (2) o teste que fica **vermelho quando aquele item
específico é desfeito** — não o teste do comportamento vizinho. No brief, escreva o
falsificador junto do requisito:

> "Passe o valor já computado. **Prova:** trocá-lo por uma segunda avaliação tem de derrubar um
> teste nomeado."

Vale principalmente para requisitos de **forma** (avaliar uma vez, persistir antes de enviar,
chamar por este caminho e não por aquele): o resultado final costuma ser idêntico, então só um
teste que olhe a forma pega. Requisito de forma sem falsificador é onde o gate seguinte acha
trabalho.
