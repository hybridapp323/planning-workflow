# Pré-voo do plano

Referência da skill `power-plans` (passo 7). Leia quando o plano estiver escrito, antes de mostrá-lo
ao usuário ou a um revisor externo.

## Por que existe

A revisão externa é o passo mais caro do planejamento, e ela vinha sendo gasta em defeito barato.
Medido em 11/2026, em 57 revisões externas de plano de dois projetos: mediana de 7 a 8 bloqueadores
por revisão, sem queda ao longo de três meses em que esta skill dobrou de tamanho. Cerca de 70%
deles eram fato não conferido, consumidor esquecido, contradição ou ordem de publicação errada, que
um grep, uma consulta ou uma leitura cruzada mostraria. Em dez casos a regra já estava escrita aqui
e o defeito da mesma classe voltou. Regra em prosa depende de o autor lembrar; checagem roda sozinha.

O pré-voo tem duas peças, e elas pegam coisas diferentes. Medido em 11/2026, sobre a versão
anterior à revisão de 6 planos (35 bloqueadores registrados): o lint achou 5 defeitos reais, e
**nenhum deles estava entre os 35**. O lint pega o defeito de formato e de âncora que nem o
revisor externo viu (em 10 planos já revisados ele ainda achou 7). Quem ataca a classe dos
bloqueadores da revisão (fato que o código desmente, consumidor esquecido, ordem errada) é o
verificador de contexto limpo. Não pule o segundo por o primeiro ter passado limpo.

Nenhuma das duas peças julga o desenho: isso é do revisor externo e do usuário.

## 1. `plan-lint.py`: o que é mecânico

```bash
python3 <pasta desta skill>/scripts/plan-lint.py <plano.md> --spec <spec.md>
```

Roda da raiz do projeto. Confere, entre outras coisas: requisito da spec que nenhuma tarefa cita;
caminho de arquivo que não existe; `arquivo:linha` além do fim do arquivo; `[SUPOSTO:]` sustentando
uma tarefa sem "PARE"; tarefa sem `Pronto quando` ou sem `Cobre`; célula vazia em tabela
obrigatória; arquivo com dois donos; script citado nos passos do coordenador que não existe. Com
`--retired termo1,termo2` conta o que uma correção aposentou e devia ter sumido do plano.

- **Erro se conserta, não se explica.** Se o lint errou (formato que ele não conhece), o conserto
  é no lint, no mesmo trabalho, pela seção *Documentação viva* do `SKILL.md`.
- Aviso se lê. "Seção não encontrada" quer dizer que o plano cortou uma seção do esqueleto: confira
  que o corte foi dito.
- Escala mínima com arquivo de plano para aqui. Plano mínimo no chat não tem pré-voo.

## 2. Verificador de contexto limpo: o que precisa de olhos novos

Um agente que **não escreveu o plano** e não viu a conversa. Subagente do harness, em modelo
intermediário: o trabalho é ler e rodar comando, não desenhar. Escala parcial e completa.

O brief, para copiar:

```
Você é o verificador de um plano de implementação. Não escreveu o plano e não vai melhorá-lo: vai
conferir fatos. Somente leitura: não edite arquivo, não rode git que altere estado, consulta ao
banco só de leitura. Plano: <caminho>. Spec: <caminho>. Acesso ao dado: <como consultar, sem
credencial colada>.

1. LINHAS CITADAS. Para cada `[LIDO: arquivo:linha]` e cada célula `arquivo:linha` do traçado
   (§3.1): abra o trecho e diga se ele afirma o que o plano diz que afirma. Leia também a função
   auxiliar de que o trecho depende e os testes vizinhos.
2. AFIRMAÇÕES DE CARGA (§0.1). Rode de novo a consulta do falsificador de cada linha e compare a
   contagem. Depois tente UM falsificador que o autor não tentou (o caminho de exceção, o bypass,
   os casos da mesma forma que ficaram fora da amostra).
3. QUEM MAIS LÊ E QUEM MAIS EMITE. Para cada função, campo, tabela, evento, texto ou arquivo que
   o plano muda ou remove: procure leitores e emissores no código, nos testes e nos dados
   (template, configuração, seed). Liste os que não estão na matriz de ownership nem no traçado.
4. ORDEM. Compare os passos do coordenador com o script ou roteiro real de publicação e de
   migração do projeto: o que o plano publica cobre tudo que importa o que mudou? Algum passo liga
   um comportamento antes de o código dele existir?
5. CONTRATOS. Leia cada regra dos contratos congelados contra as outras e contra os requisitos da
   spec: contradição, regra inexecutável, contrato mais restrito que o requisito.

Responda em tabela: achado | evidência (arquivo:linha ou saída do comando) | classe (fato errado,
consumidor esquecido, contradição, ordem, prova que não prova). Depois, "conferido e correto": o
que você abriu e estava certo. Sem opinião sobre o desenho.
```

## 3. Depois do pré-voo

- **Confira cada achado antes de aceitar**, como faria com um revisor externo, e corrija no lugar:
  a correção substitui o texto contradito, nunca é anexada embaixo dele.
- Rode o `plan-lint.py` de novo depois das correções.
- Anote no `## Registro do ciclo` do plano: `prevoo_lint_erros` (da primeira rodada) e
  `prevoo_verificador_achados` (os confirmados).
- Só então siga para o passo 8: revisão externa ou commit e push.

O que o pré-voo **não** pega, e continua sendo da revisão externa na escala completa: desenho
errado, decisão de produto que faltou, risco de segurança que exige modelar um ataque, interação
entre peças que ainda não existem.
