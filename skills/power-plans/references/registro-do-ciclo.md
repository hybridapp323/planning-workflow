# Registro do ciclo

Referência das skills `spec-interview`, `power-plans` e `orchestrating-execute`. É o último bloco
do arquivo de plano. Existe para uma pergunta só: **o processo está melhorando?** Sem ele, ninguém
sabe se uma mudança nestas skills derrubou os bloqueadores e as rodadas de correção ou só empurrou
o trabalho para o ciclo seguinte.

Trabalho feito na escala direta, sem arquivo de plano, não tem registro.

## O bloco

Copie para o fim do plano, sob o título `## Registro do ciclo`, e mantenha as chaves como estão:
quem lê é um script.

```yaml
registro_do_ciclo:
  plugin: nd                 # commit curto do plugin que a sessão carregou
  escala: completa           # minima | parcial | completa
  tem_tela: nao              # sim | nao
  spec:
    rodadas_de_perguntas: 0
    decisoes_do_usuario: 0
    decisoes_assumidas: 0
    referencia_visual: nao_se_aplica   # exercitada | aprovada | dispensada | nao_se_aplica
  plano:
    linhas: 0
    tarefas: 0
    prevoo_lint_erros: 0
    prevoo_verificador_achados: 0
    revisao_externa: nao_solicitada    # ou o modelo que revisou
    bloqueadores: {total: 0, documental: 0, decisao: 0, redesenho: 0, recusados: 0}
  execucao:
    inicio: nd               # AAAA-MM-DD
    entregue: nd             # AAAA-MM-DD
    emendas_de_contrato: 0
    escalacoes: {total: 0, que_o_plano_respondia: 0}
    gate: {veredito: sem_gate, achados: 0}     # passa | bloqueia | sem_gate
    tela_comparada_com_referencia: nao_se_aplica   # sim | nao | nao_se_aplica
    sonda_externa: nao_se_aplica               # antes_do_codigo | adiada | nao_se_aplica
    tokens: {total: nd, saida: nd}
  depois_de_entregue:
    rodadas_do_usuario: 0
    commits_de_correcao: 0
```

## Quem preenche o quê, e quando

| Parte | Quem | Momento |
| --- | --- | --- |
| `plugin`, `escala`, `tem_tela`, `spec`, `plano` (menos a revisão) | `power-plans` | ao terminar o pré-voo |
| `plano.revisao_externa` e `plano.bloqueadores` | `power-plans` | ao fechar a triagem da revisão |
| `execucao` | `orchestrating-execute` | no fecho, antes do commit |
| `depois_de_entregue` | quem atender a rodada | a cada correção que o usuário pedir depois da entrega |

## Regras

- **Número desconhecido é `nd`, nunca chute.** Um zero inventado estraga a medição mais que um vazio.
- **Conte no momento do fato.** Emenda de contrato e escalação se contam quando acontecem, no
  documento do ciclo; o fecho só copia o total. Reconstituir de memória no fim subconta.
- `decisoes_assumidas` conta as marcadas "assumida por mim" na spec. `bloqueadores.recusados`
  conta os que a triagem refutou com prova.
- `escalacoes.que_o_plano_respondia`: a pergunta do worker cuja resposta devia estar no plano.
- `rodadas_do_usuario`: cada vez que o usuário, depois de receber a entrega, pede ajuste no que
  foi entregue. Escopo novo pedido depois conta, e vale anotar ao lado.
- O `plugin` costuma estar no caminho de onde a skill foi carregada; se não der para saber, `nd`.
- Não transforme o registro em relatório: o que não cabe numa chave vai para o documento do ciclo.
