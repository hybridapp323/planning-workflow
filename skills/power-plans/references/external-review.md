# Revisão externa read-only

Uma segunda opinião, de outro agente ou outro modelo, sobre a spec e o plano **antes** de executar. Ela não altera nada: produz um relatório com veredito (passa / bloqueia) e a lista de problemas.

Vale quando a feature é grande, quando toca dado de produção, ou quando o usuário pede. Ofereça; não imponha, e não fixe qual agente ou modelo faz o papel. O usuário escolhe.

## O que entregar ao revisor

Três coisas, e o caminho absoluto de cada uma:

1. A spec.
2. O plano.
3. O snapshot de evidência da fase 0 (é o que evita o revisor gastar o turno inteiro redescobrindo o schema).

4. **As suas afirmações de carga, nomeadas uma a uma**, com o pedido explícito de tentar
   derrubar cada uma. São as afirmações que, se falsas, derrubam uma decisão estrutural do
   plano, e quase sempre têm forma de invariante ("isso continua garantido", "não existe
   caminho que faça X"). Sem esta lista o revisor distribui atenção por igual, e a atenção
   por igual é o que deixa passar o furo caro. Cada afirmação chega com a consulta do
   falsificador já rodada e a contagem dela (§0.1 do plano); o que você pede é o que essa
   consulta não viu. Medido em 2026-09-12: os quatro bloqueadores estavam embaixo de perguntas
   que o próprio briefing fazia. O autor sabia onde estava a dúvida e mandou a dúvida, não a
   contagem.
5. **O que você NÃO conseguiu verificar, e por quê.** Diga também o que o revisor não vai
   ter: sem acesso ao banco ele marca como hipótese o que você mede numa query. Resolver essas
   hipóteses depois é seu, não dele.

Mais o mandato, abaixo, e o caminho onde ele deve escrever o relatório, **fora do repositório**.

Ordene as perguntas por importância e termine sempre com esta, que rende mais que as
específicas: *"o que está faltando aqui que eu não teria como notar, porque fui eu que
escrevi?"* Peça também que ele diga o que conferiu e achou **correto**: sem isso você não
sabe distinguir "verificado e são" de "não olhou".

## O mandato read-only

Escreva no briefing, com estas palavras:

- Não editar nenhum arquivo do repositório.
- Não rodar comando de git.
- Não aplicar migration, não deployar função, não rodar SQL de escrita.
- Consulta ao banco: apenas leitura.
- Pode escrever exatamente um arquivo: o relatório, no caminho indicado, fora do repositório.

Diga também **quais caminhos de acesso ao banco existem** (MCP, CLI, credenciais e onde elas estão), sem colar valor de credencial. Um revisor que não sabe que pode consultar o banco vai devolver hipótese onde você queria evidência.

## Formato do relatório

Peça exatamente isto:

```
Veredito: PASSA | BLOQUEIA
Bloqueadores  — impedem executar como está, com arquivo:linha ou query que prova,
                e o custo da correção: documental | decisão do usuário | redesenho
Riscos        — não impedem, mas custam se ignorados
Sugestões     — melhorias opcionais
```

Exija prova em cada bloqueador. Bloqueador sem `arquivo:linha` nem resultado de query é opinião.

Exija também o custo. Um caminho de arquivo errado e uma decisão de produto em aberto cumprem a
mesma barra de "impede executar como está" e custam coisas muito diferentes; sem a etiqueta,
"BLOQUEIA" lê como "está tudo errado". Medido em 2026-09-12: quatro bloqueadores, três
documentais e uma decisão do usuário, zero redesenho. O esqueleto estava são; a camada de fatos
sobre dado existente e convenção do repositório, não.

## Verificar que ele foi mesmo read-only

Antes de despachar, guarde o pré-estado:

```bash
git rev-parse HEAD > /tmp/pre-head.txt
git status --short > /tmp/pre-state.txt
```

Depois que o relatório chegar:

```bash
git rev-parse HEAD                     # tem que ser idêntico
git status --short | diff - /tmp/pre-state.txt   # tem que ser vazio
```

Se algo divergir, diga isso ao usuário com o diff, sem suavizar.

**Verifique de novo ao terminar de aplicar o relatório.** Uma checagem feita no instante do `worker_done` não cobre o que o agente escreveu depois dela. Se aparecer arquivo modificado que não é seu, reporte, não commite, e não atribua a si.

## Ao receber o relatório: não valide por deferência

Este é o passo que mais gera valor, e o mais fácil de pular.

1. **Verifique cada bloqueador você mesmo.** Abra o arquivo. Rode a query. Um revisor competente ainda erra de tamanho.
2. **Separe buraco real de decisão de negócio.** "O resolver descarta a segunda sessão do mesmo dia" é buraco: o código faz isso, está em `arquivo:linha`, e o plano ignorava. "Devemos suportar o terceiro idioma agora?" é decisão de negócio: não tem resposta técnica.
3. **Redimensione com dado.** Um bloqueador que protege zero usuário hoje não é bloqueador. Traga a contagem, decida com ela, e registre o número no documento para a próxima pessoa não reabrir a discussão.
4. **Leve as decisões de negócio ao usuário**, com resumo curto e recomendação explícita. Não decida por ele, e não empurre a decisão para dentro do plano disfarçada de detalhe técnico.
5. **Aplique o que sobrou** na spec e no plano, e diga ao usuário onde você discordou do revisor e por quê.
6. **Conte por custo e registre no plano:** "N bloqueadores: n documentais, n decisão do usuário,
   n redesenho". É esse número, não o veredito, que diz se a spec e o plano estavam sãos.
7. **Feche a triagem com uma linha por skill:** o que entra em qual arquivo, ou *"nada entra,
   porque X"*. Sem a linha, a lição fica no relatório e a próxima spec paga de novo. Medido: as
   lições de duas revisões de 2026-09-08 e 2026-09-09 ficaram só nos relatórios, sem decisão
   registrada de entrar ou não.

## Custo

Uma revisão dessas consome um turno inteiro de um modelo caro e costuma levar dezenas de minutos. Para feature pequena, não paga. Diga isso ao usuário quando ele pedir uma revisão para algo que não precisa.
