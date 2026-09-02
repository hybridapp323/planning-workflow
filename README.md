# planning-workflow

Skills de Claude Code para o ciclo de vida de uma feature, da ideia crua até a execução — e a depuração de quando algo quebra no caminho.

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

## Créditos

`spec-interview` e `systematic-debugging` adaptam material do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent): a classificação em três caminhos e o portão de aprovação da skill `brainstorming`, e as quatro fases da `systematic-debugging`. O formato de rodadas de fronteira vem da skill `grilling`.
