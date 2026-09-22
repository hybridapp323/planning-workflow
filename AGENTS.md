# AGENTS.md — regras de quem edita este repositório

Este repositório não é um projeto. É um conjunto de skills que são **carregadas dentro de
projetos alheios** — repositórios diferentes, linguagens diferentes, bancos diferentes, clientes
diferentes. Uma linha escrita aqui vai ser lida em sessões que não têm nada a ver com o lugar
onde o aprendizado aconteceu.

Daí a única regra que governa todo o resto.

## A regra

> **Aqui entra o CONCEITO. A peculiaridade do repositório onde você aprendeu fica lá.**

Você acabou de pagar um erro num projeto e quer que ele não se repita. Isso é exatamente o que
este repositório aceita — mas o que entra é o **mecanismo** do erro, não o caso.

Um caso que virou regra é uma frase que alguém que nunca viu aquele projeto consegue aplicar no
dele. Um caso que ficou caso é uma frase que só funciona para quem conhece aquela tabela, aquele
comando, aquele cliente.

## O teste, antes de commitar a linha

Três perguntas. Se qualquer uma falhar, a linha ainda é caso, não regra.

1. **Quem nunca viu aquele repositório consegue agir a partir disto?**
2. **Apague todo nome próprio da frase. A regra sobrevive?** Se ela morre sem o nome da tabela,
   do arquivo, do cliente ou do comando, o nome *era* a regra — e ela não era regra.
3. **Isto seria útil no próximo projeto, com outra stack?** Se a resposta depende de o próximo
   projeto usar o mesmo banco ou o mesmo framework, reescreva um nível acima.

## Nunca entra

- Nome de cliente, empresa, pessoa, ou workspace.
- Id de projeto, conta, tenant, chave, url, token, caminho de máquina. Nem como exemplo.
- Nome de tabela, coluna, função, módulo ou arquivo de um projeto específico, **escrito como se
  o leitor soubesse o que é**.
- Comando de uma ferramenta que só aquele projeto usa, quando a lição não é sobre a ferramenta.
- Regra de negócio, invariante de domínio, ou decisão de produto de um projeto. Isso é do
  `CLAUDE.md` / `AGENTS.md` dele, e só faz sentido lá.

## Entra

- **O mecanismo**: o que enganou, por que enganou, e o que teria denunciado antes.
- **A medição, como lastro**: data, o que foi medido e o número. É o que separa regra de opinião,
  e é o critério de entrada de todas as skills (*custou*). O caso vem reduzido à forma genérica:
  "uma função auxiliar que fazia a própria escrita" em vez do nome dela.
- **O sintoma que se reconhece cedo** — de preferência em uma linha, do tipo "você se pega
  fazendo X pela terceira vez".
- **O custo**, em unidade que qualquer um entende: rodadas, ondas, horas, um run pago.

## Como generalizar o que você acabou de aprender

Escreva a lição na forma concreta, do jeito que ela aconteceu. Depois **remova os nomes próprios
um a um**, e a cada remoção pergunte se a frase ainda ensina alguma coisa. O que sobrar quando
não houver mais nome é a entrada. Se não sobrar nada, a lição era operacional daquele projeto:
ela pertence ao `CLAUDE.md` dele, e você não perdeu nada escrevendo-a lá.

Quando o exemplo concreto for indispensável para o leitor entender, **troque-o por um exemplo
neutro da mesma forma** — não apague o exemplo, despersonalize-o.

## A exceção, e ela é estreita

`skills/orchestrating-execute/references/orca-traps.md` documenta **uma ferramenta**: o
orquestrador e os CLIs de agente usados com ele. Ali, nome de comando, flag e mensagem de erro
*daquela ferramenta* são o assunto — é isso que torna o arquivo útil, e o `README.md` já avisa
que ele não serve fora dela.

A exceção cobre a ferramenta, **não o projeto**. Tabela, cliente, id e regra de negócio de um
repositório continuam fora, inclusive ali.

## Manutenção

- **Doc desatualizada é pior que doc ausente:** a próxima sessão segue a instrução errada com
  confiança. A edição entra no mesmo trabalho em que o aprendizado aconteceu, nunca "depois".
- **Achou conteúdo que viola esta regra enquanto mexia na seção?** Generalize junto. Não abra
  frente para varrer o repositório inteiro.
- **Nunca `git add -A`.** Estas skills são documentação viva e costumam ter mudança de mais de
  uma sessão na árvore ao mesmo tempo. Liste os caminhos.
- O que cada skill aceita receber, e o que ela recusa, está na tabela *Documentação viva* do
  [`README.md`](README.md).
