#!/usr/bin/env bash
# sync-harnesses.sh: mantém as skills do planning-workflow instaladas e atualizadas
# nos harnesses de agente desta máquina. Uso:
#   sync-harnesses.sh                    atualiza os plugins (Claude Code, Codex) e cria os links das
#                                        skills nas pastas dos harnesses sem plugin (opencode, muse,
#                                        agy). Grok lê o plugin do Claude Code: não recebe link.
#   sync-harnesses.sh --pull             antes de tudo, git pull --ff-only do clone
#   sync-harnesses.sh --check            só lê; uma linha por harness; sai com 1 se algo falta ou diverge
#   sync-harnesses.sh --install-timer    agenda --pull a cada 10 min no crontab do usuário
#   sync-harnesses.sh --uninstall-timer  remove só as linhas com a marca do agendamento
# Regras: nunca stash, nunca reset; nunca sobrescreve pasta ou link que não aponte para este clone.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CLONE="$(cd "$SCRIPT_DIR/.." && pwd -P)"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/planning-workflow"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
PLUGIN="planning-workflow@planning-workflow"
TIMER_MARK="# planning-workflow-sync"

MODE=sync
PULL=0
for arg in "$@"; do
  case "$arg" in
    --check) MODE=check ;;
    --pull) PULL=1 ;;
    --install-timer) MODE=install ;;
    --uninstall-timer) MODE=uninstall ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "argumento desconhecido: $arg (use --help)" >&2; exit 2 ;;
  esac
done
if [ "$MODE" = check ] && [ "$PULL" = 1 ]; then
  echo "--check não altera nada: não combina com --pull" >&2; exit 2
fi

have() { command -v "$1" >/dev/null 2>&1; }
say() { if [ "$MODE" = sync ]; then echo "$(date '+%F %T') $*"; else echo "$*"; fi; }
row() { printf '%-9s %-13s %s\n' "$1" "$2" "$3"; }

HEAD_FULL="$(git -C "$CLONE" rev-parse HEAD 2>/dev/null)" || { echo "clone git inválido: $CLONE" >&2; exit 1; }
HEAD12="${HEAD_FULL:0:12}"

SKILLS=()
for d in "$CLONE"/skills/*/; do
  [ -f "$d/SKILL.md" ] && SKILLS+=("$(basename "$d")")
done
[ "${#SKILLS[@]}" -gt 0 ] || { echo "nenhuma skill em $CLONE/skills" >&2; exit 1; }

# detected <binário> <pasta de sinal>: o harness existe se o binário está no PATH ou a pasta de config existe.
detected() {
  local bin="$1" d="$2"
  have "$bin" && return 0
  [ -d "$d" ]
}

pull_clone() {
  local before after out branch
  before="$(git -C "$CLONE" rev-parse --short=12 HEAD)"
  if [ -n "$(git --no-optional-locks -C "$CLONE" status --porcelain)" ]; then
    say "pull: pulado, o clone tem mudança local (não toco nela)"; return 0
  fi
  branch="$(git -C "$CLONE" rev-parse --abbrev-ref HEAD)"
  if [ "$branch" != main ]; then
    say "pull: pulado, clone em '$branch' (só main é atualizada)"; return 0
  fi
  if out="$(GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes}" git -C "$CLONE" pull --ff-only 2>&1)"; then
    after="$(git -C "$CLONE" rev-parse --short=12 HEAD)"
    [ "$after" != "$before" ] && say "pull: $before -> $after"
  else
    say "pull: falhou, clone continua em $before: $(printf '%s' "$out" | tail -n 1)"
  fi
  return 0
}

write_clone_file() {
  mkdir -p "$CONFIG_HOME/planning-workflow" && printf '%s\n' "$CLONE" > "$CONFIG_HOME/planning-workflow/clone"
}

# eval_links <harness> <pasta de skills>: no sync cria o link que falta; fixa ST e DT.
# Nunca mexe no que não é link deste clone: pasta real ou link de outro lugar só é reportado.
ST=""
DT=""
eval_links() {
  local h="$1" dir="$2" name src dst diverg=() falta=()
  for name in "${SKILLS[@]}"; do
    src="$CLONE/skills/$name"
    dst="$dir/$name"
    if [ -L "$dst" ] && [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ]; then
      continue
    fi
    if [ -e "$dst" ] || [ -L "$dst" ]; then
      diverg+=("$name"); continue
    fi
    if [ "$MODE" = sync ]; then
      if mkdir -p "$dir" && ln -s "$src" "$dst"; then
        say "$h: link criado: $dst"
      else
        diverg+=("$name"); say "$h: falhou criar o link: $dst"
      fi
    else
      falta+=("$name")
    fi
  done
  if [ "${#diverg[@]}" -gt 0 ]; then
    ST=divergente; DT="${#diverg[@]} de ${#SKILLS[@]} não é link deste clone (${diverg[*]}); não toco"
  elif [ "${#falta[@]}" -gt 0 ]; then
    ST=faltando; DT="${#falta[@]} de ${#SKILLS[@]} link(s) faltando em $dir"
  else
    ST=ok; DT="${#SKILLS[@]} skills linkadas em $dir"
  fi
}

# ---- Claude Code: plugin do marketplace; o plugin entrega skills e o hook SessionStart ----
claude_field() { # version | enabled; vazio se o plugin não está instalado
  timeout 60 claude plugin list --json 2>/dev/null | tr -d '\n' \
    | grep -o "\"id\": *\"$PLUGIN\"[^}]*" | grep -o "\"$1\": *[^,}]*" | head -n 1 \
    | sed 's/.*: *//; s/[" ]//g'
}

update_claude() {
  local before after
  before="$(claude_field version)"
  timeout 180 claude plugin marketplace update planning-workflow </dev/null >/dev/null 2>&1 \
    || say "claude: falhou 'claude plugin marketplace update planning-workflow'"
  timeout 300 claude plugin update "$PLUGIN" </dev/null >/dev/null 2>&1 \
    || say "claude: falhou 'claude plugin update $PLUGIN'"
  after="$(claude_field version)"
  [ "$after" != "$before" ] && say "claude: plugin ${before:-nenhum} -> ${after:-nenhum} (reinicie o Claude Code para aplicar)"
  return 0
}

eval_claude() {
  if ! have claude; then ST="não instalado"; DT="binário claude fora do PATH"; return; fi
  [ "$MODE" = sync ] && update_claude
  local ver en
  ver="$(claude_field version)"
  en="$(claude_field enabled)"
  if [ -z "$ver" ]; then ST=faltando; DT="plugin não instalado: claude plugin install $PLUGIN"
  elif [ "$ver" != "$HEAD12" ]; then ST=divergente; DT="plugin em $ver, clone em $HEAD12"
  elif [ "$en" != true ]; then ST=divergente; DT="plugin $ver desativado"
  else ST=ok; DT="plugin em $ver"
  fi
}

# ---- Codex: plugin do marketplace (cache git em CODEX_HOME); sem link em skills/, que duplicaria ----
codex_rev() { # HEAD do cache git do plugin (o arquivo de registro nem sempre existe); vazio se não instalado
  local d
  for d in "$CODEX_DIR"/plugins/cache/planning-workflow/planning-workflow/*/; do
    [ -d "$d/.git" ] && { git -C "$d" rev-parse HEAD 2>/dev/null; return 0; }
  done
  return 0
}

update_codex() {
  local before after
  before="$(codex_rev)"
  timeout 300 codex plugin marketplace upgrade planning-workflow </dev/null >/dev/null 2>&1 \
    || say "codex: falhou 'codex plugin marketplace upgrade planning-workflow'"
  # O upgrade do Codex nem sempre move o cache (medido: devolve upgradedRoots vazio). O cache é um
  # clone git do mesmo repositório: se está limpo, avança por fast-forward. Nunca reset.
  local d
  for d in "$CODEX_DIR"/plugins/cache/planning-workflow/planning-workflow/*/; do
    [ -d "$d/.git" ] || continue
    # só arquivo rastreado alterado segura o avanço; o Codex deixa um marcador não rastreado no cache
    if [ -n "$(git -C "$d" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
      say "codex: cache com mudança local, não avanço: $d"; continue
    fi
    timeout 120 git -C "$d" pull --ff-only -q </dev/null >/dev/null 2>&1 \
      || say "codex: git pull --ff-only do cache falhou: $d"
  done
  after="$(codex_rev)"
  [ "$after" != "$before" ] && say "codex: plugin ${before:0:12} -> ${after:0:12} (reinicie as sessões do Codex)"
  return 0
}

eval_codex() {
  if ! have codex && [ ! -d "$CODEX_DIR" ]; then ST="não instalado"; DT="codex fora do PATH e sem $CODEX_DIR"; return; fi
  [ "$MODE" = sync ] && have codex && update_codex
  local rev n dup=""
  rev="$(codex_rev)"
  for n in "${SKILLS[@]}"; do
    if [ -e "$CODEX_DIR/skills/$n" ] || [ -L "$CODEX_DIR/skills/$n" ]; then dup="$dup $n"; fi
  done
  if [ -z "$rev" ]; then ST=faltando; DT="plugin não instalado no Codex: codex plugin add $PLUGIN"
  elif [ "$rev" != "$HEAD_FULL" ]; then ST=divergente; DT="plugin no Codex em ${rev:0:12}, clone em $HEAD12"
  elif [ -n "$dup" ]; then ST=divergente; DT="link de usuário duplica o plugin:$dup"
  else ST=ok; DT="plugin em $HEAD12"
  fi
}

# ---- Grok: lê os plugins Claude-compatíveis (medido: grok inspect --json aponta para o cache do plugin
# do Claude Code). Link próprio duplicaria a skill no catálogo, então não recebe link.
eval_grok() {
  local n dup=""
  for n in "${SKILLS[@]}"; do
    if [ -e "$HOME/.grok/skills/$n" ] || [ -L "$HOME/.grok/skills/$n" ]; then dup="$dup $n"; fi
  done
  ST="$CL_ST"; [ "$ST" = "não instalado" ] && ST=faltando
  DT="via plugin do Claude Code: $CL_DT"
  if [ -n "$dup" ]; then ST=divergente; DT="link em ~/.grok/skills duplica o plugin:$dup (remova à mão)"; fi
}

# ---- Demais harnesses: pasta de skills própria, com link por skill ----
BAD=0
CL_ST=""
CL_DT=""
run_harness() {
  local h="$1"
  ST=""; DT=""
  case "$h" in
    claude) eval_claude; CL_ST="$ST"; CL_DT="$DT" ;;
    codex) eval_codex ;;
    grok)
      if detected grok "$HOME/.grok"; then eval_grok; else ST="não instalado"; fi ;;
    opencode)
      if detected opencode "$CONFIG_HOME/opencode"; then eval_links opencode "$CONFIG_HOME/opencode/skills"; else ST="não instalado"; fi ;;
    muse)
      if detected muse "$CONFIG_HOME/muse"; then eval_links muse "$CONFIG_HOME/muse/skills"; else ST="não instalado"; fi ;;
    agy)
      if detected agy "$HOME/.gemini"; then eval_links agy "$HOME/.gemini/config/skills"; else ST="não instalado"; fi ;;
  esac
  if [ "$MODE" = check ]; then
    row "$h" "$ST" "$DT"
  elif [ "$ST" != ok ] && [ "$ST" != "não instalado" ]; then
    say "$h: $ST: $DT"
  fi
  case "$ST" in faltando|divergente) BAD=$((BAD + 1)) ;; esac
}

run_all() {
  local h
  for h in claude codex opencode muse grok agy; do run_harness "$h"; done
}

# ---- Agendamento: crontab (systemd --user indisponível sem linger; crontab funciona sem sudo) ----
read_crontab() {
  local out rc
  out="$(LC_ALL=C crontab -l 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ]; then
    case "$out" in
      *"no crontab"*) out="" ;;
      *) echo "crontab -l falhou: $out" >&2; return 1 ;;
    esac
  fi
  printf '%s' "$out"
}

keep_lines() { # linhas de $1 sem a marca deste agendamento
  [ -n "$1" ] && printf '%s\n' "$1" | grep -v -F "$TIMER_MARK"
  return 0
}

write_crontab() { # $1 = conteúdo inteiro novo (pode ser vazio)
  if [ -n "$1" ]; then printf '%s\n' "$1"; fi | crontab -
}

install_timer() {
  have crontab || { echo "crontab não encontrado: sem agendamento" >&2; exit 1; }
  have flock || { echo "flock não encontrado (util-linux): sem trava, não agendo" >&2; exit 1; }
  local cur new line path b d dirs=()
  cur="$(read_crontab)" || exit 1
  # PATH do cron: as pastas dos binários que o script usa, na ordem em que o usuário os acha hoje.
  for b in claude codex opencode muse grok agy git flock; do
    d="$(command -v "$b")" || continue
    d="${d%/*}"
    case " ${dirs[*]} " in *" $d "*) ;; *) dirs+=("$d") ;; esac
  done
  for d in /usr/bin /bin; do
    case " ${dirs[*]} " in *" $d "*) ;; *) dirs+=("$d") ;; esac
  done
  path="$(IFS=:; printf '%s' "${dirs[*]}")"
  mkdir -p "$STATE_DIR" || exit 1
  line="*/10 * * * * PATH='$path' $(command -v flock) -n '$STATE_DIR/sync.lock' $(command -v bash) '$SCRIPT_DIR/sync-harnesses.sh' --pull >> '$STATE_DIR/sync.log' 2>&1 $TIMER_MARK"
  new="$(keep_lines "$cur")"
  new="${new:+$new$'\n'}$line"
  write_crontab "$new" || { echo "crontab: escrita falhou; nada mudou" >&2; exit 1; }
  echo "timer: instalado no crontab (a cada 10 min); log: $STATE_DIR/sync.log; linhas antigas preservadas: $(printf '%s\n' "$new" | grep -c -v -F "$TIMER_MARK")"
}

uninstall_timer() {
  have crontab || { echo "crontab não encontrado" >&2; exit 1; }
  local cur new
  cur="$(read_crontab)" || exit 1
  if ! printf '%s\n' "$cur" | grep -q -F "$TIMER_MARK"; then
    echo "timer: não estava instalado"; return 0
  fi
  new="$(keep_lines "$cur")"
  write_crontab "$new" || { echo "crontab: escrita falhou; nada mudou" >&2; exit 1; }
  echo "timer: removido; as outras linhas do crontab foram mantidas"
}

case "$MODE" in
  install) install_timer ;;
  uninstall) uninstall_timer ;;
  check)
    echo "clone: $CLONE, branch $(git -C "$CLONE" rev-parse --abbrev-ref HEAD) @ $HEAD12, arquivos alterados: $(git --no-optional-locks -C "$CLONE" status --porcelain | wc -l | tr -d ' ')"
    run_all
    [ "$BAD" -eq 0 ]
    ;;
  sync)
    [ "$PULL" = 1 ] && pull_clone
    write_clone_file
    # Trava de commit do próprio plugin: check-skills.sh no pre-commit deste clone.
    if [ -x "$CLONE/.githooks/pre-commit" ]; then git -C "$CLONE" config core.hooksPath .githooks; fi
    run_all
    ;;
esac
