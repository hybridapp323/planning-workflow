# planning-workflow

Skills de Claude Code para o ciclo de vida de uma feature, da ideia crua até a execução — e a depuração de quando algo quebra no caminho.

- **`spec-interview`** — entrevista em rodadas até a ideia fechar: classifica a escala (sonda / limitada / arquitetural), mapeia a árvore de decisões e pergunta a fronteira inteira por rodada com a recomendação em cada pergunta, busca sozinha os fatos que estão no código ou no banco, e só para quando não sobra decisão em aberto. Termina com a spec escrita e aprovada.
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

## Instalar em outra máquina

O diretório precisa ser filho direto de `~/.claude/skills/`:

```bash
git clone https://github.com/hybridapp323/planning-workflow.git ~/.claude/skills/planning-workflow
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
    ├── spec-interview/
    │   └── SKILL.md
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

## Documentação viva

As quatro skills são documentação viva do próprio processo, e cada uma diz na seção final o que aceita receber. O critério de entrada é o mesmo em todas: **custou.**

| Skill | O que entra | O que fica de fora |
| --- | --- | --- |
| `spec-interview` | Pergunta que faltou e virou retrabalho, bug, ou uma discussão que se repetiu pela segunda vez | Preferência de estilo; ideia de pergunta que nunca foi testada |
| `power-plans` | Lacuna de plano que quebrou execução paralela — contrato não congelado, consumidor esquecido, colisão de ownership | Ajuste cosmético de template |
| `orchestrating-execute` | Armadilha de execução paga na marra (`references/orca-traps.md`) | Erro pontual de digitação numa sessão |
| `systematic-debugging` | Armadilha de diagnóstico que custou tempo real e vai custar de novo — camada que engole erro, log que mente | Bug específico de um repositório (isso é do `CLAUDE.md` dele) |

Regra comum: a edição entra **no mesmo trabalho** em que o aprendizado aconteceu, nunca "depois". Doc desatualizada é pior que doc ausente — a próxima sessão segue a instrução errada com confiança.

## Créditos

`spec-interview` e `systematic-debugging` adaptam material do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent): a classificação em três caminhos e o portão de aprovação da skill `brainstorming`, e as quatro fases da `systematic-debugging`. O formato de rodadas de fronteira vem da skill `grilling`.
