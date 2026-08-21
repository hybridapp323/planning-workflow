---
name: orchestrating-plans
description: >-
  Executa um plano de implementação multi-agente já escrito: pergunta ao usuário
  qual modelo vai em cada nível de complexidade, roda os passos que só o
  coordenador pode rodar, sobe os workers onda por onda respeitando o grafo de
  dependências, e para nos gates antes de qualquer passo irreversível. USE
  SEMPRE que existir um plano pronto e o usuário disser "vamos executar",
  "executa o plano", "sobe os workers", "dispara os agentes", "começa a onda 1",
  "roda isso em paralelo", "manda pros agentes", "toca o plano X". Usa a skill
  `orchestration` do Orca para a mecânica de task, dispatch e espera, e
  acrescenta o que é específico de executar um plano: o portão de atribuição de
  modelo, o laço de ondas, o que nunca se delega, e as armadilhas já pagas. Se o
  plano ainda não existe, a skill é `writing-plans`, não esta.
---

# Executar um plano multi-agente

## Preflight

Leia o plano inteiro antes de qualquer comando. Ele precisa ter, no mínimo:

- nível de complexidade em cada tarefa;
- matriz de ownership de arquivo;
- contratos congelados escritos literal;
- grafo com dependências e passos do coordenador.

Faltando qualquer um, **pare e volte para `writing-plans`**. Executar um plano sem ownership é combinar colisão; sem contrato congelado é combinar divergência. Custa menos consertar o documento agora.

Confirme também que a árvore está limpa do que interessa, e que você sabe quais arquivos modificados **não** são deste trabalho. Sessões paralelas deixam lixo, e ele acaba num commit errado.

## Portão de atribuição de modelo

**Antes de criar qualquer terminal**, pergunte ao usuário qual modelo vai em cada nível:

| Nível | Modelo |
| --- | --- |
| Complexa | ? |
| Média | ? |
| Baixa | ? |

O plano vem com `<MODELO_COMPLEXA>` / `<MODELO_MEDIA>` / `<MODELO_BAIXA>` justamente para essa decisão ser tomada aqui, com o custo e a disponibilidade do dia na mesa. Nunca assuma, nunca herde do plano anterior, e não comece a onda 1 com um nível ainda em aberto.

Se o usuário atribuir um modelo por tarefa em vez de por nível, aceite: a granularidade é dele.

## Mecânica: use a skill `orchestration`

Não redocumente o Orca. Para criar run, criar task com dependência, despachar com preâmbulo injetado e esperar `worker_done` / `escalation` / `decision_gate`, siga a skill `orchestration`. Esta aqui só acrescenta o que é específico de executar um plano.

Sequência por worker, na ordem:

1. `run-create` uma vez, no começo. Sem run vinculada, `task-list` falha.
2. `task-create` para cada tarefa, com `--deps` refletindo o grafo do plano. O grafo vira estado, não fica só no documento.
3. `terminal create`, com o flag de bypass de permissão **dentro** da string de `--command`.
4. `terminal wait --for tui-idle` antes de despachar. Terminal que ainda está subindo engole o dispatch.
5. `dispatch --inject` com o preâmbulo abaixo.
6. `check --wait --types worker_done,escalation,decision_gate`.

Armadilhas medidas, que custam tempo quando descobertas na marra: `references/orca-traps.md`. Leia antes da primeira onda.

**Sem Orca disponível**, o plano continua válido: é um grafo com níveis, donos e contratos. Execute com o mecanismo de subagente que houver, mantendo ownership, ordem e gates. O que não se pode perder é o grafo, não a ferramenta.

## O preâmbulo de todo dispatch

Todo worker recebe, sem exceção:

- **Onde está a verdade:** caminho da spec e do plano, e a instrução de ler os dois.
- **Sua tarefa, pelo identificador:** "você é a T5, e só a T5".
- **Seus arquivos, listados.** Mais a frase: nenhum arquivo fora desta lista, nem para "corrigir de passagem".
- **Os contratos que ele consome**, colados literal no dispatch, não por referência. Worker não deve depender de achar a seção certa.
- **O que este projeto proíbe delegar.** Tipicamente git. Diga com essas palavras: não rode comando de git, quem commita é o coordenador.
- **Escalar em vez de improvisar.** Se a tarefa exigir sair do escopo, mudar contrato, ou tocar arquivo de outro, ele manda `escalation` e para. Um worker que improvisa custa mais que um worker que espera.
- **Pronto quando:** o critério verificável da tarefa, copiado do plano.

Worker que recebe contrato por referência e não por valor inventa o contrato. Cole.

## O laço de ondas

Para cada onda:

1. Suba todos os workers da onda **no mesmo momento**. Onda serializada é onda desperdiçada.
2. Espere as conclusões. Trate `escalation` na hora: worker escalando está parado.
3. Rode os passos do coordenador daquela onda, você mesmo.
4. Verifique antes de abrir a próxima. Onda seguinte que começa em cima de passo do coordenador não confirmado propaga o erro para todos os workers de uma vez.

Um `check --wait` que volta só com keepalive e sai não é falha: é ponto de checagem. Confirme que o worker está vivo e rearme a espera.

## Gates

Um gate tem `worker_done` como qualquer tarefa, mas o que ele autoriza é um passo **seu**, não a próxima onda.

- Gate aprovou: rode o passo do coordenador que ele guardava.
- Gate reprovou: **não rode**. Despache a correção como tarefa nova, com dono, e passe pelo gate de novo.

Nunca rode o passo irreversível "enquanto o gate roda". O ganho é minutos; a perda é migration aplicada em produção sem `git revert`, ou deploy que republica módulo compartilhado de uma branch atrasada.

Revisão que volta com achados **não autoriza o coordenador a corrigir por conta própria**. Sintetize, decida quem é o dono da correção, e despache. Se a decisão for de negócio e não técnica, leve ao usuário com resumo e recomendação.

## Passos que são sempre seus

Descubra no `CLAUDE.md` / `AGENTS.md` do projeto o que não se delega. Quase sempre inclui:

- git: `add` com caminhos explícitos, `commit`, `push`;
- aplicar mudança de schema;
- deploy de função ou serviço;
- publicação para usuário.

Estes são os passos que definem onde as ondas quebram. Se você se pegar delegando um deles, o grafo do plano estava errado, não o projeto.

Ao commitar, estage caminho por caminho e confira o que está estagiado. Em checkout compartilhado por sessões paralelas, `add -A` varre trabalho alheio para dentro do seu commit, e ninguém acha depois pelo histórico.

## Fecho

1. Rode lint e testes do projeto, você mesmo.
2. Commite com caminhos explícitos.
3. Responda os portões de entrega do projeto, sem esperar o usuário perguntar. Se o projeto entrega por bundle ou build nativo, diga sim ou não para cada um.
4. Atualize a documentação que este projeto exige atualizar no mesmo commit.
5. Feche as tasks no Orca com o resultado real. Task que fica aberta some do radar e reaparece como confusão na próxima sessão.
6. Relate ao usuário o que ficou de fora, se ficou, e por quê.

Se alguma armadilha nova aparecer durante a execução, acrescente-a a `references/orca-traps.md` no mesmo trabalho. É a única forma de a próxima execução não pagar de novo.
