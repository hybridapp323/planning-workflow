# Rubrica dos três níveis

O nível responde a uma pergunta só: **o que acontece se esta tarefa for feita mal, e quanto raciocínio ela exige para ser feita bem?**

Não é tamanho. Não é quantidade de arquivos. Não é quanto tempo leva.

## Complexa

Erro caro, erro difícil de detectar, ou raciocínio que precisa segurar muita coisa ao mesmo tempo.

Sinais:

- Decide **precedência** entre regras que podem se aplicar juntas ("se a prova cai na semana do deload e também na janela de taper, quem ganha?").
- Toca **invariante**: algo que precisa continuar verdadeiro depois da mudança e que nenhum teste óbvio cobre.
- Toca **concorrência**: escrita simultânea, trava otimista, idempotência, ordem de eventos.
- Toca **segurança ou privacidade**: policy, função com privilégio elevado, dado pessoal, autorização.
- Escreve em **dado de produção** de forma difícil de reverter.
- Precisa entender um módulo inteiro antes de mudar dez linhas dele.
- É uma **revisão adversarial** de outra tarefa (revisar bem é mais difícil que fazer).

Exemplos reais:

- Função com privilégio elevado no banco, com guarda de role e trava por hash da versão anterior.
- Módulo determinístico que transforma um plano e precisa ser fiel na ida e na volta.
- Endpoint que lê, transforma e grava atômico, com resposta que distingue "não aplicou" de "falhou".
- Consumidores espalhados de um dado que mudou de forma (relógio, exportação, job, tela).

## Média

Solução conhecida, escopo claro, o erro aparece em teste ou na tela.

Sinais:

- O caminho é conhecido, o trabalho é aplicar bem.
- Existe padrão no repositório para copiar.
- O resultado é verificável localmente por quem fez.
- Quebra fica evidente rápido.

Exemplos reais:

- Tabela nova com índices e permissões, seguindo o padrão já estabelecido do repositório.
- Componente de UI com estado local, seguindo primitivas que já existem.
- Camada de acesso a dado no front, tipada contra contrato já congelado.
- Validação e mensagens de aviso no formulário, com as regras já definidas na spec.

## Baixa

Mecânica, verificável por inspeção, sem decisão de design.

Sinais:

- Se duas pessoas fizerem, sai igual.
- Não há escolha a fazer, só execução.
- Revisar leva menos tempo que fazer.

Exemplos reais:

- Chaves de tradução novas replicadas nos quatro idiomas, com as chaves já fixadas no contrato.
- Renomear símbolo em vários arquivos.
- Atualizar documento para refletir mudança já feita.
- Mover arquivo e ajustar imports.

## Casos de fronteira

**"É grande, então é complexa."** Não. Trezentas linhas de tradução mecânica são baixas. Dez linhas que decidem qual regra vence são complexas.

**"É pequena, então é baixa."** Não. Ver acima.

**"Tem teste, então é média."** Depende de o teste cobrir o que importa. Teste que só confirma o caminho feliz não rebaixa uma tarefa que decide precedência.

**"É UI, então é média."** UI que só compõe primitivas existentes é média. UI que inventa um padrão novo, que a partir dela vira referência para o resto do produto, é complexa.

**Empate.** Suba. O modelo mais forte numa tarefa média custa menos que o retrabalho de uma complexa mal feita, e você descobre o erro mais tarde do que gostaria.

## Como isso aparece no plano

Cada tarefa carrega o nível no título, e o plano traz placeholders no topo:

```
### T4 — Migration do RPC transacional · **Complexa** · sem dependência
```

```
| Nível    | Modelo             |
| -------- | ------------------ |
| Complexa | <MODELO_COMPLEXA>  |
| Média    | <MODELO_MEDIA>     |
| Baixa    | <MODELO_BAIXA>     |
```

O plano nunca preenche essa tabela. Quem preenche é o usuário, na hora de executar.
