---
name: systematic-debugging
description: >-
  Investigação de causa raiz antes de qualquer tentativa de correção. USE SEMPRE
  ao encontrar bug, falha de teste, comportamento inesperado, erro de build,
  problema de performance ou integração quebrada — antes de propor conserto. E
  especialmente quando houver pressa, quando o conserto parecer óbvio, ou quando
  uma correção anterior não resolveu. Triggers: "tá quebrado", "não funciona",
  "deu erro", "o teste falhou", "isso era pra funcionar", "por que isso está
  acontecendo", "conserta isso", "tá dando pau". Correção de sintoma é falha,
  não conserto.
---

# Depuração sistemática

## A lei de ferro

```
NENHUM CONSERTO SEM INVESTIGAÇÃO DE CAUSA RAIZ ANTES
```

Sem a Fase 1 completa, você não propõe conserto. Nem "só pra testar".

Violar a letra do processo é violar o espírito da depuração.

## Quando usar

Qualquer problema técnico: teste que falha, bug em produção, comportamento inesperado, performance, build, integração.

**Especialmente quando:**

- há pressa (emergência é o que torna o chute tentador);
- "é só um ajuste rápido" parece óbvio;
- você já tentou mais de um conserto;
- o conserto anterior não resolveu;
- você não entende o problema por inteiro.

**Não pule porque:** o problema parece simples (bug simples também tem causa raiz), você está com pressa (chutar garante retrabalho), ou alguém quer resolvido agora (sistemático é mais rápido que tatear).

## As quatro fases

Complete cada fase antes da seguinte.

### Fase 1 — causa raiz

**Antes de QUALQUER conserto:**

1. **Leia a mensagem de erro inteira.** Não passe por cima de erro nem de warning: eles costumam conter a solução exata. Stack trace completo, número de linha, caminho de arquivo, código do erro.

2. **Reproduza de forma consistente.** Você consegue disparar de novo? Quais os passos exatos? Acontece toda vez? Se não reproduz, colete mais dado — não chute.

3. **Veja o que mudou.** Diff, commits recentes, dependência nova, config, diferença de ambiente.

4. **Instrumente as fronteiras, em sistema de várias camadas.** Quando o fluxo passa por vários componentes (front → edge function → banco, CI → build → assinatura), **antes de propor conserto** adicione log em cada fronteira: o que entra no componente, o que sai, se a config/variável de ambiente propagou, qual o estado em cada camada. Rode **uma vez** para juntar evidência de **onde** quebra, e só então investigue aquele componente.

5. **Rastreie o dado para trás.** Quando o erro aparece fundo na pilha, o instinto é consertar onde ele aparece — e isso é tratar sintoma. Vá subindo:

   - onde nasce o valor errado?
   - quem chamou isso com o valor errado?
   - continue subindo até achar a origem;
   - conserte na origem, não no sintoma.

   Se não der para rastrear lendo, instrumente: logue o valor **antes** da operação perigosa (não depois que ela falha), junto com o contexto (parâmetro, ambiente, `new Error().stack` para a cadeia de chamada completa). Em teste, use a saída de erro direta do runtime — logger pode estar suprimido.

**Regra dura deste projeto:** para bug, a causa vem de evidência concreta — query, log, ou o código-fonte lido — antes de escrever plano ou editar arquivo. Suspeita raciocinada não é causa raiz.

### Fase 2 — padrão

1. **Ache um exemplo que funciona.** Código parecido, no mesmo repositório, que está de pé.
2. **Leia a referência inteira.** Se está implementando um padrão, leia a implementação de referência **completa**, linha por linha. Não folheie.
3. **Liste as diferenças.** Todas, por menores que pareçam. Não decida que "isso não pode importar".
4. **Entenda as dependências.** De que outros componentes, configs e suposições isso depende?

### Fase 3 — hipótese

1. **Uma hipótese por vez, escrita.** "Acho que X é a causa raiz porque Y." Específica, não vaga.
2. **Teste minimamente.** A menor mudança possível que testa a hipótese. Uma variável por vez.
3. **Verifique antes de seguir.** Funcionou → Fase 4. Não funcionou → **nova hipótese**, nunca mais um conserto empilhado em cima do anterior.
4. **Quando não souber, diga "não entendi X".** Não finja entender.

### Fase 4 — conserto

1. **Escreva antes o caso que falha.** A reprodução mais simples possível — teste automatizado se houver framework, script de uma vez se não houver. **Antes** do conserto, não depois.
2. **Um conserto só.** Ataque a causa raiz identificada. Uma mudança por vez, sem "já que estou aqui", sem refatoração de carona.
3. **Verifique.** O teste passa? Nenhum outro quebrou? O problema realmente sumiu — ou só mudou de lugar?
4. **Se não funcionou: pare e conte.** Quantos consertos você já tentou?
   - menos de 3 → volte à Fase 1 com a informação nova;
   - **3 ou mais → pare e questione a arquitetura.** Não tente o quarto.

5. **Três consertos falhados = problema de arquitetura, não hipótese errada.**

   O padrão é reconhecível: cada conserto revela um acoplamento novo em outro lugar; cada conserto exige "refatorar tudo" para caber; cada conserto cria sintoma novo.

   Pare e questione o fundamento: esse padrão é sólido? Estamos seguindo com ele por inércia? Vale refatorar em vez de continuar consertando sintoma? **Converse com o usuário antes de tentar mais consertos.**

### Depois da causa raiz: defesa em camadas

Achada a causa, considere validar em mais de uma camada — a entrada valida, o intermediário recusa o valor impossível, a operação perigosa se recusa a rodar fora do contexto esperado. Não é redundância inútil: é o que torna a classe inteira do bug impossível de voltar, em vez de só esta ocorrência.

Só faça isso **depois** de achar a causa. Antes, virou banda-aid em quatro lugares.

## Bandeiras vermelhas — pare e volte à Fase 1

Se você se pegar pensando:

- "conserto rápido agora, investigo depois";
- "deixa eu mudar X e ver se resolve";
- "mudo várias coisas e rodo os testes";
- "pulo o teste, verifico na mão";
- "provavelmente é X, vou consertar isso";
- "não entendi direito, mas isso talvez funcione";
- "o padrão diz X mas vou adaptar";
- listar "os problemas principais" como consertos, sem ter investigado;
- propor solução antes de rastrear o fluxo do dado;
- "só mais uma tentativa" (já tendo tentado duas ou mais).

**Todas significam: pare. Volte à Fase 1.**

## Sinais do usuário de que você está errando

- "isso não está acontecendo?" → você assumiu sem verificar;
- "isso vai mostrar…?" → faltou instrumentar para juntar evidência;
- "para de chutar" → você está propondo conserto sem entender;
- "pensa fundo nisso" → questione o fundamento, não o sintoma;
- "a gente tá travado?" → sua abordagem não está funcionando.

Ao ver qualquer um deles: pare, volte à Fase 1.

## Racionalizações comuns

| Desculpa | Realidade |
| --- | --- |
| "É simples, não precisa de processo" | Problema simples também tem causa raiz. O processo é rápido em bug simples. |
| "É emergência, não dá tempo" | Sistemático é **mais rápido** que tatear no escuro. |
| "Tento isso primeiro, investigo depois" | O primeiro conserto define o padrão. Faça certo desde o começo. |
| "Escrevo o teste depois de confirmar" | Conserto sem teste não se sustenta. O teste antes é a prova. |
| "Vários consertos de uma vez economizam tempo" | Não dá para isolar o que funcionou, e cria bug novo. |
| "A referência é longa, adapto o padrão" | Entendimento parcial garante bug. Leia inteira. |
| "Estou vendo o problema, deixa eu consertar" | Ver o sintoma não é entender a causa. |
| "Só mais uma tentativa" (após 2+) | 3 falhas = problema de arquitetura. Questione o padrão. |

## Referência rápida

| Fase | Atividade | Critério de saída |
| --- | --- | --- |
| **1. Causa raiz** | Ler erro, reproduzir, ver o que mudou, instrumentar fronteiras, rastrear para trás | Entender **o quê** e **por quê** |
| **2. Padrão** | Achar exemplo que funciona, comparar | Diferenças identificadas |
| **3. Hipótese** | Uma teoria, teste mínimo | Confirmada, ou nova hipótese |
| **4. Conserto** | Teste que falha, um conserto, verificação | Bug resolvido, nada mais quebrado |

## Quando a investigação diz "não tem causa raiz"

Se a investigação mostrar que é mesmo ambiental, dependente de timing, ou externo: você completou o processo. Documente o que investigou, implemente o tratamento adequado (retry, timeout, mensagem de erro honesta) e adicione log/monitoramento para a próxima ocorrência.

**Mas:** 95% dos casos de "não tem causa raiz" são investigação incompleta.

## Documentação viva

Quando uma sessão de depuração revelar uma armadilha nova deste tipo de sistema — uma camada que engole erro em silêncio, um log que mente, uma ferramenta cuja saída parece dizer o contrário do que diz — ela entra aqui **no mesmo trabalho**. Critério de entrada: **custou tempo real**, e vai custar de novo.

Como escrever: melhore a seção que já cobre o assunto antes de acrescentar linha; siga o `AGENTS.md` da raiz do plugin (conceito, não caso); escreva no clone git de onde a skill foi carregada (sem git, deixe a proposta no relatório); **não commite nem dê push**, avise o usuário como follow-up com arquivo e seção.

---

*Adaptado da skill `systematic-debugging` do plugin [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent), com as técnicas de rastreamento reverso e defesa em camadas destiladas para dentro do fluxo principal.*
