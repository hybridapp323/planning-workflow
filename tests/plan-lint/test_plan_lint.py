"""Testes do plan-lint.

O caso limpo (fixtures/plano-limpo.md, sobre fixtures/repo) tem que passar sem achado.
Cada teste de defeito injeta UM defeito nele e exige que a checagem certa dispare.
Rodar: python3 -m unittest discover -s tests/plan-lint
Para testar uma cópia alterada do script (prova de que o teste pega a regressão):
PLAN_LINT=<caminho do script> python3 -m unittest discover -s tests/plan-lint
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

AQUI = Path(__file__).resolve().parent
LINT = Path(os.environ.get("PLAN_LINT") or AQUI.parents[1] / "skills/power-plans/scripts/plan-lint.py")
REPO = AQUI / "fixtures" / "repo"
LIMPO = (AQUI / "fixtures" / "plano-limpo.md").read_text(encoding="utf-8")


def _carrega_script():
    spec = importlib.util.spec_from_file_location("plan_lint", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PL = _carrega_script()


def sub(texto, antigo, novo):
    """Troca um trecho do plano limpo. Falha se o trecho não existir, para o teste não passar em silêncio."""
    assert antigo in texto, f"trecho não achado no plano limpo: {antigo!r}"
    return texto.replace(antigo, novo)


def rodar(texto, *extra, cwd=None):
    """Roda o CLI num plano temporário, com a raiz de fixture. Devolve (código, saída JSON)."""
    with tempfile.TemporaryDirectory() as tmp:
        plano = Path(tmp) / "plano.md"
        plano.write_text(texto, encoding="utf-8")
        r = subprocess.run([sys.executable, str(LINT), str(plano), "--root", str(REPO), "--json", *extra],
                           capture_output=True, text=True, cwd=cwd)
    if r.returncode not in (0, 1):
        raise AssertionError(f"CLI saiu com {r.returncode}: {r.stderr}")
    return r.returncode, json.loads(r.stdout)


class Asserts(unittest.TestCase):
    def achados(self, d, checagem, sev=None, trecho=None):
        return [a for a in d["achados"]
                if a["checagem"] == checagem
                and (sev is None or a["severidade"] == sev)
                and (trecho is None or trecho in a["mensagem"])]

    def assertAchou(self, d, checagem, sev="erro", trecho=None):
        hits = self.achados(d, checagem, sev, trecho)
        self.assertTrue(hits, f"faltou {sev} {checagem} ({trecho!r}); achados: {d['achados']}")

    def assertSem(self, d, checagem, trecho=None):
        hits = self.achados(d, checagem, None, trecho)
        self.assertFalse(hits, f"não devia haver {checagem} ({trecho!r}): {hits}")


class Unitarios(unittest.TestCase):
    def test_split_row_respeita_crase_e_pipe_escapado(self):
        self.assertEqual(PL.split_row("| a | `x|y` | b |"), ["a", "`x|y`", "b"])
        self.assertEqual(PL.split_row("| a \\| b | c |"), ["a | b", "c"])

    def test_split_row_mantem_celula_vazia_no_fim(self):
        self.assertEqual(PL.split_row("| a | |"), ["a", ""])

    def test_ids_fr_nao_casam_prefixo_e_expandem_barra(self):
        self.assertEqual(PL.ids_fr("FR-10"), ["FR-10"])
        self.assertEqual(PL.ids_fr("cobre FR-1/2 e FR-3a"), ["FR-1", "FR-2", "FR-3a"])
        self.assertNotIn("FR-1", PL.ids_fr("só FR-10 aqui"))

    def test_parse_ref(self):
        self.assertEqual(PL.parse_ref("`x/y.ts:3-5`"), {"caminho": "x/y.ts", "a": 3, "b": 5})
        self.assertIsNone(PL.parse_ref("v1.2"))
        self.assertIsNone(PL.parse_ref("GET/POST"))
        self.assertIsNone(PL.parse_ref("src/*.ts"))
        self.assertIsNone(PL.parse_ref("`.../historico.ts:448-458`"))
        self.assertEqual(PL.parse_ref("docs/fichas/")["caminho"], "docs/fichas")

    def test_frs_da_spec_pula_requisito_removido(self):
        texto = (REPO / "docs/specs/feito/exemplo-design.md").read_text(encoding="utf-8")
        ids, por_titulo = PL.frs_da_spec(texto)
        self.assertEqual(ids, ["FR-1", "FR-2", "FR-10"])
        self.assertTrue(por_titulo)


class PlanoLimpo(Asserts):
    def test_plano_limpo_passa_sem_achado(self):
        code, d = rodar(LIMPO)
        self.assertEqual(code, 0, d["achados"])
        self.assertEqual(d["achados"], [])


class Defeitos(Asserts):
    def test_fr_ausente_nao_casa_em_fr10(self):
        code, d = rodar(re.sub(r"\bFR-1\b", "FR-9", LIMPO))
        self.assertEqual(code, 1)
        self.assertAchou(d, "fr-sem-tarefa", trecho="FR-1 da spec")
        self.assertSem(d, "fr-sem-tarefa", trecho="FR-10")

    def test_caminho_inexistente_na_ownership(self):
        texto = sub(LIMPO, "| `app/functions/motor/_lib/alpha.ts` + `_test.ts` | T1 |",
                    "| `app/functions/motor/_lib/alfa.ts` + `_test.ts` | T1 |")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "caminho-inexistente", trecho="alfa.ts")
        self.assertAchou(d, "caminho-inexistente", trecho="alfa_test.ts")

    def test_sufixo_de_teste_resolve_contra_o_arquivo_anterior(self):
        code, d = rodar(LIMPO)
        self.assertSem(d, "caminho-inexistente", trecho="_test.ts")

    def test_irmao_de_linha_novo_inexistente(self):
        texto = sub(LIMPO, "(irmão: `_lib/beta.ts`", "(irmão: `_lib/nao-existe.ts`")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "caminho-inexistente", trecho="nao-existe")
        self.assertSem(d, "caminho-inexistente", trecho="gamma")

    def test_nome_nu_em_lista_da_mesma_pasta_conta_como_planejado(self):
        # Lista de NOVO com nome nu (`novo-cmd-2.mjs`) é da pasta do primeiro; o comando que o usa não erra.
        texto = sub(LIMPO, "| NOVO `scripts/novo-cmd.mjs` (irmão: `scripts/run-check.mjs`) | T3 |",
                    "| NOVO `scripts/novo-cmd.mjs`, `novo-cmd-2.mjs` (irmão: `scripts/run-check.mjs`) | T3 |")
        texto = sub(texto, "bash scripts/deploy.sh\n```", "bash scripts/deploy.sh\nnode scripts/novo-cmd-2.mjs\n```")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertSem(d, "comando-inexistente")

    def test_novo_sem_irmao_e_aviso(self):
        texto = sub(LIMPO, "| NOVO `scripts/novo-cmd.mjs` (irmão: `scripts/run-check.mjs`) | T3 |",
                    "| NOVO `scripts/novo-cmd.mjs` | T3 |")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "novo-sem-irmao", sev="aviso")

    def test_lido_inexistente(self):
        code, d = rodar(sub(LIMPO, "[LIDO: src/modulo.ts:4]", "[LIDO: src/nao.ts:4]"))
        self.assertEqual(code, 1)
        self.assertAchou(d, "caminho-inexistente", trecho="src/nao.ts")

    def test_linha_fora_do_arquivo(self):
        texto = sub(LIMPO, "[LIDO: app/functions/motor/_lib/alpha.ts:3-5]",
                    "[LIDO: app/functions/motor/_lib/alpha.ts:3-99]")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "linha-fora-do-arquivo", trecho="linha 99")

    def test_suposto_sem_pare_sustenta_tarefa_e_erro(self):
        code, d = rodar(sub(LIMPO, "Se der diferente, PARE e escale.", "Se der diferente, siga."))
        self.assertEqual(code, 1)
        self.assertAchou(d, "suposto-sustenta-tarefa", trecho="T2")

    def test_suposto_com_escale_conta_como_parada(self):
        code, d = rodar(sub(LIMPO, "Se der diferente, PARE e escale.", "Se der diferente, escale para o responsável."))
        self.assertEqual(code, 0, d["achados"])
        self.assertSem(d, "suposto-sustenta-tarefa")

    def test_tarefa_sem_cobre_e_erro(self):
        code, d = rodar(sub(LIMPO, "**Cobre:** FR-10.\n", ""))
        self.assertEqual(code, 1)
        self.assertAchou(d, "tarefa-incompleta", trecho="T2 sem 'Cobre'")

    def test_cobre_por_fr_no_titulo_e_aceito(self):
        texto = sub(LIMPO, "**Cobre:** FR-10.\n", "")
        texto = sub(texto, "### T2 — gama · **Média** · depende de T1", "### T2 — gama (FR-10) · **Média** · depende de T1")
        code, d = rodar(texto)
        self.assertSem(d, "tarefa-incompleta", trecho="T2 sem 'Cobre'")

    def test_tarefa_sem_pronto_quando_e_erro(self):
        texto = sub(LIMPO, "**Pronto quando:** **Dado** um lead, **quando** o alfa roda, **então** a coisa um acontece.\n", "")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "tarefa-incompleta", trecho="T1 sem 'Pronto quando'")

    def test_celula_vazia_na_rastreabilidade(self):
        texto = sub(LIMPO, "| FR-2 | dado um lead, quando o alfa roda, então a coisa dois | T1 |",
                    "| FR-2 | dado um lead, quando o alfa roda, então a coisa dois |  |")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "celula-vazia", trecho="'Tarefa' vazia")

    def test_celula_vazia_no_tracado(self):
        texto = sub(LIMPO, "| o usuário vê a coisa dez |", "|  |")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "celula-vazia", trecho="Efeito observável")

    def test_celula_extra_e_aviso_de_tabela_malformada_nao_erro(self):
        texto = sub(LIMPO, "| o usuário vê a coisa dois |", "| o usuário vê a coisa dois | extra |")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "tabela-malformada", sev="aviso")

    def test_dono_duplicado_com_donos_diferentes_e_erro(self):
        texto = sub(LIMPO, "| `src/modulo.ts` | T3 |", "| `src/modulo.ts` | T3 |\n| `src/modulo.ts` | T9 |")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "arquivo-dois-donos", trecho="src/modulo.ts")

    def test_linha_repetida_com_mesmo_dono_e_aviso(self):
        texto = sub(LIMPO, "| `src/modulo.ts` | T3 |", "| `src/modulo.ts` | T3 |\n| `src/modulo.ts` | T3 |")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "arquivo-linha-repetida", sev="aviso")

    def test_arquivo_dividido_com_conciliacao_escrita_e_aviso(self):
        texto = sub(LIMPO, "| `src/modulo.ts` | T3 |",
                    "| `src/modulo.ts` | T3 (W1) |\n| `src/modulo.ts` | T9 (W2; concilia no rebase com T3) |")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "arquivo-compartilhado-declarado", sev="aviso")

    def test_comando_de_bloco_inexistente(self):
        code, d = rodar(sub(LIMPO, "bash scripts/deploy.sh\n```", "bash scripts/deploy.sh\nnode scripts/nao-existe.mjs\n```"))
        self.assertEqual(code, 1)
        self.assertAchou(d, "comando-inexistente", trecho="nao-existe")

    def test_comando_em_crase_inexistente(self):
        texto = sub(LIMPO, "confira `scripts/novo-cmd.mjs`, que o T3 cria.", "confira `scripts/sumiu.mjs`, que o T3 cria.")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "comando-inexistente", trecho="sumiu")

    def test_script_planejado_pelo_plano_nao_erra(self):
        code, d = rodar(LIMPO)
        self.assertSem(d, "comando-inexistente")

    def test_cd_muda_a_pasta_de_onde_o_script_e_lido(self):
        texto = sub(LIMPO, "FOO=1 node scripts/run-check.mjs\n", "cd app/functions/motor\nnode scripts/run-check.mjs\n")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertAchou(d, "comando-inexistente", trecho="app/functions/motor/scripts/run-check.mjs")

    def test_placeholder_tbd_e_aviso(self):
        code, d = rodar(sub(LIMPO, "Ondas: W1", "TBD Ondas: W1"))
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "placeholder", sev="aviso")

    def test_termo_aposentado_e_erro(self):
        texto = sub(LIMPO, "Ondas: W1", "Ondas: supervisor W1")
        code, d = rodar(texto, "--retired", "supervisor")
        self.assertEqual(code, 1)
        self.assertAchou(d, "termo-aposentado", trecho="supervisor")

    def test_secao_ausente_vira_aviso_e_nao_erro(self):
        i, j = LIMPO.index("## 0.1 Afirmações"), LIMPO.index("## 1. Níveis")
        code, d = rodar(LIMPO[:i] + LIMPO[j:])
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "secao-nao-encontrada", sev="aviso", trecho="afirmações de carga")

    def test_spec_que_mudou_de_pasta_de_estado_e_achada(self):
        texto = sub(LIMPO, "`docs/specs/feito/exemplo-design.md`", "`docs/specs/a-fazer/exemplo-design.md`")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertSem(d, "spec-nao-encontrada")

    def test_spec_inexistente_vira_aviso(self):
        texto = sub(LIMPO, "`docs/specs/feito/exemplo-design.md`", "`docs/specs/feito/nao-existe.md`")
        code, d = rodar(texto)
        self.assertEqual(code, 0, d["achados"])
        self.assertAchou(d, "spec-nao-encontrada", sev="aviso")

    def test_json_conta_por_checagem(self):
        texto = sub(LIMPO, "Se der diferente, PARE e escale.", "Se der diferente, siga.")
        texto = sub(texto, "Ondas: W1", "TBD Ondas: W1")
        code, d = rodar(texto)
        self.assertEqual(code, 1)
        self.assertEqual(d["erros"], 1)
        self.assertEqual(d["por_checagem"]["suposto-sustenta-tarefa"], {"erro": 1, "aviso": 0})
        self.assertEqual(d["por_checagem"]["placeholder"], {"erro": 0, "aviso": 1})

    def test_spec_por_flag_sem_cabecalho_roda_a_checagem_de_fr(self):
        sem_cabecalho = sub(LIMPO, "**Spec:** `docs/specs/feito/exemplo-design.md`\n", "")
        code, d = rodar(sem_cabecalho, "--spec", "docs/specs/feito/exemplo-design.md")
        self.assertEqual(code, 0, d["achados"])
        self.assertEqual(d["spec"], str(REPO / "docs/specs/feito/exemplo-design.md"))
        code, d = rodar(sub(sem_cabecalho, "FR-2", "FR-7"), "--spec", "docs/specs/feito/exemplo-design.md")
        self.assertEqual(code, 1)
        self.assertAchou(d, "fr-sem-tarefa", trecho="FR-2 da spec")

    def test_spec_relativa_ao_cwd_e_aceita(self):
        # Raiz vazia: só o cwd (a fixture) acha a spec. Sem o candidato de cwd, a spec não é achada.
        sem_cabecalho = sub(LIMPO, "**Spec:** `docs/specs/feito/exemplo-design.md`\n", "")
        with tempfile.TemporaryDirectory() as vazia, tempfile.TemporaryDirectory() as tmp:
            plano = Path(tmp) / "plano.md"
            plano.write_text(sem_cabecalho, encoding="utf-8")
            r = subprocess.run([sys.executable, str(LINT), str(plano), "--root", vazia, "--json",
                                "--spec", "docs/specs/feito/exemplo-design.md"],
                               capture_output=True, text=True, cwd=REPO)
        d = json.loads(r.stdout)
        self.assertEqual(d["spec"], str(REPO / "docs/specs/feito/exemplo-design.md"))
        self.assertSem(d, "spec-nao-encontrada")

    def test_spec_passada_inexistente_sai_com_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            plano = Path(tmp) / "plano.md"
            plano.write_text(LIMPO, encoding="utf-8")
            r = subprocess.run([sys.executable, str(LINT), str(plano), "--root", str(REPO),
                                "--spec", "docs/specs/feito/nao-existe.md"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--spec não encontrado", r.stderr)

    def test_plano_ilegivel_sai_com_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(LINT), str(Path(tmp) / "nao-existe.md")],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
