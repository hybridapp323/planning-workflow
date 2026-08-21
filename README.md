# planning-workflow

Duas skills de Claude Code para o ciclo de implementação de feature depois que o design está aprovado:

- **`writing-plans`** — escreve o plano de implementação desenhado para execução multi-agente: evidência antes de plano, níveis de complexidade, matriz de ownership de arquivo, contratos congelados, grafo de ondas e gates bloqueantes. Não cita orquestrador.
- **`orchestrating-plans`** — executa esse plano: portão de atribuição de modelo por nível, laço de ondas, gates, e o que nunca se delega. Usa a skill `orchestration` do Orca para a mecânica.

São genéricas de propósito. As regras específicas de cada repositório saem do `CLAUDE.md` / `AGENTS.md` dele, e de um `.claude/plan-profile.md` opcional.

## Onde isso entra

```
brainstorming  →  spec aprovada  →  writing-plans  →  plano commitado  →  orchestrating-plans
```

## Instalar em outra máquina

O diretório precisa ser filho direto de `~/.claude/skills/`:

```bash
git clone <url-do-repo> ~/.claude/skills/planning-workflow
```

Carrega na sessão seguinte como `planning-workflow@skills-dir`, ou imediatamente com `/reload-plugins`.

## Atualizar

```bash
cd ~/.claude/skills/planning-workflow && git pull
```

E depois de editar, daqui:

```bash
cd ~/.claude/skills/planning-workflow && git add <caminhos> && git commit && git push
```

## Estrutura

```
planning-workflow/
├── .claude-plugin/plugin.json
├── README.md
└── skills/
    ├── writing-plans/
    │   ├── SKILL.md
    │   └── references/
    │       ├── plan-template.md
    │       ├── complexity-rubric.md
    │       └── external-review.md
    └── orchestrating-plans/
        ├── SKILL.md
        └── references/
            └── orca-traps.md
```

`references/orca-traps.md` é documentação viva: armadilha nova descoberta em execução entra ali no mesmo trabalho.
