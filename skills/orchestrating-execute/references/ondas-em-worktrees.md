# Ondas paralelas em worktrees

Referência da skill `orchestrating-execute`. Leia só quando o plano põe ondas em worktrees separadas, com coordenador de onda.

### Ondas paralelas em worktrees: coordenador de onda e integração

Quando o plano põe ondas paralelas em worktrees separadas (`power-plans`, Fase 2), você é o
coordenador **principal**: cria as worktrees em C0, toca a sua onda na árvore atual e integra as
outras. Cada outra onda tem um coordenador de onda, uma sessão de agente aberta na worktree dela,
com o modelo da linha `Coordenador de onda`.

Plano que chega com ondas em camadas por profundidade, sem a linha "Ondas paralelas" no §2.1, e
com trilhas que o grafo mostra sem dependência entre si: antes de C0, mostre as trilhas ao usuário
e proponha um coordenador secundário por trilha (`power-plans`, *Ondas são trilhas, não camadas*).
Não execute as camadas em silêncio.

**O brief do coordenador de onda** leva o plano, a onda dele, a tabela de papéis copiada do plano,
a atribuição de modelos já decidida (ele não roda o portão de atribuição de novo) e esta skill: ele roda o laço de ondas para a própria onda, com o mesmo aceite e o mesmo fechamento
de terminais. Commita só no branch dele; não publica nada (homologação inclusive), não aplica
migração, não escreve em dado e não integra na branch principal.

**A entrega, pelo coordenador de onda:**

1. Rebase sobre a branch principal **commitada**, no SHA que você indicar (trabalho seu não
   commitado não existe para a onda), resolvendo os conflitos ele mesmo: quem conhece o código da
   onda resolve. Entre indicar o SHA e integrar, você não commita na branch principal.
2. Suíte por nome de novo, contra a base desse SHA.
3. A você: branch, SHA **pós-rebase** (o rebase reescreve os SHAs), tarefas aceitas com a prova de
   neutralização, diferença da suíte por nome e o que ficou de fora. Canal: o `worker_done` dele,
   se foi você quem o despachou pelo orquestrador; um arquivo de entrega na pasta do plano, se o
   usuário o abriu à mão.

**A integração, por você, uma onda por vez na ordem do plano:** `git merge --ff-only <branch>`.
Recusou, a branch principal andou depois do rebase: devolva à onda para refazer, não concilie
você. Depois de cada integração, suíte por nome e verificação de tipos no integrado. O gate não é
por integração nem por onda, e o coordenador de onda nunca roda gate: ele roda sobre o candidato
integrado, antes de cada ida à produção. Padrão: integrar todas as ondas paralelas e ir uma vez.
Produção em etapas (uma onda corrige algo ao vivo e não pode esperar as outras) é decisão do plano,
com um gate por produção. No fecho, `git worktree remove` e `git branch -d`, que recusa branch não
integrado.

**Sem PR por padrão.** As worktrees compartilham o repositório, e o branch da onda é visível para
você sem push. PR só quando o coordenador de onda roda em outra máquina, quando a onda toca
frontend e o preview por branch serve à validação do usuário, ou quando o usuário quer revisar no
forge; mesmo aí quem junta é você, depois da suíte. Medido em 26/09/2026, num plano que mandava
cada onda abrir PR: os dois branches de onda tinham 2 e 3 commits, nenhum push, e já apareciam
para o principal num `git log`; o repositório não tinha CI, e nos 8 PRs anteriores o único check era
o preview do host (7) ou nenhum (1); o host publicava a branch principal sozinho, então o botão de merge seria deploy
de produção sem a suíte integrada, e o squash apagaria o commit por tarefa.
