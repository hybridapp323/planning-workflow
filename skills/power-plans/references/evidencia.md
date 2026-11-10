# Evidência antes de plano (Fases 0 e 0.5)

Referência da skill `power-plans`. Leia antes de escrever qualquer afirmação factual no plano: snapshot, etiqueta de procedência, afirmações de carga e o que não se decide no plano.

## Fase 0 — evidência antes de plano

O erro caro não é planejar errado. É planejar em cima de suposição que ninguém checou, porque o plano fica coerente, convincente e falso ao mesmo tempo.

1. Leia a spec inteira.
2. Abra os arquivos que ela promete tocar. Anote `arquivo:linha` de tudo que confirma ou contradiz o que a spec assume.
3. Consulte o estado real do dado sempre que a spec depender dele: schema, trigger, policy, e **contagem**. Contagem muda prioridade. "Vamos suportar X" é outra conversa quando X tem zero usuário hoje.
4. Escreva o snapshot de evidência.

**O snapshot** é um arquivo com o que foi lido, os `arquivo:linha` das descobertas, as queries rodadas e o resultado cru delas. Guarde fora do repositório (scratchpad da sessão) a menos que o projeto tenha lugar próprio. Ele paga duas vezes: fecha as lacunas agora, e é o que se entrega ao revisor externo depois, se houver revisão.

**Sonda não é evidência; o resultado reproduzível é.** Script exploratório (uma consulta de uma
vez, um teste de hipótese, a versão 2 e 3 da mesma sonda) fica no scratchpad e não entra no
repositório. Entra como evidência só o que outra pessoa consegue refazer: a consulta ou a receita,
os parâmetros, o SHA e o resultado cru; ou o caso mínimo promovido a teste. O plano cita o
resultado, não o script. Medido: um ciclo arquivou dezenas de sondas descartáveis como "evidência",
e foi a maior parte dos 127 arquivos dele.

**Regra dura:** um bloqueador que você não conseguiu reproduzir no código ou no dado não é bloqueador, é hipótese. Escreva-o como hipótese, com o que faltou para confirmar.

**Esta fase cobre o DIAGNÓSTICO e para aí.** Os fatos que a sua solução vai inventar ainda não
existem agora. Eles têm fase própria, logo abaixo, e ignorá-la foi o que produziu três
afirmações falsas num plano cujo snapshot de evidência tinha 17 KB.

### Validar a spec, e consertá-la se precisar

A spec saiu de uma entrevista com as decisões fechadas, mas quem a escreveu não estava tentando paralelizar. Três lacunas só aparecem agora, e as três quebram execução paralela:

- **Contratos ausentes.** A spec descreve comportamento mas não fixa formato. Dois workers vão inventar dois formatos.
- **Matriz de consumidores ausente, e ela é BIDIRECIONAL.** Quem mais **lê** o dado, o campo ou o arquivo que essa feature muda? Um resolver, um job agendado, uma exportação, uma tela secundária. E, na direção que quase sempre falta: quem mais **escreve ou emite** o comportamento que a feature altera? Feature nova morre num consumidor esquecido; feature que REMOVE comportamento morre num emissor esquecido.
- **Decisões sem o que foi descartado.** Sem isso, o primeiro worker que achar a alternativa "melhor" vai implementá-la.

Se faltar, conserte a spec, e diga ao usuário exatamente o que você mudou nela. Planejar em cima de spec furada só adia o furo.

## Fase 0.5 — a evidência da SOLUÇÃO, não só a do problema

A Fase 0 valida **a spec**: o que o problema é, onde ele mora, quanto dado ele afeta. Isso é
metade. A outra metade nasce depois, quando você desenha a correção, e **não passa por
evidência nenhuma** se você não voltar de propósito.

Medido num ciclo de auditoria de turno de atendimento: o snapshot de evidência tinha 17 KB, media o
problema ao segundo, citava `arquivo:linha` e contava frequência em produção. Ainda assim o
plano saiu com **três afirmações falsas**, e as três eram do lado da *prescrição*:

| afirmação do plano | realidade | custo |
|---|---|---|
| "corte no `created_at` da tabela de auditoria" | é quando o turno **fechou**, ~13 s DEPOIS do inbound a recuperar. O corte cru excluiria exatamente a mensagem alvo | **o fix seria um no-op, e passaria verde** |
| "o registro auditado aparece na flag de teto impossível" | `max=20000` é plausível e não bate em nenhum dos 3 critérios congelados | um worker gastou um ciclo de dispatch para escalar |
| `node scripts/<runner>.mjs` | o script mora noutro diretório, dentro da pasta de uma skill do projeto | comando quebrado no passo do coordenador |

Nenhuma das três estava no snapshot — porque nenhuma existia quando a Fase 0 rodou. A regra
que faltava é esta:

> **Evidência que para no diagnóstico não protege a prescrição.** Todo fato NOVO que a
> solução inventa entra na mesma disciplina do fato que descreveu o problema.

### Etiqueta de procedência: obrigatória em todo fato do plano

Toda afirmação factual do plano carrega uma das três, literal:

```
[MEDIDO: <comando ou query> → <resultado cru>]      verificado agora, com o resultado à vista
[LIDO: caminho/arquivo.ts:120-134]                  confirmado no código, com a linha
[SUPOSTO: <o que provaria que é falso>]             NÃO verificado, e traz o próprio falsificador
```

**Regra dura:** um fato de que a implementação de uma tarefa **depende** não pode ficar
`[SUPOSTO]`. Ou você mede antes de congelar o plano, ou o primeiro passo daquela tarefa é
medir, escrito assim: *"se der diferente, PARE e escale — não improvise"*. Fato decorativo
pode ser suposto; fato que sustenta um fix, não.

Isso é barato. As três falhas acima custavam um `ls` e duas queries.

**Fato que sustenta uma DECISÃO que você leva ao usuário não pode ser adiado para o primeiro
passo da tarefa: meça antes de perguntar.** O "PARE e escale" protege a implementação, não a
decisão. Se a premissa cai na execução, o usuário decidiu em cima de um fato falso, a tarefa trava
esperando uma decisão nova e a rodada de perguntas se repete. O sintoma: você escreve a
recomendação ao usuário e, no plano, a mesma premissa aparece como "primeiro passo: medir".
Medido em 26/09/2026: uma recomendação ("o estado pendente deriva de uma flag que o registro já
tem") foi aprovada com a premissa "o registro do caso real tem essa flag" deixada como primeiro
passo da tarefa. A revisão externa rodou a consulta por turno: a flag era falsa em todos os turnos
do caso real. A decisão caiu, o usuário decidiu de novo e a tarefa ficou bloqueada até lá.
Custo da medição que faltou: um `select`.

**Norma citada não é fato verificado.** Quando o plano invoca uma regra da documentação do
projeto ("o checklist manda X", "a convenção aqui é Y"), `[LIDO: checklist.md:44]` prova que o
**documento** diz — não que o **código** faz. Documentação envelhece; o código é a verdade. Norma
que decide uma tarefa vira `[MEDIDO:]` contra o repositório antes de entrar no plano.

Medido em 2026-09-03: um plano citou a regra "não use chave estrangeira para a tabela de usuários
do auth", vinda do checklist de segurança do próprio projeto. A medição no schema devolveu **7 de
7 tabelas comparáveis fazendo exatamente isso, e nenhuma fazendo o contrário**. Obedecer o
documento teria feito da tabela nova a única exceção do banco. Quem estava errado era o documento,
e ele foi corrigido no mesmo trabalho. Custo da verificação: uma query.

### A carga do plano: liste o que ele SUSTENTA, e tente derrubar

A etiqueta acima prova que você **olhou**. Ela não prova que você olhou o caminho inteiro, e
é aí que mora o furo caro: a afirmação que o desenho inteiro apoia em cima.

Antes de congelar, escreva a lista das **afirmações de carga**: as que, se falsas, derrubam
uma decisão estrutural do plano. Elas quase sempre têm forma negativa ou de invariante:

- "isso continua garantido mesmo com a mudança";
- "não existe caminho que faça X";
- "esse comportamento só nasce em Y";
- "desativar Z é seguro porque Z é a única porta".

> **Para uma afirmação de carga, a evidência é uma REFUTAÇÃO TENTADA, não uma citação.**
> Citar a linha que te dá razão é confirmação; procurar a linha que te derruba é verificação.

O método, três passos e nenhum é caro:

1. **Escreva o falsificador em uma frase.** "Isto seria falso se existisse um caminho que
   satisfaça a checagem sem o dado real."
2. **Busque o falsificador, não a confirmação.** Leia a função auxiliar de que a checagem
   depende, não só a linha que a enuncia. Faça `grep` pelo caminho de exceção, pelo
   relaxamento, pelo bypass, pelo `||`. Leia os **testes existentes** daquele arquivo: um
   teste que trava o comportamento permissivo é a prova pronta de que sua invariante não vale.
3. **Puxe a linha real da entidade afetada**, não o agregado. Contagem responde "quantos"; a
   sua afirmação normalmente é sobre "este". Se o plano toca N registros, olhe os N quando N é
   pequeno, e uma amostra nomeada quando não é.

Medido em 2026-08-26, num ciclo de configuração de cliente: o plano afirmava *"o envio
continua exigindo o dado de identidade em qualquer etapa"*, com etiqueta `[LIDO:]` apontando
para o trecho certo da função de política, e a citação estava correta.
A afirmação, não: uma função auxiliar noventa linhas acima aceitava o nome como presente
quando um marcador persistido dizia "esse campo foi pulado", e **um teste do próprio
repositório travava esse comportamento**. Pior, o único registro afetado **já tinha o marcador
gravado**, de um teste feito dias antes. Três verificações de segundos derrubariam a
afirmação: ler o auxiliar, ler o teste vizinho, e dar um `select` na linha. Nenhuma foi feita
porque a afirmação parecia confirmada. Quem achou foi a revisão externa.

> **A linha só fecha com a CONTAGEM do falsificador, sobre o universo inteiro da afirmação.**
> Escreva a consulta ou o `grep` que conta o caso que derruba a afirmação, e o número que ela
> devolveu, mesmo que seja zero. Contagem que confirma a afirmação mede outra coisa e não fecha
> a linha. E amostra escolhida **porque mostrava o defeito** (os registros que a regra antiga
> gravou errado) não refuta um "nunca": o contraexemplo costuma estar nos casos da mesma forma
> em que a regra antiga acertou por outro caminho, e que por isso ficaram fora da amostra.
> Conte também nesse resto.

Medido em 2026-09-12: uma afirmação de carga dizia *"os vínculos persistidos cobrem a
duplicação entre dois provedores"*, o falsificador estava escrito na frase certa (*"vínculo
não existe"*), e a coluna de resultado trazia `[MEDIDO: 149 linhas vinculadas]`. A consulta
que contava o falsificador tinha a mesma forma, com um `not exists` a mais, e devolvia 32
pares sem vínculo em 90 dias. Ninguém a rodou porque a tabela aceitava qualquer `[MEDIDO:]`.
Quem a rodou foi a revisão externa, e virou bloqueador.

Medido em 2026-10-09: a afirmação *"essa forma de fala, sob aquela pergunta, nunca é
orçamento"* foi contada nos 24 registros em que o defeito tinha gravado um teto: zero
contraexemplos. A revisão externa procurou entre as respostas da mesma forma que **não**
gravaram teto e achou um; a regra que o usuário tinha aprovado erraria exatamente esse caso, e
ele teve de decidir de novo antes de qualquer código.

### As classes que morderam de verdade: confira estas por nome

Cada uma custou um ciclo, uma rodada de gate ou um run pago. O mecanismo e a medição de cada uma
estão em `references/classes-de-erro.md`: **leia a classe inteira quando ela se aplicar** ao plano.

1. **Semântica de coluna, flag ou campo:** nunca infira pelo nome; abra a linha real e compare com
   um caso conhecido.
2. **O fix é no-op?** Com o código de hoje, a mudança altera alguma coisa? No-op passa verde.
3. **O caso prometido dispara o critério novo?** Rode o critério contra o caso agora.
4. **Caminho, comando e nome existem?** Arquivo novo cita o irmão existente; `--help` inteiro,
   nunca recortado.
5. **Invariante que você promete preservar:** caminho de exceção procurado e testes existentes lidos;
   se é isolamento, as escritas que mudam o pertencimento também.
6. **Emissores do comportamento que você REMOVE:** chamadores, literal no código e literal nos
   dados; gate novo sobre saída existente é remoção.
7. **Receita copiada de outro contexto:** a pré-condição dela vale aqui?
8. **Passo novo em pipeline existente:** leia do ponto de inserção até o fim do fluxo.
9. **Tarefa que adia, segura ou bloqueia uma ação:** o ponto único antes dos efeitos; ação com
   vários executores lê a mesma trava com a mesma entrada.
10. **Tarefa que substitui um módulo:** os gatilhos do módulo antigo entram na matriz.
11. **Peça nova dentro de um hospedeiro existente:** ela herda o estado (e os defeitos) dele.
12. **"Importar a mesma função" não é paridade** quando a entrada é preparada no chamador.
13. **Teste do consumidor com campo que o produtor real não emite:** a fixture vem do produtor.
    Vale também quando o produtor é a rodada anterior do próprio sistema: cenário de várias
    rodadas prova-se pela camada que grava e relê o estado entre elas.
14. **Remover evento ou linha de log:** procure leitores por tempo (`desc`, `limit 1`, `max`).
15. **Escritor único prometido:** inventário dos sites de escrita de hoje, incluindo gatilhos e jobs.
16. **Linha nova em template, seed ou catálogo global:** o provisionamento de tenant a copia;
    unicidade pode morar num índice.
17. **Detector de texto:** falso positivo medido em amostra real, falso negativo com as frases
    vizinhas, lista de variações no `Pronto quando`.
18. **"N itens acham par" não é "N vínculos" quando o alvo é único:** conte alvos distintos, do lado
    da restrição (índice único, reserva no chamador).
19. **Grant explícito não tira privilégio padrão herdado:** meça o privilégio efetivo depois de criar
    o objeto, não o texto do `grant`.

### O que NÃO dá para decidir no plano — diga isso em vez de fingir

Rigor não é prometer que o plano prevê tudo; é separar o decidível do emergente e escrever a
fronteira. Não são planejáveis, e o plano deve dizê-lo:

- **defeito que depende de uma escolha do modelo** (a LLM decide transferir, ou responde em
  prosa em vez de lista). Não é reproduzível sob demanda: a prova é teste determinístico, e a
  verificação é telemetria de produção;
- **interação entre peças que ainda não existem** — um guard novo cruzando com outro guard só
  se avalia depois de escritos. É para isso que serve o gate adversarial, não o plano;
- **corrida de tempo real** que o harness de teste não reproduz.

Escreva estes como **watchlist do plano**, com o método de verificação que os cobre. Um plano
que promete cobrir o emergente vira álibi; um que declara a fronteira vira mapa.

### Prova ponta a ponta: não executado é hipótese, e só conta com a causa inspecionada

Cenário escrito e não executado não é cobertura: roda antes do gate, ou entra `[SUPOSTO:]` com o
passo "rodar ANTES de considerar coberto". Vermelho e verde só contam com a causa inspecionada
(a asserção do defeito, não setup, fraseado ou reparo pelo modelo). Mecanismo e medições:
`references/classes-de-erro.md`, seções finais.
