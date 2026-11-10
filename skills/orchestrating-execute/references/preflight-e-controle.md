# Preflight e controle de avanço

Referência da skill `orchestrating-execute`. Leia antes do primeiro comando da execução.

## Preflight

Leia o plano inteiro antes de qualquer comando. Ele precisa ter, no mínimo:

- nível de complexidade em cada tarefa;
- matriz de ownership de arquivo;
- contratos congelados escritos literal;
- grafo com dependências e passos do coordenador;
- **um `Pronto quando` por tarefa, copiado de um cenário de aceitação da spec.**
- para tarefa com risco de interação/ordem, camada de prova, peças reais/simuladas e
  primeira prova integrada com dependências e dono explícitos.

Faltando qualquer um, **pare e volte para `power-plans`**. Executar um plano sem ownership é combinar colisão; sem contrato congelado é combinar divergência; **sem critério de pronto é combinar que o coordenador invente um — e ele vai inventar relendo a spec, que é exatamente onde o sentido se perde.** Custa menos consertar o documento agora.

O quinto item tem uma verificação mecânica, e ela custa segundos: rode de novo o `plan-lint.py`
da skill `power-plans` (`scripts/plan-lint.py <plano> --spec <spec>`). Ele acusa requisito que
nenhuma tarefa cita e, como o código andou desde que o plano foi escrito, também o caminho e a
linha que deixaram de existir. Erro novo é âncora deslocada: conserte o plano antes de despachar.

Medido em 2026-09-03: a spec tinha 13 FRs com cenário executável; o plano citava **6 deles zero vezes** e não tinha nenhum `Pronto quando`. O coordenador escreveu o critério de cada briefing de cabeça, e um campo que a spec mandava tratar como *"desconhecido, nunca zero"* virou "zero" no briefing — um valor inventado entrou na conta como se fosse medido, e o defeito só apareceu na revisão adversarial do fim. `plano=0` num FR é um requisito que nenhum worker vai ver.

Confirme também que a árvore está limpa do que interessa, e que você sabe quais arquivos modificados **não** são deste trabalho. Sessões paralelas deixam lixo, e ele acaba num commit errado.

**Revisão da spec ou do plano dentro do grafo não é passo de execução.** Se o plano traz uma
tarefa que revisa o próprio plano (um `S0 — revisão externa do plano`, "bloqueia a onda 1"), ela
só roda se o usuário pediu a revisão nesta sessão, com o modelo que ele nomeou. Sem pedido: pule,
diga em uma linha que pulou, e comece em C0 / onda 1. Medido em 2026-09-22: um executor abriu o
ciclo despachando o revisor do plano, uma task no run e nenhum worker, sem que o usuário tivesse
pedido revisão. Gate (`S<n>` sobre código escrito, antes de passo irreversível) é outra coisa e
segue a seção *Dois mecanismos de qualidade*.

## Controle de avanço e custo

Registre no plano o comportamento observável de aceitação, limites técnicos de candidatas e
tentativas, estimativas de tokens totais/saída/caminho crítico e saldo pago já autorizado.
Estimativa não concede quota. Mantenha um estado corrente único: fonte, último aceite,
falha/família, tentativas acumuladas, consumo, evidência e próximo passo; ligue logs por
referência. Contagem de testes verdes não aprova jornada vermelha ou prova modelo simulado.

Faça diagnóstico focal e contraprovas durante o reparo; estabilize a candidata antes da
campanha completa obrigatória. Repetir exige mudança relevante, falha ou dúvida concreta.
A segunda reprovação da mesma família ou o freio técnico do plano/runner (inclusive três a
cinco candidatas) chama automaticamente o advisor. Trocar SHA, worker ou sessão não zera
tentativas. Para texto aberto, avalie estado estruturado e composição antes de mais exceções.

**Lote com modelo estocástico não fecha em 100% por amostra.** Se cada cenário passa 96% das vezes, 25 juntos passam
cerca de metade das vezes; corrigir a redação de cada vermelho novo abre uma candidata por rodada e não converge.
Antes de abrir candidata, classifique o vermelho: defeito (repete no mesmo SHA, ou nasce do seu código) vai para
correção; variação (abaixo de 1 em 3 no histórico do dia) vai como resíduo medido ao usuário, que decide. A
correção de defeito de redação se prova contra o corpus de TODAS as respostas reais do dia, nunca contra a última
frase. E verde não é aceite: leia as respostas dos verdes. Medido em 01/11/2026 (vertical nova, 5 candidatas):
a leitura achou três defeitos que as asserções passavam, um deles por oráculo de substring curta ("IA" dentro de
"informações").
