# planning-workflow

Skills para o ciclo de vida de uma feature **grande**: da ideia com escopo aberto até a execução
por vários agentes, e a depuração de quando algo quebra no caminho.

A primeira regra do plugin é quando **não** usá-lo. Mudança delimitada, que o usuário já descreveu
por inteiro e que se desfaz com um revert, se faz direto: sem spec, sem arquivo de plano, sem
revisão externa. O ciclo completo existe para feature nova, subsistema novo, escopo em aberto,
trabalho de vários donos e passo irreversível.

A segunda: **o tamanho da obra corta documento, nunca pergunta.** Decisão de produto em aberto
(muda o que o usuário vê, o dado gravado ou o custo) vira pergunta em qualquer tamanho de pedido;
decisão técnica o agente toma e avisa.

## As quatro skills

- **`spec-interview`**: entrevista em rodadas até a ideia fechar. Pergunta a fronteira inteira por
  rodada com a recomendação em cada pergunta, traz o que o usuário não pensou, busca sozinha os
  fatos que estão no código ou no banco, e nada escreve enquanto sobrar decisão de produto em
  aberto. O tamanho da obra decide só o documento (sonda, direta, limitada, arquitetural): obra
  pequena termina num design curto no chat, obra grande numa spec escrita. Feature com tela só fecha com referência visual exercitada
  pelo usuário, decisões visuais fechadas ou dispensa escrita.
- **`power-plans`**: o plano de implementação, com o aparato na medida do risco (direto, mínimo,
  parcial, completo): evidência antes de plano, um dono por arquivo, contratos congelados, grafo
  de ondas e um gate antes do passo irreversível. Antes de mostrar o plano a alguém, roda o
  **pré-voo**: um lint mecânico e um verificador de contexto limpo. Depois para e pergunta:
  revisão externa ou commit e push.
- **`orchestrating-execute`**: executa o plano. Portão de atribuição de modelo, laço de ondas com
  aceite do coordenador por tarefa, comparação de tela com a referência aprovada como trava da
  integração, um gate por plano em rodada única, advisor de rumo com registro. Usa a skill
  `orchestration` do Orca para a mecânica.
- **`systematic-debugging`**: causa raiz antes de conserto, em quatro fases.

São genéricas de propósito. As regras de cada repositório saem do `CLAUDE.md` / `AGENTS.md` dele e
de um `.claude/plan-profile.md` opcional.

```
pedido ─┬─ delimitado ───────────────────────────────→ faça direto
        ├─ bug ──────────────────────────────────────→ systematic-debugging
        └─ grande ou com escopo aberto
              → spec-interview → spec → power-plans → pré-voo → PARA: revisão externa ou commit?
                                                                      |
                                              orchestrating-execute  ←─ só a pedido explícito
```

## Como as skills são escritas

Cada `SKILL.md` é um **roteiro curto**, com uma linha por regra e um ponteiro para o detalhe em
`references/`, lido na hora de usar. O teto é de 19 mil caracteres por `SKILL.md`, e não é
estético: depois de uma compactação de contexto, o harness devolve só o começo de cada skill. O
que passa do teto some justamente nas sessões longas, que são as de execução.

Três scripts sustentam isso:

| Script | Faz |
| --- | --- |
| `skills/power-plans/scripts/plan-lint.py` | Confere o plano contra a spec e contra o repositório: requisito sem tarefa, caminho e linha que não existem, tarefa sem critério de pronto, célula vazia, arquivo com dois donos |
| `scripts/check-skills.sh` | Recusa `SKILL.md` acima do teto ou que cite arquivo inexistente. Roda no `pre-commit` (`.githooks/`) |
| `scripts/sync-harnesses.sh` | Instala as skills em cada CLI de agente da máquina e mantém todos atualizados |

Regra de manutenção que vem da medição: **verificação antes de prosa.** Em três meses, a skill de
plano dobrou de tamanho acrescentando lições em texto, e o número de bloqueadores por revisão
externa não caiu. Defeito que uma checagem mecânica pegaria vira checagem.

## Instalar

### Claude Code

```
/plugin marketplace add hybridapp323/planning-workflow
/plugin install planning-workflow@planning-workflow
```

O repositório é o próprio marketplace. Marketplace de terceiro nasce sem atualização automática:
ligue em `/plugin` → Marketplaces → `planning-workflow` → Enable auto-update. O `plugin.json` não
tem `version` de propósito: a versão é o commit, e todo push chega às instalações.

### Todos os CLIs de agente da máquina

```bash
git clone https://github.com/hybridapp323/planning-workflow.git
planning-workflow/scripts/sync-harnesses.sh            # instala nos CLIs detectados
planning-workflow/scripts/sync-harnesses.sh --check    # mostra o estado de cada um
planning-workflow/scripts/sync-harnesses.sh --install-timer   # puxa o repositório e sincroniza sozinho
```

Cada CLI descobre skills de um jeito, e o script trata cada um pelo dele:

| CLI | Como recebe | Atualização |
| --- | --- | --- |
| Claude Code | plugin do marketplace (skills e gancho de roteamento) | `plugin marketplace update` + `plugin update` |
| Codex | plugin do marketplace, com cache git próprio | `marketplace upgrade` e avanço do cache por fast-forward |
| Grok | lê o plugin do Claude Code | junto com o Claude Code |
| OpenCode, Muse, Antigravity | um link por skill, da pasta de skills do CLI para o clone | imediata: o link aponta para o clone |

Sessão já aberta não vê a mudança: vale a partir da próxima. O `--install-timer` agenda
`--pull` a cada 10 minutos no crontab do usuário, para a mudança feita em outra máquina chegar.

Em um agente que o script não conhece: copie `skills/<nome>/` inteira (com `references/` e
`scripts/`) para onde ele lê instruções. Se ele não escolhe skill pela `description`, cole
`hooks/session-start.md` no prompt de sistema. `orchestrating-execute` depende do Orca para a
mecânica; sem ele, o plano continua válido e se executa com o mecanismo de subagente que houver.

## O gancho de roteamento

`hooks/hooks.json` injeta `hooks/session-start.md` no começo de cada sessão do Claude Code. São
poucas linhas: começar pelo tamanho do pedido, a tabela pedido → caminho, e os sinais de que o
agente está inflando ou encolhendo o processo.

## Medir se o processo melhora

Todo plano termina com um bloco `## Registro do ciclo`
(`skills/power-plans/references/registro-do-ciclo.md`): escala, achados do pré-voo, bloqueadores
da revisão por custo, emendas de contrato, veredito do gate, comparação de tela, rodadas de
correção depois da entrega. É o que permite comparar antes e depois de uma mudança nestas skills.

## Documentação viva

As skills melhoram com o uso, e o critério de entrada é um só: **custou, e vai custar de novo.**

Quem edita é o próprio agente, de dentro do projeto em que está trabalhando:

1. Melhora a seção que já cobre o assunto antes de acrescentar. Regra nova entra em uma linha no
   roteiro; o caso medido vai para `references/`.
2. Entra o conceito, nunca o caso de um repositório: o teste está no [`AGENTS.md`](AGENTS.md).
3. Escreve no clone git do plugin, roda `scripts/check-skills.sh`, **commita só os caminhos que
   mudou e dá push na branch principal, no mesmo trabalho**, roda `scripts/sync-harnesses.sh` e
   diz ao usuário o commit em uma linha.

O histórico do git é o backup: se uma mudança piorar o processo, `git revert` no commit dela.

## Licença e créditos

MIT, ver [`LICENSE`](LICENSE). `spec-interview` e `systematic-debugging` adaptam material do plugin
[superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent): a classificação em
caminhos e a auto-revisão da skill `brainstorming`, e as quatro fases da `systematic-debugging`. O
formato de rodadas de fronteira vem da skill `grilling`.
