# Conferência do construtor

Referência da skill `spec-interview` (Fase 4). Leia quando a spec estiver escrita e auto-revisada,
antes de invocar `power-plans`. Só no caminho arquitetural: a limitada não tem arquivo de spec.

## Por que existe

A auto-revisão é feita por quem escreveu a spec, com a conversa inteira na cabeça: o que ficou só na
conversa parece estar no documento. Quem vai planejar lê só o documento. A decisão que faltou
aparece então no pior lugar: no plano, como suposição, ou na implementação, como escolha do agente.

A conferência põe um leitor sem a conversa entre a spec e o plano. Ele não julga o desenho nem
melhora o texto: lista onde teria de chutar. O que for decisão de produto volta ao usuário **antes**
do plano, que é onde custa uma mensagem, e não uma onda de retrabalho.

Medido em 11/2026 em duas specs já escritas e auto-revisadas (191 e 347 linhas), com o brief abaixo,
modelo intermediário, uma rodada cada: 6 e 4 perguntas, das quais o leitor marcou 4 e 2 como de
produto. Conferidas contra a spec, 4 dessas 6 estavam de fato em aberto (por exemplo: o que fazer
quando a medição cai entre a meta e o limite que a refuta; quem reverte uma configuração fora da
janela de observação); as outras duas a spec deixava para o plano ou respondia em parte. Custo:
perto de 110 mil tokens e menos de um minuto por spec, fora a triagem.

## Como rodar

Um subagente do harness, de **contexto limpo** (não um fork da sua sessão: ele não pode herdar a
conversa), em modelo intermediário: o trabalho é ler e conferir, não desenhar. Somente leitura.

O brief, para copiar:

```
Você vai planejar a implementação do que esta spec descreve, e não vai poder falar com quem a
escreveu nem com quem pediu. Somente leitura: não edite arquivo e não rode comando que altere
estado. Spec: <caminho>. Raiz do projeto: <caminho>.

Leia a spec inteira. Onde ela citar código, dado ou documento do projeto, abra e confira: o que o
projeto responde não é pergunta.

Liste só as perguntas que você ainda precisaria ver respondidas para planejar bem: os pontos em
que teria de chutar, e em que o chute errado mudaria o que é construído. Para cada uma:
- a pergunta;
- a seção ou o requisito da spec a que se refere;
- por que a resposta muda o plano;
- onde você procurou a resposta e não achou;
- o tipo: PRODUTO (muda o que o usuário vê, o dado gravado ou o custo) ou TÉCNICA (muda só o
  como, e um construtor sensato poderia decidir).

Ordene por importância, no máximo dez. Não liste: o que a spec deixa explicitamente para quem
constrói, o que você decidiria sem risco, o que o projeto responde, reparo de redação, sugestão
de melhoria do desenho.

Se não sobrar nada importante, responda só: "nada importante em aberto".
```

### Spec grande: um leitor por trilha

O brief foi medido em specs de até uns 350 linhas. Acima disso, ou quando a spec se divide em
trilhas que ela mesma chama de independentes, despache **um leitor por trilha**, em paralelo, cada
um com o mesmo brief mais uma linha: *"leia a spec inteira, mas liste só as perguntas da trilha
<X>"*. O teto de dez perguntas vale por leitor. Continua sendo uma rodada só: as perguntas de
produto de todos os leitores voltam ao usuário juntas.

Medido em 11/2026: uma spec de 700 linhas, cinco trilhas e cerca de 30 requisitos, com um leitor
só, devolveu 4 perguntas, nenhuma sobre o requisito que depois custou três correções em cadeia. A
atenção de um leitor se reparte pelo documento inteiro; o teto de dez perguntas, também.

## O que fazer com a resposta

Confira cada pergunta antes de aceitar, como faria com um revisor: o leitor pode ter deixado de
abrir o arquivo que respondia. O tipo que ele marcou é palpite; quem classifica é você, pela mesma
régua da entrevista. Depois separe em três:

| A pergunta | O que fazer |
| --- | --- |
| Já estava respondida, na conversa ou no projeto | A resposta entra na spec, no lugar onde o leitor procurou. Se ele não achou, o planejador também não acharia |
| Técnica | Decida, e registre na tabela de decisões como "assumida por mim", com o porquê |
| De produto | Volta ao usuário **numa rodada única**, no formato das rodadas, com a sua recomendação em cada pergunta. O plano espera a resposta |

Atualize a spec com as respostas e siga para `power-plans`. **É a única rodada que a conferência
produz**: não rode o leitor de novo sobre a spec corrigida, e não transforme a conferência em laço.

Sem ferramenta de subagente, leia você mesmo a spec como esse construtor, do começo, sem consultar
a conversa.

## Registro

Anote na tabela de decisões da spec a linha da conferência (data, quantas perguntas, quantas de
produto) e, no `## Registro do ciclo` do plano, a chave `spec.conferencia`.

## O que ela não pega

Decisão que nem a spec nem o leitor imaginaram: isso é da varredura de cobertura, na entrevista. E
defeito de plano (ordem, contrato entre tarefas, prova que não prova): isso é do pré-voo de
`power-plans`.

---

*Adaptada da "builder check" da skill `brainstorming` do plugin
[superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent), v7.*
