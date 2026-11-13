# Escala: o detalhe e as medições

Referência da skill `power-plans`. Leia ao escolher a escala e ao escrever um plano mínimo. A tabela que vale é a do `SKILL.md`; aqui estão o plano mínimo, a regra de família e as medições que sustentam o critério.

## Primeira decisão: o portão de escala

Antes de qualquer coisa, decida quanto aparato essa feature merece. Um plano de 15 tarefas para uma mudança de duas telas é imposto, não rigor.

**O critério é o RISCO da mudança, não a superfície que ela toca.** Publicar uma função ou um
serviço se desfaz republicando a versão anterior; isso sozinho não sobe o nível. O que sobe é o que
não se desfaz, o que atravessa donos e o que protege dado de terceiros.

| Escala | Quando | O que fazer |
| --- | --- | --- |
| **Mínima** | Um defeito ou uma família, um dono da decisão, nenhum contrato novo entre tarefas, **sem** migração de schema e sem escrita em dado de produção, reversível por revert + republicação | Plano mínimo (abaixo) e implemente. Sem ondas, sem gate. |
| **Parcial** | Duas ou mais tarefas com donos diferentes, **ou** um contrato que uma tarefa produz e outra consome | Níveis, ownership de arquivo e `Pronto quando` por tarefa. Sem ondas nem gate. |
| **Completa** | Migração, escrita em dado de produção ou outro passo irreversível, **ou** invariante de segurança, permissão ou isolamento entre clientes, **ou** trabalho genuinamente paralelo em arquivos disjuntos | Fases 0 a 4, com um gate antes do passo irreversível. |

Diga ao usuário qual dos três você escolheu, e por quê, antes de escrever o plano. Se ele discordar, ele corrige agora e não depois de vinte minutos de documento.

Medido em 60 dias de um projeto que publica a mesma função várias vezes por dia: o critério antigo
("toca função publicada ou deploy → aparato completo") mandou ondas e gate para consertos de um
arquivo, e a documentação de ciclo somou 227 mil linhas contra 92 mil de código de produção;
um único ciclo produziu 13,8 mil linhas em 127 arquivos para 45 requisitos, e outro já tinha 10,6
mil linhas de documento contra 2,4 mil de código antes de executar.

### O plano mínimo: sai a cerimônia, fica a prova

Escala mínima não é "sem prova". O plano cabe numa tela e tem, cada um com `arquivo:linha` ou
consulta:

1. **Causa**, com a evidência que a mostra (não o sintoma do relatório).
2. **Arquivos** que mudam.
3. **Quem mais lê ou emite isto:** uma linha com os outros consumidores e emissores do que muda.
   Uma mudança de um arquivo num módulo compartilhado alcança todos os chamadores dele.
4. **Teste que falha com o fix neutralizado.**
5. **Camada de prova** (ver *Critério de pronto*): a mais barata que exercita o consumidor real.
6. **Publicação e rollback:** o comando e a versão para onde se volta.

Se para escrever o item 3 você precisar de mais de um dono ou de um contrato novo, a escala não era
mínima: suba.

### Um pedido, uma família

Quando a entrada é um relatório com vários achados (auditoria, triagem, lista de bugs), agrupe por
**família**: achados que têm a mesma causa e o mesmo dono da decisão. **Um plano por família**, com
a família no título. Plano que mistura famílias sem relação é recortado antes de escrever: cada
família a mais multiplica leituras, contratos, fixtures e rodadas de gate, e nenhuma delas fica
mais bem consertada por estar junto. O urgente sai já; o resto segue a cadência que o projeto
definir. Vale para a spec que chega: spec que junta famílias sem relação é recortada no mesmo
passo (Fase 0, *Validar a spec*), e cada família segue com o seu plano.

Número de requisitos é **alerta que vira pergunta**: passou de uns dez, ou a spec se divide em
trilhas que ela mesma chama de independentes, recorte em um plano por família. Se o usuário pediu
tudo junto, isso decide a entrega, não o número de planos: pergunte, com o custo à mostra, se o
trabalho segue em um plano por trilha com a entrega combinada no fim, ou num plano só. Plano
único com mais de uma família fica escrito como decisão dele, e o pré-voo roda um verificador
por trilha (medição em `pre-voo.md`).
Mudanças que precisam ser atômicas ficam juntas mesmo assim, e o plano diz por quê. Medido no mesmo
projeto: requisitos por ciclo subiram de 5 para 45 em um mês, sempre juntando o relatório inteiro.
