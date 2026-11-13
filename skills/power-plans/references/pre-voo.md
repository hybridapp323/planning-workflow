# Pré-voo do plano

Referência da skill `power-plans` (passo 7). Leia quando o plano estiver escrito, antes de mostrá-lo
ao usuário ou a um revisor externo.

## Por que existe

A revisão externa é o passo mais caro do planejamento, e ela vinha sendo gasta também em defeito
barato. Medido em 11/2026, em 57 revisões externas de plano de dois projetos: mediana de 7 a 8
bloqueadores por revisão, sem queda ao longo de três meses em que esta skill dobrou de tamanho. Em
dez casos a regra já estava escrita aqui e o defeito da mesma classe voltou. Regra em prosa depende
de o autor lembrar; checagem roda sozinha.

O pré-voo tem duas peças, e elas pegam coisas diferentes. Medido em 11/2026 sobre 4 planos, na
versão exata em que foram mandados à revisão externa (34 bloqueadores registrados; versões
reconstruídas do transcript da sessão, porque o plano só era commitado depois da revisão):

- O **lint** achou 7 erros, e nenhum estava entre os 34. Ele pega formato e âncora (tarefa sem
  `Cobre`, caminho citado que não existe), não o que o revisor aponta.
- O **verificador de contexto limpo**, com o brief abaixo, uma rodada, modelo intermediário e sem
  acesso ao banco, apontou 13 dos 34 (38%) e mais 5 em parte. Trouxe perto de 15 achados por plano;
  os que não coincidem com a revisão não foram triados. Custo medido: cerca de 280 mil tokens e 10
  minutos por plano.

O que o verificador pegou: contrato que cita tipo ou função que não existe, chamador ou emissor fora
da matriz, ordem errada entre commit, migração e publicação, prova que passa sem o conserto, nulo em
filtro. O que passou por ele: semântica de falha e de repetição (timeout, segundo efeito),
autorização entre recursos, decisão de tela, colisão de ambiente entre tarefas paralelas.

Não pule o verificador por o lint ter passado limpo. E o pré-voo não substitui a revisão externa:
nesta medição ele tira perto de quatro em cada dez bloqueadores, não a maioria.

Nenhuma das duas peças julga o desenho: isso é do revisor externo e do usuário.

## 1. `plan-lint.py`: o que é mecânico

```bash
python3 <pasta desta skill>/scripts/plan-lint.py <plano.md> --spec <spec.md>
```

Roda da raiz do projeto (fora de um repositório git, a raiz é a pasta atual ou `--root`). Confere,
entre outras coisas: requisito da spec que nenhuma tarefa cita;
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
   Chave ou opção que desliga uma exigência conta como remoção: procure todo ponto que exige e
   todo texto que manda exigir (instrução de modelo, template, mensagem), em todos os caminhos,
   partindo do comportamento e não do nome da chave.
4. ORDEM. Compare os passos do coordenador com o script ou roteiro real de publicação e de
   migração do projeto: o que o plano publica cobre tudo que importa o que mudou? Algum passo liga
   um comportamento antes de o código dele existir, ou depende de algo que só nasce num passo
   posterior?
5. CONTRATOS. Leia cada regra dos contratos congelados contra as outras e contra os requisitos da
   spec: contradição, regra inexecutável, contrato mais restrito ou mais frouxo que o requisito,
   caso que o contrato não cobre. Leia a frase de cada requisito ao lado da frase do contrato que
   o implementa e liste toda condição que só o contrato tem.
6. CENÁRIOS DE VÁRIOS PASSOS. Para cada cenário de aceitação com mais de uma interação: percorra
   o código de hoje passo a passo e escreva em que estado o sistema está em cada passo. Aponte o
   passo em que a regra da tarefa não é alcançada (o gatilho sai num estado e a regra trata em
   outro), o termo que classifica a entrada e não tem definição na spec, e o cenário sem as
   entradas literais.

Antes da tabela, a cobertura dos itens 5 e 6, uma linha cada, mesmo quando não há achado:
- por requisito da spec no seu alcance: a frase do requisito, a frase do contrato ou da tarefa que
  o implementa, e as condições que só a segunda tem ("nenhuma" vale);
- por cenário de aceitação com mais de uma interação: o estado em cada passo e se a regra é
  alcançada.
Requisito ou cenário sem linha conta como não conferido.

Depois responda em tabela, do mais grave ao menos grave, só o confirmado com evidência, no máximo 15:
achado | evidência (arquivo:linha ou saída do comando) | classe (fato errado, consumidor esquecido,
contradição, ordem, prova que não prova, contrato incompleto, cenário que não chega na regra). Depois, "conferido e correto" (o que
você abriu e estava certo) e "não conferível". Sem opinião sobre o desenho.
```

**Plano com mais de uma trilha: um verificador por trilha**, em paralelo, cada um com o brief
acima mais a linha *"confira só a trilha <X>; leia o resto para contexto"*. O teto de 15 achados
vale por verificador. Medido em 11/2026: num plano de cinco trilhas e 51 tarefas, o pré-voo
devolveu 51 achados e a revisão externa mais 7, e os dois requisitos que depois custaram correção
em cadeia passaram sem nenhum. Os itens 3, 5 e 6 acima pegam os dois; num plano desse tamanho,
só chegam a cada requisito se cada trilha tiver o seu leitor.

**A linha de cobertura existe porque o teto de achados esconde o que não foi conferido.** Medido
em 11/2026, uma rodada de cada, sobre o mesmo plano já escrito e sem dizer ao verificador o que
procurar: sem a cobertura, ele devolveu 15 achados e o aperto de um requisito pelo contrato não
apareceu em lugar nenhum; com ela, o aperto apareceu na linha daquele requisito, e o cenário de
vários passos que não chegava na regra apareceu com o estado de cada passo. Nas duas rodadas
ficou de fora um texto de instrução de modelo que mandava exigir o que a chave desligava: o
item 3 ainda depende de o verificador procurar pelo comportamento.

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
