#!/usr/bin/env python3
"""plan-lint: pré-voo mecânico de um plano do power-plans.

Confere só o que se confere sem ler o sentido: FR da spec que o plano não cita,
caminhos e linhas citados que não existem, tabelas obrigatórias com célula vazia,
tarefa sem "Pronto quando" ou "Cobre", [SUPOSTO] sustentando tarefa sem PARE,
script dos passos do coordenador que não existe, placeholders e termos aposentados.
Se a tarefa está certa continua sendo julgamento de quem revisa.

Uso: plan-lint.py <plano.md | pasta-do-plano> [--spec SPEC] [--root RAIZ]
                  [--retired termo1,termo2] [--json]
Saída: 0 sem erro, 1 com erro, 2 uso ou plano ilegível.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path

ERRO = "erro"
AVISO = "aviso"

# Severidade fixa por checagem. Erro reprova; aviso não.
SEVERIDADE = {
    "fr-sem-tarefa": ERRO,
    "caminho-inexistente": ERRO,
    "caminho-ambiguo": AVISO,
    "linha-fora-do-arquivo": ERRO,
    "suposto-sustenta-tarefa": ERRO,
    "tarefa-incompleta": ERRO,
    "celula-vazia": ERRO,
    "arquivo-dois-donos": ERRO,
    "arquivo-compartilhado-declarado": AVISO,
    "arquivo-linha-repetida": AVISO,
    "novo-sem-irmao": AVISO,
    "comando-inexistente": ERRO,
    "placeholder": AVISO,
    "termo-aposentado": ERRO,
    "tabela-malformada": AVISO,
    "secao-nao-encontrada": AVISO,
    "spec-nao-encontrada": AVISO,
}

CERCA_RE = re.compile(r"^\s*(```|~~~)")
TITULO_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
SPEC_CAB_RE = re.compile(r"\*\*Spec:\*\*\s*`([^`]+)`")
ASSUME_RE = re.compile(r"\*\*\s*Assume que", re.IGNORECASE)
ROTULO_RE = re.compile(r"^\s*\*\*[^*]{2,60}:\*\*|^\s*\*\*[^*]{2,60}\*\*:")
TAREFA_ID_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)")
FR_TITULO_RE = re.compile(r"^#{1,6}\s+\**\s*(FR-\d+[a-z]?)\b")
FR_RE = re.compile(r"(?<![A-Za-z0-9])FR-\d+[a-z]?(?:\s*[/,]\s*\d+[a-z]?)*(?![A-Za-z0-9])")
CRASE_RE = re.compile(r"`([^`]+)`")
LIDO_RE = re.compile(r"\[LIDO:\s*([^\]]*)\]")
SUPOSTO_RE = re.compile(r"\[SUPOSTO\b")
LINHA_RE = re.compile(r"^(.+?)(?::(\d+)(?:-(\d+))?)?$")
EXT_RE = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,9}$")
DONO_ID_RE = re.compile(r"\b[A-Z]{1,3}(?:-[A-Z]{0,2})?\d+[a-z]?\b")
ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
INTERPRETADORES = {"node", "bash", "sh", "python", "python3", "deno", "bun", "tsx", "ts-node"}
EXT_SCRIPT = (".sh", ".mjs", ".cjs", ".js", ".ts", ".tsx", ".py")
ESTADOS = ("a-fazer", "em-validacao", "feito")
IGNORAR = {".git", "node_modules", ".venv", "__pycache__"}


# ---------------------------------------------------------------- texto e tabelas

def split_row(linha):
    """Quebra uma linha de tabela em células. `|` dentro de crase não quebra; `\\|` é pipe literal."""
    s = linha.strip()
    if s.startswith("|"):
        s = s[1:]
    s = s.rstrip()
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cels, atual, crase, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and s[i + 1:i + 2] == "|":
            atual.append("|")
            i += 2
            continue
        if c == "`":
            crase = not crase
        if c == "|" and not crase:
            cels.append("".join(atual).strip())
            atual = []
        else:
            atual.append(c)
        i += 1
    cels.append("".join(atual).strip())
    return cels


def e_separador(linha):
    s = linha.strip()
    return s.startswith("|") and "-" in s and re.fullmatch(r"[\s|:\-]+", s) is not None


def tipo_tabela(tab):
    cab = [c.lower() for c in tab["cab"]]
    if not cab:
        return None
    if cab[0] in ("arquivo", "arquivos") and len(cab) >= 2 and cab[1].startswith("dono"):
        return "ownership"
    if cab[0] in ("#", "id") and len(cab) >= 2 and "afirma" in cab[1]:
        return "afirmacoes"
    if cab[0] == "fr" and any(re.search(r"nasce|transporta|decide|emite|efeito", c) for c in cab[1:]):
        return "tracado"
    if cab[0] == "fr" and cab[-1].startswith("tarefa"):
        return "rastreabilidade"
    if any(c.startswith(("nível", "nivel")) for c in cab) and "modelo" in cab:
        return "niveis"
    return None


def zona_tarefas(h2):
    hl = h2.lower()
    if "rastreab" in hl:
        return False
    return re.match(r"5(\.\d+)?\b", h2) is not None or "tarefa" in hl


def zona_coordenador(h2):
    return "coordenador" in h2.lower() or re.match(r"6(\.\d+)?\b", h2) is not None


class Plano:
    def __init__(self, texto):
        self.linhas = texto.splitlines()
        self.cercado = set()   # números de linha dentro de cerca de código
        self.titulos = []      # (n, nivel, titulo, h2)
        self.tabelas = []      # dict(n, cab, linhas=[(n, celulas)], h2)
        self.blocos = []       # dict(n, h2, linhas=[(n, texto)])
        self.h2_linha = {}     # n -> título do ## mais recente
        self._varre()

    def _varre(self):
        h2, bloco, i, total = "", None, 0, len(self.linhas)
        while i < total:
            n, ln = i + 1, self.linhas[i]
            self.h2_linha[n] = h2
            if CERCA_RE.match(ln):
                if bloco is None:
                    bloco = {"n": n, "h2": h2, "linhas": []}
                else:
                    self.blocos.append(bloco)
                    bloco = None
                self.cercado.add(n)
                i += 1
                continue
            if bloco is not None:
                self.cercado.add(n)
                bloco["linhas"].append((n, ln))
                i += 1
                continue
            m = TITULO_RE.match(ln)
            if m:
                nivel, titulo = len(m.group(1)), m.group(2)
                if nivel == 2:
                    h2 = titulo
                self.titulos.append((n, nivel, titulo, h2))
                i += 1
                continue
            if ln.lstrip().startswith("|") and i + 1 < total and e_separador(self.linhas[i + 1]):
                cab = split_row(ln)
                linhas, j = [], i + 2
                while j < total and self.linhas[j].lstrip().startswith("|") and not CERCA_RE.match(self.linhas[j]):
                    linhas.append((j + 1, split_row(self.linhas[j])))
                    j += 1
                self.tabelas.append({"n": n, "cab": cab, "linhas": linhas, "h2": h2})
                i = j
                continue
            i += 1

    def prosa(self):
        return [(n, ln) for n, ln in enumerate(self.linhas, 1) if n not in self.cercado]

    def tabelas_do_tipo(self, tipo):
        return [t for t in self.tabelas if tipo_tabela(t) == tipo]

    def tarefas(self):
        """Blocos ### de tarefa dentro da seção de tarefas. Gate (S1), coordenador (C0) e passo manual ficam fora."""
        out, total = [], len(self.linhas)
        for k, (n, nivel, titulo, h2) in enumerate(self.titulos):
            if nivel != 3 or not zona_tarefas(h2):
                continue
            m = TAREFA_ID_RE.match(titulo)
            if not m:
                continue
            tid = m.group(1)
            if not re.search(r"\d", tid) or re.match(r"(S|C)\d|ADV", tid):
                continue
            if re.search(r"gate|advisor|coordenador|passo do", titulo, re.IGNORECASE):
                continue
            fim = total
            for n2, nivel2, _, _ in self.titulos[k + 1:]:
                if nivel2 <= 3:
                    fim = n2 - 1
                    break
            texto = [(x, self.linhas[x - 1]) for x in range(n, fim + 1)]
            out.append({"id": tid, "n": n, "texto": texto})
        return out


# ---------------------------------------------------------------- referências a arquivo

def parse_ref(token):
    """Caminho de arquivo (com linha opcional) ou None se o token não parece caminho."""
    t = token.strip().strip("`").strip().rstrip(".,;:")
    if not t or re.search(r"[\s*<>{}\[\]$|\\\"'…]", t) or "..." in t or "://" in t or t[0] in "/~@#-(":
        return None
    m = LINHA_RE.match(t)
    caminho, a, b = m.group(1), m.group(2), m.group(3)
    diretorio = caminho.endswith("/")
    caminho = caminho.rstrip("/")
    if caminho.startswith("./"):
        caminho = caminho[2:]
    if not caminho or ".." in caminho.split("/"):
        return None
    if not (EXT_RE.search(caminho.split("/")[-1]) or diretorio):
        return None
    return {"caminho": caminho, "a": int(a) if a else None, "b": int(b) if b else None}


def ids_fr(texto):
    out = []
    for m in FR_RE.finditer(texto):
        for num in re.findall(r"\d+[a-z]?", m.group(0)[3:]):
            out.append("FR-" + num)
    return out


def _git_arquivos(raiz):
    """Arquivos rastreados ou não ignorados, se raiz for a raiz do repositório; senão None."""
    try:
        topo = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True)
        if topo.returncode != 0 or Path(topo.stdout.strip()).resolve() != raiz.resolve():
            return None
        r = subprocess.run(["git", "-C", str(raiz), "ls-files", "-z", "-co", "--exclude-standard"],
                           capture_output=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]


def _walk_arquivos(raiz):
    out = []
    for dp, dns, fns in os.walk(raiz):
        dns[:] = [d for d in dns if d not in IGNORAR]
        for f in fns:
            out.append(os.path.relpath(os.path.join(dp, f), raiz).replace(os.sep, "/"))
    return out


class Repo:
    def __init__(self, raiz):
        self.raiz = raiz
        self._idx = None
        self._linhas = {}

    def existe(self, rel):
        return (self.raiz / rel).exists()

    def _indice(self):
        if self._idx is None:
            arquivos = _git_arquivos(self.raiz)
            if arquivos is None:
                arquivos = _walk_arquivos(self.raiz)
            idx = set(arquivos)
            for f in arquivos:
                partes = f.split("/")
                for k in range(1, len(partes)):
                    idx.add("/".join(partes[:k]))
            self._idx = idx
        return self._idx

    def resolve(self, rel, base=None):
        """(casamentos, exato). Ordem: caminho exato, relativo a base, sufixo único no repositório."""
        if self.existe(rel):
            return [rel], True
        if base:
            cand = posixpath.normpath(posixpath.join(base, rel))
            if not cand.startswith("..") and self.existe(cand):
                return [cand], True
        suf = "/" + rel
        return [f for f in self._indice() if f.endswith(suf)], False

    def linhas(self, rel):
        if rel not in self._linhas:
            alvo = self.raiz / rel
            if alvo.is_file():
                self._linhas[rel] = len(alvo.read_text(encoding="utf-8", errors="replace").splitlines())
            else:
                self._linhas[rel] = None
        return self._linhas[rel]


# ---------------------------------------------------------------- relatório

class Relatorio:
    def __init__(self):
        self.achados = []
        self.nao_conferidos = 0

    def add(self, checagem, linha, msg):
        self.achados.append({"checagem": checagem, "severidade": SEVERIDADE[checagem],
                             "linha": linha, "mensagem": msg})

    def por_checagem(self):
        out = {}
        for a in self.achados:
            c = out.setdefault(a["checagem"], {"erro": 0, "aviso": 0})
            c["erro" if a["severidade"] == ERRO else "aviso"] += 1
        return out


def formata(rel, rotulo):
    linhas = []
    for a in rel.achados:
        sev = "ERRO " if a["severidade"] == ERRO else "AVISO"
        linhas.append(f"{sev} {rotulo}:{a['linha']} {a['checagem']}: {a['mensagem']}")
    erros = sum(1 for a in rel.achados if a["severidade"] == ERRO)
    linhas.append(f"Resumo: {erros} erro(s), {len(rel.achados) - erros} aviso(s).")
    if rel.nao_conferidos:
        linhas.append(f"Comandos não conferidos (cd não resolvido): {rel.nao_conferidos}")
    return "\n".join(linhas)


# ---------------------------------------------------------------- checagens

def cabecalho_spec(plano):
    for ln in plano.linhas[:40]:
        m = SPEC_CAB_RE.search(ln)
        if m:
            return m.group(1).strip()
    return None


def resolve_spec(ref, pasta_plano, raiz):
    """Caminho da spec: relativo ao cwd, à raiz ou ao plano. Se mudou de pasta de estado, tenta as irmãs."""
    base = [Path(ref)] if Path(ref).is_absolute() else [Path.cwd() / ref, raiz / ref, pasta_plano / ref]
    partes = ref.split("/")
    for i, p in enumerate(partes):
        if p in ESTADOS:
            for est in ESTADOS:
                nova = partes[:]
                nova[i] = est
                base.append(raiz / "/".join(nova))
    for c in base:
        if c.is_file() or (c.is_dir() and any(c.glob("*.md"))):
            return c
    return None


def ler_spec(caminho):
    if caminho.is_file():
        return caminho.read_text(encoding="utf-8", errors="replace")
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in sorted(caminho.glob("*.md")))


def frs_da_spec(texto):
    """(ids exigidos, veio_de_titulo). Requisito marcado removido não é exigido."""
    ids, removidos = [], set()
    for ln in texto.splitlines():
        m = FR_TITULO_RE.match(ln)
        if m:
            fid = m.group(1)
            if re.search(r"remov", ln, re.IGNORECASE):
                removidos.add(fid)
            elif fid not in ids:
                ids.append(fid)
    if ids:
        return [i for i in ids if i not in removidos], True
    por_mencao = []
    for ln in texto.splitlines():
        if re.search(r"remov", ln, re.IGNORECASE):
            continue
        for fid in ids_fr(ln):
            if fid not in por_mencao:
                por_mencao.append(fid)
    return por_mencao, False


def check_fr(plano, texto_spec, rel):
    exigidos, por_titulo = frs_da_spec(texto_spec)
    if not exigidos:
        rel.add("secao-nao-encontrada", 0, "spec sem requisitos FR-n: nada a conferir no plano")
        return
    if not por_titulo:
        rel.add("secao-nao-encontrada", 0, "spec sem títulos FR-n: ids tirados de menções no texto")
    no_plano = set(ids_fr("\n".join(plano.linhas)))
    for fid in exigidos:
        if fid not in no_plano:
            rel.add("fr-sem-tarefa", 0, f"{fid} da spec não aparece no plano")


def check_tabelas(plano, rel):
    nomes = {"afirmacoes": "tabela de afirmações de carga (§0.1)",
             "ownership": "tabela de ownership (Arquivo | Dono)",
             "tracado": "traçado por requisito (§3.1)",
             "rastreabilidade": "rastreabilidade (§5.1)",
             "niveis": "níveis de complexidade (§1)"}
    for tipo, nome in nomes.items():
        if not plano.tabelas_do_tipo(tipo):
            rel.add("secao-nao-encontrada", 0, f"{nome} não encontrada")
    for tab in plano.tabelas:
        if tipo_tabela(tab) not in ("afirmacoes", "ownership", "tracado", "rastreabilidade"):
            continue
        for n, cels in tab["linhas"]:
            if len(cels) != len(tab["cab"]):
                rel.add("tabela-malformada", n, f"{len(cels)} células, cabeçalho tem {len(tab['cab'])}")
                continue
            for cab, val in zip(tab["cab"], cels):
                if not val:
                    rel.add("celula-vazia", n, f"coluna '{cab}' vazia")


def caminhos_da_celula(tokens, repo):
    """Refs de uma célula de ownership. Nome nu depois de um caminho é resolvido nesta ordem:
    sufixo do anterior (`x.ts` + `_test.ts`), pasta do anterior (lista `a/x.ts`, `y.ts`), raiz exata
    (`AGENTS.md`), arquivo único de mesmo nome no repositório. Sem achado, vale o composto, para o
    erro citar o caminho mais provável. Dois ou mais homônimos: `ambiguo`, que vira aviso."""
    out, anterior = [], None
    for tok in tokens:
        ref = parse_ref(tok)
        if ref is None:
            continue
        cam, cands, ambiguo = ref["caminho"], [ref["caminho"]], False
        if anterior and "/" not in cam:
            stem = posixpath.splitext(anterior)[0]
            cands = ([stem + cam] if cam[0] in "_." else []) + [posixpath.join(posixpath.dirname(anterior), cam)]
            best = next((c for c in cands if repo.existe(c)), None)
            if best is None and repo.existe(cam):
                best = cam
            if best is None:
                casa, _ = repo.resolve(cam)
                best = casa[0] if len(casa) == 1 else None
                ambiguo = len(casa) > 1
            cam = best or cands[0]
        out.append(dict(ref, caminho=cam, candidatos=cands, ambiguo=ambiguo))
        anterior = cam
    return out


def compartilhado_declarado(caminho, plano):
    """O plano divide o arquivo entre ondas e diz como concilia (ex.: W1 muda um trecho, W2 outro, rebase)."""
    base = posixpath.basename(caminho)
    return any(base in ln and re.search(r"concilia|trecho|rebase", ln, re.IGNORECASE)
               for _, ln in plano.prosa())


def check_ownership(plano, repo, rel):
    """Confere os caminhos da tabela de ownership. Devolve o conjunto de caminhos que o plano cria ou possui."""
    tabs = plano.tabelas_do_tipo("ownership")
    if not tabs:
        return set()  # o aviso de seção ausente sai em check_tabelas
    planejados, vistos = set(), {}
    for tab in tabs:
        for n, cels in tab["linhas"]:
            if len(cels) != len(tab["cab"]):
                continue
            arq, dono = cels[0], cels[1]
            novo = re.search(r"\bNOVO\b", arq) is not None
            principal = arq.split("(", 1)[0]
            tokens = CRASE_RE.findall(principal) or re.findall(r"[^\s,;]+", principal)
            refs = caminhos_da_celula(tokens, repo)
            irmao = None
            m = re.search(r"irm[ãa]o\b", arq, re.IGNORECASE)
            if m:
                cand = CRASE_RE.findall(arq[m.end():])
                irmao = parse_ref(cand[0]) if cand else None
            chave = tuple(sorted(set(DONO_ID_RE.findall(dono)))) or (dono,)
            for ref in refs:
                caminho = ref["caminho"]
                planejados.add(caminho)
                if novo:
                    planejados.update(ref["candidatos"])  # o script/arquivo que a linha NOVO cria
                achados, exato = repo.resolve(caminho)
                if novo:
                    if irmao is None:
                        rel.add("novo-sem-irmao", n, f"linha NOVO de `{caminho}` sem irmão citado")
                    else:
                        ach_i, exato_i = repo.resolve(irmao["caminho"], base=posixpath.dirname(caminho))
                        if not ach_i:
                            rel.add("caminho-inexistente", n, f"irmão `{irmao['caminho']}` de linha NOVO não existe")
                        elif len(ach_i) > 1 and not exato_i:
                            rel.add("caminho-ambiguo", n, f"irmão `{irmao['caminho']}` casa com {len(ach_i)} arquivos")
                elif ref["ambiguo"]:
                    rel.add("caminho-ambiguo", n, f"`{ref['candidatos'][0]}` casa com mais de um arquivo do repositório")
                elif not achados:
                    rel.add("caminho-inexistente", n, caminho)
                elif len(achados) > 1 and not exato:
                    rel.add("caminho-ambiguo", n, f"`{caminho}` casa com {len(achados)} arquivos")
                vistos.setdefault(caminho, []).append((n, chave))
    for caminho, lst in vistos.items():
        if len(lst) < 2:
            continue
        linhas = ", ".join(str(n) for n, _ in lst)
        if len({c for _, c in lst}) > 1:
            if compartilhado_declarado(caminho, plano):
                rel.add("arquivo-compartilhado-declarado", lst[1][0],
                        f"`{caminho}` nas linhas {linhas}: dividido entre donos com conciliação escrita")
            else:
                rel.add("arquivo-dois-donos", lst[1][0], f"`{caminho}` nas linhas {linhas} com donos diferentes")
        else:
            rel.add("arquivo-linha-repetida", lst[1][0], f"`{caminho}` repetido nas linhas {linhas}")
    return planejados


def checa_linha(repo, arq, ref, n, rel, vistos):
    chave = (n, ref["caminho"], ref["a"], ref["b"])
    if ref["a"] is None or chave in vistos:
        return
    vistos.add(chave)
    total = repo.linhas(arq)
    if total is None:
        return
    for v in (ref["a"], ref["b"]):
        if v is not None and v > total:
            rel.add("linha-fora-do-arquivo", n, f"{arq} tem {total} linhas, citada linha {v}")
            return


def check_lido_e_linhas(plano, repo, rel):
    vistos = set()
    for n, ln in plano.prosa():
        for m in LIDO_RE.finditer(ln):
            for seg in re.split(r"[;,]", m.group(1)):
                partes = seg.replace("`", " ").split()
                ref = parse_ref(partes[0]) if partes else None
                if ref is None:
                    continue
                achados, exato = repo.resolve(ref["caminho"])
                if not achados:
                    rel.add("caminho-inexistente", n, f"LIDO cita `{ref['caminho']}`, que não existe")
                elif len(achados) > 1 and not exato:
                    rel.add("caminho-ambiguo", n, f"LIDO `{ref['caminho']}` casa com {len(achados)} arquivos")
                else:
                    checa_linha(repo, achados[0], ref, n, rel, vistos)
        for crase in CRASE_RE.findall(ln):
            ref = parse_ref(crase)
            if ref is None or ref["a"] is None:
                continue
            achados, _ = repo.resolve(ref["caminho"])
            if len(achados) == 1:
                checa_linha(repo, achados[0], ref, n, rel, vistos)


def check_tarefas(plano, rel):
    tarefas = plano.tarefas()
    if not tarefas:
        rel.add("secao-nao-encontrada", 0, "seção de tarefas (### <id> em '## 5' ou 'Tarefas') não encontrada")
        return
    for t in tarefas:
        texto = "\n".join(ln for _, ln in t["texto"])
        if not re.search(r"Pronto quando", texto, re.IGNORECASE):
            rel.add("tarefa-incompleta", t["n"], f"{t['id']} sem 'Pronto quando'")
        # Cobre pode vir como rótulo, como **FR:**, como FR-n no título da tarefa, ou como "sem FR".
        cobre = (re.search(r"\bCobre\b", texto) or re.search(r"\*\*\s*FR\s*:", texto)
                 or ids_fr(t["texto"][0][1]) or re.search(r"sem FR", texto))
        if not cobre:
            rel.add("tarefa-incompleta", t["n"], f"{t['id']} sem 'Cobre'")
        hits, assume = [], False
        for n, ln in t["texto"]:
            if ASSUME_RE.search(ln):
                assume = True
            elif ROTULO_RE.match(ln):
                assume = False
            if assume and SUPOSTO_RE.search(ln):
                hits.append(n)
        # PARE literal ou a forma equivalente "escale / volta ao responsável" (a parada que o template pede).
        if hits and not re.search(r"\bpare\b|\bescal(?:e|ar|ado|ada)\b|\bvolta ao\b", texto, re.IGNORECASE):
            rel.add("suposto-sustenta-tarefa", hits[0], f"{t['id']}: [SUPOSTO] em 'Assume que' e sem PARE na tarefa")


def e_script(t):
    if "$" in t or re.search(r"[<*…]", t):
        return False
    return t.startswith("./") or ("/" in t and t.endswith(EXT_SCRIPT))


def script_de(toks):
    """Caminho do script que o comando executa, ou None se a linha não roda script do projeto."""
    primeiro = toks[0]
    if primeiro in INTERPRETADORES:
        resto = toks[1:]
        if primeiro == "deno":
            if not resto or resto[0] != "run":
                return None
            resto = resto[1:]
        for t in resto:
            if t.startswith("-"):
                continue
            return t if e_script(t) else None
        return None
    if primeiro.startswith("./") and "$" not in primeiro:
        return primeiro
    if "/" in primeiro and e_script(primeiro):
        return primeiro
    return None


def check_comandos(plano, repo, planejados, rel):
    blocos = [b for b in plano.blocos if zona_coordenador(b["h2"])]
    # Comando de linha de texto: crase em passo do coordenador que começa por interpretador, ./ ou scripts/.
    inline = [(n, c) for n, ln in plano.prosa() if zona_coordenador(plano.h2_linha.get(n, ""))
              for c in CRASE_RE.findall(ln)]
    if not blocos and not inline:
        rel.add("secao-nao-encontrada", 0, "passos do coordenador sem bloco de código nem comando em crase")
        return
    for n, cmd in inline:
        try:
            toks = shlex.split(cmd)
        except ValueError:
            continue
        while toks and ENV_RE.match(toks[0]):
            toks = toks[1:]
        if not toks or not (toks[0] in INTERPRETADORES or toks[0].startswith(("./", "scripts/"))):
            continue
        roteiro = script_de(toks)
        if roteiro is None or roteiro.startswith(".."):
            continue
        alvo = posixpath.normpath(roteiro)
        if alvo in planejados:
            continue
        achados, exato = repo.resolve(alvo)
        if not achados:
            rel.add("comando-inexistente", n, f"script `{alvo}` não existe e o plano não o cria")
        elif len(achados) > 1 and not exato:
            rel.add("caminho-ambiguo", n, f"script `{alvo}` casa com {len(achados)} arquivos")
    for b in blocos:
        cwd = ""
        for n, ln in b["linhas"]:
            s = re.sub(r"^\s*\$\s+", "", ln).strip()
            if not s or s.startswith("#"):
                continue
            for parte in re.split(r"&&|\|\||;", s):
                try:
                    toks = shlex.split(parte, comments=True)
                except ValueError:
                    continue
                while toks and ENV_RE.match(toks[0]):
                    toks = toks[1:]
                if not toks:
                    continue
                if toks[0] == "cd":
                    alvo = toks[1] if len(toks) > 1 else ""
                    if cwd is None or not alvo or re.search(r"[$~]", alvo):
                        cwd = None
                        continue
                    nova = posixpath.normpath(posixpath.join(cwd, alvo.rstrip("/") or "."))
                    cwd = nova if not nova.startswith("..") and repo.existe(nova) else None
                    continue
                roteiro = script_de(toks)
                if roteiro is None:
                    continue
                if cwd is None:
                    rel.nao_conferidos += 1
                    continue
                alvo = posixpath.normpath(posixpath.join(cwd, roteiro))
                if alvo in planejados or alvo.startswith(".."):
                    continue
                achados, exato = repo.resolve(alvo)
                if not achados:
                    rel.add("comando-inexistente", n, f"script `{alvo}` não existe e o plano não o cria")
                elif len(achados) > 1 and not exato:
                    rel.add("caminho-ambiguo", n, f"script `{alvo}` casa com {len(achados)} arquivos")


def check_placeholders(plano, rel):
    for n, ln in enumerate(plano.linhas, 1):
        if re.search(r"\bTBD\b", ln):
            rel.add("placeholder", n, "TBD")
        if re.search(r"a definir", ln, re.IGNORECASE):
            rel.add("placeholder", n, "'a definir'")
    for tab in plano.tabelas_do_tipo("niveis"):
        idx = [i for i, c in enumerate(tab["cab"]) if c.lower() == "modelo"][0]
        for n, cels in tab["linhas"]:
            if len(cels) > idx and "<MODELO_" not in cels[idx]:
                rel.add("placeholder", n, f"coluna Modelo sem <MODELO_…>: «{cels[idx]}»")


def check_termos(plano, termos, rel):
    for t in termos:
        rx = re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.IGNORECASE)
        for n, ln in enumerate(plano.linhas, 1):
            k = len(rx.findall(ln))
            if k:
                rel.add("termo-aposentado", n, f"'{t}' aparece {k}x")


def lint(caminho, spec_arg, raiz, termos):
    plano = Plano(caminho.read_text(encoding="utf-8", errors="replace"))
    rel, repo = Relatorio(), Repo(raiz)
    spec_info = None
    ref = spec_arg or cabecalho_spec(plano)
    if ref is None:
        rel.add("spec-nao-encontrada", 0, "sem --spec e sem cabeçalho **Spec:**: FR não conferidos")
    else:
        sp = resolve_spec(ref, caminho.parent, raiz)
        if sp is None:
            rel.add("spec-nao-encontrada", 0, f"spec não encontrada: {ref}")
        else:
            spec_info = str(sp)
            check_fr(plano, ler_spec(sp), rel)
    check_tabelas(plano, rel)
    planejados = check_ownership(plano, repo, rel)
    check_lido_e_linhas(plano, repo, rel)
    check_tarefas(plano, rel)
    check_comandos(plano, repo, planejados, rel)
    check_placeholders(plano, rel)
    check_termos(plano, termos, rel)
    return rel, spec_info


def git_topo(pasta):
    try:
        r = subprocess.run(["git", "-C", str(pasta), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    except OSError:
        return None
    return Path(r.stdout.strip()) if r.returncode == 0 else None


def main(argv=None):
    ap = argparse.ArgumentParser(description="pré-voo mecânico de um plano do power-plans")
    ap.add_argument("plano", help="arquivo .md do plano, ou pasta com plan.md")
    ap.add_argument("--spec", help="spec (senão, o cabeçalho **Spec:** do plano)")
    ap.add_argument("--root", help="raiz do projeto (padrão: raiz git do plano)")
    ap.add_argument("--retired", default="", help="termos aposentados, separados por vírgula")
    ap.add_argument("--json", action="store_true", help="saída estruturada")
    a = ap.parse_args(argv)

    caminho = Path(a.plano)
    if caminho.is_dir():
        caminho = caminho / "plan.md"
    if not caminho.is_file():
        print(f"plan-lint: plano não encontrado: {a.plano}", file=sys.stderr)
        return 2
    caminho = caminho.resolve()
    raiz = Path(a.root).resolve() if a.root else (git_topo(caminho.parent) or caminho.parent)
    if not raiz.is_dir():
        print(f"plan-lint: raiz não é pasta: {raiz}", file=sys.stderr)
        return 2
    termos = [t.strip() for t in a.retired.split(",") if t.strip()]
    if a.spec and resolve_spec(a.spec, caminho.parent, raiz) is None:
        # --spec é a invocação escolhida: spec que não existe é erro de uso, não aviso.
        print(f"plan-lint: --spec não encontrado: {a.spec}", file=sys.stderr)
        return 2

    rel, spec_info = lint(caminho, a.spec, raiz, termos)
    erros = sum(1 for x in rel.achados if x["severidade"] == ERRO)
    if a.json:
        saida = {"plano": a.plano, "raiz": str(raiz), "spec": spec_info,
                 "erros": erros, "avisos": len(rel.achados) - erros,
                 "por_checagem": rel.por_checagem(), "comandos_nao_conferidos": rel.nao_conferidos,
                 "achados": rel.achados}
        print(json.dumps(saida, ensure_ascii=False, indent=2))
    else:
        print(formata(rel, a.plano))
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
