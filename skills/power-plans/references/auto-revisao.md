# Auto-revisão: a lista de julgamento

Referência da skill `power-plans`. Leia depois do pré-voo mecânico (`pre-voo.md`). O que o `plan-lint` e o verificador já conferem não precisa ser refeito de cabeça; o resto está aqui.

## Auto-revisão antes de entregar

**O que é mecânico saiu daqui.** Cobertura de requisito, caminho e linha que existem, célula
vazia, tarefa sem `Pronto quando` e arquivo com dois donos são conferidos pelo `plan-lint.py`; linha
citada que diz o que o plano afirma, contagem do falsificador e consumidor esquecido são do
verificador de contexto limpo (`pre-voo.md`). Rode os dois antes desta lista: ela é o que sobra
para o seu julgamento, e julgamento aprova o que ele mesmo escreveu.

Duas listas, e a primeira é a que faltava. Estrutura impecável em cima de fato falso continua
sendo plano falso.

**Pergunta de julgamento aprova o próprio texto; coluna vazia não.** Medido em 25/09/2026: dos
11 bloqueadores que a revisão externa achou num plano, **6 já eram cobertos por regras desta
skill** que o autor não aplicou (traçado, no-op, contrato mais restrito que o requisito). Mais
regra em prosa não teria pegado nenhum. O que pegou foram as verificações mecânicas: o `grep` de
FR e a tabela de afirmações de carga. Por isso, antes das listas: o plano tem as tabelas
obrigatórias preenchidas, sem célula vazia (afirmações de carga §0.1, ownership §3, traçado §3.1,
rastreabilidade §5.1)? Célula vazia é item aberto, não detalhe.

**Tamanho — o primeiro item, e é mecânico:** o plano mais a evidência que ele arquiva já passou do
tamanho do diff que ele planeja? Então ele está planejando mais de uma família, ou arquivando
sonda. Recorte antes de entregar (ver *Um pedido, uma família* e *Sonda não é evidência*).

**Verdade — cada item vale um `ls` ou uma query:**

- Todo fato do plano tem etiqueta `[MEDIDO:]`, `[LIDO:]` ou `[SUPOSTO:]`?
- Nenhum `[SUPOSTO:]` sustenta a implementação de uma tarefa? (se sustenta: medir agora, ou
  virar o primeiro passo da tarefa com "se der diferente, PARE e escale")
- Toda coluna, flag ou campo citado teve a **semântica conferida na linha real**, e não
  deduzida do nome? Campo derivado de mais de uma origem: uma conferência por origem?
- Para cada fix: com o código de hoje, ele muda alguma coisa — ou é **no-op que passa verde**?
- Todo caso que o plano promete que vai disparar um critério novo foi rodado contra esse
  critério?
- Todo caminho, comando e subcomando do plano existe? (inclusive os dos passos do coordenador)
  Todo arquivo NOVO cita o irmão existente e a configuração que o descobre?
- O que é emergente está na **watchlist**, com método de verificação, em vez de prometido?
- As **afirmações de carga** estão listadas, e cada uma passou por refutação TENTADA, não por
  citação que a confirma? A linha traz a **contagem do falsificador**, não a que confirma?
- Toda invariante que o plano promete preservar tem o caminho de exceção procurado, e os
  **testes existentes** daquele arquivo lidos?
- Para cada comportamento que o plano REMOVE: os emissores foram contados pelos três lados,
  chamadores da função, literal do texto **e** literal nos dados (template, configuração, seed)?
  Validação ou gate novo sobre saída existente contou como remoção, com a medição no histórico
  persistido? Os testes que hoje afirmam o comportamento têm dono e decisão na matriz?
- Toda tarefa que mexe em detector de texto tem a amostra de falso positivo medida e a lista de
  variações escrita no `Pronto quando`?
- Toda receita copiada de outro contexto teve a pré-condição dela conferida aqui?
- Todo passo novo inserido em pipeline existente foi posicionado depois de ler **até o fim** do
  fluxo, e não pelo nome da abstração?
- As linhas reais das entidades afetadas foram olhadas, e não só a contagem?

**Estrutura:**

- **Mecânico, e é o único desta lista que devolve número em vez de opinião:** todo `FR-n` da spec
  aparece em pelo menos uma tarefa, e toda tarefa tem `Pronto quando` copiado de um cenário — ou
  a marca explícita *"infra, sem FR"*?

  ```bash
  for n in $(grep -o 'FR-[0-9]\+' <spec> | sort -u -V); do
    printf '%-6s plano=%s\n' "$n" "$(grep -cw "$n" <plano>)"
  done
  ```

  **`-w` não é enfeite:** sem ele `FR-1` casa dentro de `FR-10`, e o requisito que ninguém citou
  aparece como coberto — o falso passe cai justamente no FR de número baixo, que costuma ser o
  comportamento central da feature.

  Os outros itens são de julgamento, e julgamento aprova o que ele mesmo escreveu. `plano=0` é um
  requisito que nenhum worker vai ver. Rode antes de entregar o plano, e de novo no preflight da
  execução.
- Toda tarefa tem nível, dono e dependências explícitas?
- Todo arquivo tocado aparece na matriz de ownership, com um dono só, e todo arquivo das
  células do traçado (§3.1) está na matriz?
- Toda célula da última coluna do traçado que descreve algo que uma pessoa vê (tela, painel,
  relatório) tem um arquivo e um dono, e não só uma frase?
- Nenhuma responsabilidade aparece em duas tarefas, mesmo sem colisão de arquivo?
- A ordem das ondas segue dependência de **comportamento**, com o que LIGA a mudança por
  último e reversível?
- Nenhum passo de validação tem item que você já sabe que vai falhar por causa de tarefa
  posterior?
- Todo contrato de que dois ou mais workers dependem está escrito literal e datado de antes da onda 1?
- Quando há coordenação assíncrona, o contrato inclui estados, identidade e confirmação
  entre donos? A tarefa indica peças reais/simuladas e quem executa a primeira prova integrada?
- Nenhum contrato é mais restrito que o FR que implementa? Se é, a decisão está na spec, com autoria?
- O gate é um por plano (ou um por produção, se o plano vai em etapas e diz por quê), antes do
  passo irreversível, sobre o candidato integrado, e nenhuma onda tem gate próprio?
- Todo par "não pode junto" tem a razão escrita?
- As ondas são trilhas, não camadas por profundidade? Toda trilha com mais de uma tarefa tem
  coordenador secundário, ou o §2.1 diz em uma linha por que não é seguro? Dependência cruzada
  resolvida por contrato, ponto de integração ou mudança de trilha, sem fundir trilhas inteiras?
- Com onda em worktree própria: há tabela de papéis, todo arquivo tocado por duas ondas está no
  "não pode junto" com o trecho de cada uma, e a ordem de integração está nos passos do
  coordenador?
- Algum worker precisa rodar comando que este projeto proíbe delegar?
- O caminho crítico está marcado?
- A estimativa está em tokens e tempo de relógio, sem "dias" ou "semanas", e o tempo saiu dos
  tokens de saída do caminho crítico, não do total?
- Sobrou placeholder de modelo, e nenhum modelo nomeado?
- A tabela de níveis tem a linha `Gate / Advisor` com `<MODELO_GATE>`, e o §7 traz o orçamento do
  advisor (uma consulta por veredito de gate)?
- A revisão externa da spec e do plano está FORA do grafo (nenhum `S0`, nenhum "bloqueia a onda
  1"), e o §0.1 registra a revisão feita ou "não solicitada"?
- Nenhuma decisão do usuário está em aberto (nem "pendente" com recomendação)? Toda decisão de
  negócio que sobrou, inclusive as que a revisão externa criou, foi perguntada e está registrada;
  autorização de execução (ação externa, escrita em dado) fica escrita como pedida na hora, não como
  decisão aberta. Ciclo sem `spec-interview` é onde isso escapa: ninguém aplicou o fechamento dela.
