# O grafo (Fase 2)

Referência da skill `power-plans`. Leia ao cortar as ondas: trilhas, caminho crítico, estimativa e ondas em worktrees.

## Fase 2 — o grafo

**Ondas são trilhas, não camadas.** Uma onda é uma sequência de tarefas ligadas por dependência, e termina exatamente onde o coordenador precisa agir. Descubra o que este projeto proíbe delegar (ver *Regras do projeto*, abaixo): tipicamente git, migration, deploy e publicação. Esses passos viram passos do coordenador, e são eles que definem onde a onda quebra. Não é escolha estética. Aceitar e commitar a entrega de uma tarefa não quebra onda: isso acontece por tarefa, dentro dela.

Corte nesta ordem:

1. **Separe as trilhas.** Trilha é um grupo de tarefas que dependem umas das outras (irmãs do mesmo
   pai ficam juntas) e que se liga aos outros grupos por poucas arestas, cada uma resolvível por
   contrato ou ponto de integração (abaixo). Não use "componente conexo do grafo": uma única aresta
   cruzada junta tudo num grupo só, e o paralelo some de novo. Conte as arestas cruzadas e escreva o
   número no §2.1.
2. **Cada trilha vira uma onda paralela com coordenador secundário** (seção abaixo), sempre que for
   seguro. É o padrão, não a exceção. Trilha de uma tarefa só não justifica coordenador: entra na
   onda de quem a consome ou na do principal.
3. **Dentro da onda, despache por dependência.** Uma tarefa sobe assim que as dependências dela
   foram aceitas, sem esperar as vizinhas da mesma profundidade.

O erro que isto evita: cortar o grafo por profundidade (o que só depende de C0 é a onda 1, o que
depende da onda 1 é a onda 2). Assim toda onda depende da anterior por construção, a regra de ondas
paralelas nunca dispara, e cada camada espera a tarefa mais lenta dela. Medido em 2026-10-23: um
plano de 18 tarefas saiu em três camadas por profundidade; por dentro havia três grupos (servidor,
compartilhar, telas) ligados por quatro arestas cruzadas, o do servidor sem depender de nenhum
outro, e nenhum ganhou coordenador próprio. Quem notou foi o usuário. O exemplo do template também
desenhava camadas, e o plano copiou o formato.

Escreva três coisas, sempre:

1. **O grafo**, em ASCII, com as dependências visíveis.
2. **O que roda junto**, por onda.
3. **O que NÃO roda junto, com a razão de cada par.** Sem a razão escrita, alguém vai "otimizar" isso depois e reintroduzir a colisão.

Marque o **caminho crítico**. É o que diz se vale acrescentar worker ou se você só vai acrescentar espera.

**Estimativa: em tokens, nunca em dias.** "Dois dias", "uma semana" medem trabalho humano em
série; aqui quem implementa é modelo em paralelo, e o que levaria dias costuma sair no mesmo dia.
O plano dá três números, como ordem de grandeza: **tokens totais** (o custo), **tokens de saída**
(o que os workers escrevem) e **tempo de relógio** ≈ tokens de saída do **caminho crítico** ÷ vazão
do modelo (referência: ~60 tok/s), somado às esperas fixas (suíte, deploy, teste pago, aceite do
usuário). Tarefas fora do caminho crítico entram no custo e não no relógio. Nunca divida o total
pela vazão: quase todo o total é releitura de contexto, que não custa esse tempo, e a conta sai
dezenas de vezes maior. Diga qual parcela domina; quando são as esperas, mais worker não adianta.
Vale também na conversa: quando o usuário pergunta o prazo, a resposta sai desta conta, não de
horas por onda somadas. Medido em 2026-10-23: a resposta em conversa somou horas por camada e deu
2 a 3 dias para um plano cuja própria conta dava menos de um dia.

**Sem número fixo de workers.** Tarefas que tocam arquivos diferentes e não dependem uma da
outra rodam todas ao mesmo tempo, na mesma trilha ou em trilhas paralelas; um teto como "3 por vez"
só acrescenta espera. O único
freio legítimo é a cota do dia nos modelos, e aí distribua entre provedores e comece pelo caminho
crítico. Durante a onda, cada worker roda só os próprios testes; a suíte inteira roda no aceite.
Medido em 24/09/2026: o plano saiu com teto de 3 workers que ninguém pediu, e o usuário mandou tirar.

**Ordene por dependência de COMPORTAMENTO, não por custo.** A tentação é pôr primeiro o que é
barato e reversível, tipicamente configuração, e deixar o código para depois. Isso inverte a
ordem real: configuração que liga um comportamento cujo código ainda não existe deixa o
sistema num estado que ninguém desenhou, meio novo e meio velho, **em produção**. A regra
geral: primeiro o que é aditivo e inerte (schema, código com default igual ao de hoje), depois
o que entrega, e por último a chave que LIGA. Esse último passo é o cutover, e ele deve ser
reversível numa linha.

**Corolário que economiza uma rodada inteira:** se, ao escrever um passo de validação, você
já sabe apontar um item dele que vai falhar por causa de outra tarefa ainda não feita, a
ordem está errada. Não escreva "este item vai falhar aqui, é esperado" — isso é um gate que
não guarda nada. Reordene.

### Ondas paralelas em worktrees separadas: um coordenador por onda

Dentro de uma onda os workers dividem a árvore, e a ownership resolve. Duas ondas independentes na
mesma árvore, não: cada uma tem aceite, suíte e commit próprios, a suíte de uma roda com o código
pela metade da outra (a mesma classe de *Medir nas dependências do checkout compartilhado*, em
`orchestrating-execute`), e o commit de uma estagia trabalho da outra. Sempre que o grafo tem duas
ou mais trilhas e é seguro, cada trilha ganha worktree, branch e coordenador secundário próprios; o
coordenador principal toca uma delas na árvore atual. **Seguro** quer dizer: contratos congelados
em C0, arquivos disjuntos ou com o trecho de cada onda nomeado, e todo recurso único (ambiente,
migração, dado) com o principal pela tabela de papéis. Quando não é seguro, o §2.1 diz em uma linha
"Ondas paralelas: não, porque …"; sem essa linha o plano não está pronto. Escala parcial não usa
isto. Projeto que só aceita branch ou worktree a pedido: o plano traz as ondas paralelas mesmo
assim, e a pergunta vai junto com a entrega do plano; nunca corte em silêncio.

**Dependência cruzada não junta trilhas.** Quando uma tarefa de uma trilha consome a entrega de
outra, tente nesta ordem: (a) congele em C0 o que a consumidora precisa (tipo, assinatura,
fixture) e ela segue sem esperar o código; (b) marque um ponto de integração: o principal integra a
tarefa produtora e a trilha consumidora faz rebase antes de despachar a consumidora; (c) só se
nenhuma serve, mova a consumidora para a trilha produtora. Fundir duas trilhas inteiras por causa
de uma aresta devolve o plano às camadas.

O plano escreve quatro coisas:

1. **A tabela de papéis.** Só o principal integra na branch principal, publica (homologação
   inclusive), roda teste ponta a ponta, aplica migração e escreve em dado: com dois coordenadores
   publicando no mesmo recurso único (um ambiente de homologação, um ambiente de teste por tipo), o
   teste de um roda com o código do outro. O coordenador de onda despacha e aceita os workers
   dela, roda a suíte, commita no próprio branch e resolve os conflitos com a branch principal.
2. **Os arquivos que duas ondas tocam**, com o trecho de cada uma. Mesmo trecho nas duas é colisão:
   junte, serialize ou parta, como dentro de uma onda.
3. **A ordem de integração**, que é também a ordem dos rebases.
4. **O que a worktree nova precisa**, no passo que a cria. Ela nasce sem o que o git ignora
   (arquivo de segredos, dependências instaladas), e ferramenta que reescreve a pasta de
   dependências pede instalação isolada por worktree.

A entrega da onda é o branch local, não um PR. Procedimento e porquê: `orchestrating-execute`,
*Ondas paralelas em worktrees*.
