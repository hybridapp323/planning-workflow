# planning-workflow

Skills para o ciclo de vida de uma feature, da ideia crua até a execução, e a depuração de quando algo quebra no caminho.

Empacotado como plugin de Claude Code, mas o conteúdo é **markdown puro**: três das quatro skills não dependem de nenhuma ferramenta específica e rodam em qualquer agente que aceite instruções em arquivo. Ver [Usar em outro agente](#usar-em-outro-agente-ou-outro-cli).

- **`spec-interview`** — entrevista em rodadas até a ideia fechar: classifica a escala (sonda / limitada / arquitetural), mapeia a árvore de decisões e pergunta a fronteira inteira por rodada com a recomendação em cada pergunta, busca sozinha os fatos que estão no código ou no banco, e só para quando não sobra decisão em aberto: a fronteira da árvore vazia **e** a varredura de cobertura sem categoria ausente. Termina com a spec escrita no esqueleto (`references/spec-template.md`: requisito com id e cenário de aceitação, critério de sucesso com número, decisão com autoria) e aprovada.
- **`power-plans`** — escreve o plano de implementação desenhado para execução multi-agente: evidência antes de plano, níveis de complexidade, matriz de ownership de arquivo, contratos congelados, grafo de ondas e gates bloqueantes. Não cita orquestrador.
- **`orchestrating-execute`** — executa esse plano: portão de atribuição de modelo por nível, laço de ondas, gates, e o que nunca se delega. Usa a skill `orchestration` do Orca para a mecânica.
- **`systematic-debugging`** — causa raiz antes de conserto: as quatro fases, o limite de três consertos falhados que vira questão de arquitetura, e as racionalizações que precedem cada banda-aid.

São genéricas de propósito. As regras específicas de cada repositório saem do `CLAUDE.md` / `AGENTS.md` dele, e de um `.claude/plan-profile.md` opcional.

## Onde isso entra

```
ideia  →  spec-interview  →  spec aprovada  →  power-plans  →  plano commitado  →  orchestrating-execute
                                                                                            |
                                                systematic-debugging  <---- quebrou --------+
```

`spec-interview` e `power-plans` param sozinhas: uma entrega a spec, a outra entrega o plano. Quem sobe worker é `orchestrating-execute`, e só quando o usuário mandar.

## Instalar

### Claude Code, pelo marketplace (recomendado)

Dentro de uma sessão:

```
/plugin marketplace add hybridapp323/planning-workflow
/plugin install planning-workflow@planning-workflow
```

O repositório é o próprio marketplace (`.claude-plugin/marketplace.json` na raiz). Atualizar depois é `/plugin marketplace update planning-workflow`.

### Claude Code, por clone

Serve quando você quer editar as skills e versionar as mudanças de volta. O diretório precisa ser filho direto de `~/.claude/skills/`:

```bash
git clone https://github.com/hybridapp323/planning-workflow.git ~/.claude/skills/planning-workflow
```

Carrega na sessão seguinte, ou imediatamente com `/reload-plugins`. Atualizar: `git pull` nesse diretório. Depois de editar, `git add <caminhos> && git commit && git push` — nunca `git add -A`, porque as skills são documentação viva e costumam ter mudança de mais de uma sessão na árvore.

## Usar em outro agente ou outro CLI

O núcleo é markdown com frontmatter YAML (`name`, `description`) e não tem código. O que muda de agente para agente é só como ele **descobre** e **carrega** o arquivo.

**Portabilidade, honestamente:**

| Skill | Portável? | O que prende |
| --- | --- | --- |
| `power-plans` | **sim, inteira** | nada. Ela se recusa de propósito a citar orquestrador: entrega um grafo com níveis, donos e contratos congelados |
| `systematic-debugging` | **sim, inteira** | nada |
| `spec-interview` | **sim, com um detalhe** | prefere a ferramenta de pergunta em modal do harness (`AskUserQuestion`); sem ela, a própria skill traz o formato em texto numerado |
| `orchestrating-execute` | **parcialmente** | a mecânica é do Orca (`orca`, `wave.sh`), a camada de orquestração usada aqui. A skill diz o que fazer sem ele: *"o plano continua válido, é um grafo com níveis, donos e contratos; execute com o mecanismo de subagente que houver"*. Já `references/orca-traps.md` é 100% específico e não serve fora do Orca |

**Receita mínima em outro agente:**

1. Copie `skills/<nome>/SKILL.md` e o `references/` dele para onde aquele agente lê instrução (pasta de skills, regras, ou system prompt).
2. Se o agente **não** faz seleção automática por `description`, cole `hooks/session-start.md` no prompt de sistema. São ~20 linhas com a tabela pedido → skill, e é o que faz o agente escolher a skill certa antes da primeira ferramenta.
3. Ignore `.claude-plugin/` e `hooks/hooks.json`: são formato de Claude Code e não têm equivalente garantido em outro lugar.

O ciclo em si — spec fecha antes do plano, plano fecha antes da execução, e cada um para no próprio portão — não depende de ferramenta nenhuma.

## Estrutura

```
planning-workflow/
├── .claude-plugin/
│   ├── plugin.json         # manifesto do plugin
│   └── marketplace.json    # o repo e o proprio marketplace: /plugin marketplace add
├── LICENSE                 # MIT, + atribuicao do material de terceiro
├── README.md
├── hooks/
│   ├── hooks.json          # SessionStart: injeta o roteador do ciclo
│   └── session-start.md    # o texto injetado
└── skills/
    ├── spec-interview/
    │   ├── SKILL.md
    │   └── references/
    │       ├── spec-template.md    # esqueleto da spec: FR-n com cenário de aceitação, SC-n, decisões com autoria
    │       └── coverage-scan.md    # segundo teste de fechamento: as categorias que a árvore não alcança
    ├── power-plans/
    │   ├── SKILL.md
    │   └── references/
    │       ├── plan-template.md
    │       ├── complexity-rubric.md
    │       └── external-review.md
    ├── orchestrating-execute/
    │   ├── SKILL.md
    │   └── references/
    │       └── orca-traps.md
    └── systematic-debugging/
        └── SKILL.md
```

## O gancho de roteamento

`hooks/hooks.json` injeta `hooks/session-start.md` no começo de cada sessão (`startup`, `clear`, `compact`). São ~20 linhas: a tabela pedido → skill, e a regra de que a decisão vem **antes** da primeira ferramenta.

A descoberta da skill já funciona sem ele — toda `description` entra na lista da sessão de qualquer forma. O gancho existe para o caso ambíguo, em que o agente racionaliza ("isso é simples", "deixa eu só olhar o código") e começa a implementar sem passar pelo ciclo.

Se em alguma máquina o gancho não carregar (o carregamento de `hooks/` de um plugin instalado por diretório depende da versão do Claude Code), o mesmo efeito sai de seis linhas no `~/.claude/settings.json` daquela máquina, apontando para o mesmo arquivo:

```json
"SessionStart": [
  { "matcher": "startup|clear|compact", "hooks": [
    { "type": "command", "shell": "bash",
      "command": "cat \"$HOME/.claude/skills/planning-workflow/hooks/session-start.md\"" } ] }
]
```

## Documentação viva

As quatro skills são documentação viva do próprio processo, e cada uma diz na seção final o que aceita receber. O critério de entrada é o mesmo em todas: **custou.**

| Skill | O que entra | O que fica de fora |
| --- | --- | --- |
| `spec-interview` | Pergunta que faltou e virou retrabalho, bug, ou uma discussão que se repetiu pela segunda vez | Preferência de estilo; ideia de pergunta que nunca foi testada |
| `power-plans` | Lacuna de plano que quebrou execução paralela — contrato não congelado, consumidor esquecido, colisão de ownership | Ajuste cosmético de template |
| `orchestrating-execute` | Armadilha de execução paga na marra (`references/orca-traps.md`) | Erro pontual de digitação numa sessão |
| `systematic-debugging` | Armadilha de diagnóstico que custou tempo real e vai custar de novo — camada que engole erro, log que mente | Bug específico de um repositório (isso é do `CLAUDE.md` dele) |

Regra comum: a edição entra **no mesmo trabalho** em que o aprendizado aconteceu, nunca "depois". Doc desatualizada é pior que doc ausente — a próxima sessão segue a instrução errada com confiança.

## Licença

MIT, ver [`LICENSE`](LICENSE). `spec-interview` e `systematic-debugging` adaptam material MIT de terceiro; a atribuição está no arquivo de licença e nos créditos abaixo.

## Créditos

`spec-interview` e `systematic-debugging` adaptam material do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent): a classificação em três caminhos e o portão de aprovação da skill `brainstorming`, e as quatro fases da `systematic-debugging`. O formato de rodadas de fronteira vem da skill `grilling`.
