#!/usr/bin/env bash
# Trava do plugin: SKILL.md cabe no que sobrevive a uma compactação de contexto, e todo
# arquivo que ele manda ler existe. Roda antes de cada commit (ver .githooks/pre-commit).
set -u
export LC_ALL=C.UTF-8
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
limite="${SKILL_MAX_CHARS:-19000}"
falhas=0
for skill in "$root"/skills/*/SKILL.md; do
  dir="$(dirname "$skill")"; nome="$(basename "$dir")"
  chars="$(wc -m < "$skill" | tr -d ' ')"
  if [ "$chars" -gt "$limite" ]; then
    echo "ERRO $nome/SKILL.md: $chars caracteres, teto $limite. Mova detalhe para references/."
    falhas=$((falhas + 1))
  fi
  # o corte da compactação foi medido em caracteres; quem o mede em bytes usa 20000: vale o mais apertado
  bytes="$(wc -c < "$skill" | tr -d ' ')"
  if [ "$bytes" -ge 20000 ]; then
    echo "ERRO $nome/SKILL.md: $bytes bytes, teto 20000. Mova detalhe para references/."
    falhas=$((falhas + 1))
  fi
  head -1 "$skill" | grep -q '^---$' && grep -q '^name: ' "$skill" && grep -q '^description:' "$skill" || {
    echo "ERRO $nome/SKILL.md: frontmatter sem name ou description."; falhas=$((falhas + 1)); }
  # todo references/x.md e scripts/x citado no SKILL.md tem de existir na pasta da skill
  # shortcut: só confere caminhos entre crases; citar outra skill pelo nome não é conferido
  for ref in $(grep -o '`\(references\|scripts\)/[A-Za-z0-9._/-]*`' "$skill" | tr -d '`' | sort -u); do
    if [ ! -e "$dir/$ref" ] && [ ! -e "$root/$ref" ]; then
      echo "ERRO $nome/SKILL.md cita $ref, que não existe."; falhas=$((falhas + 1))
    fi
  done
done
hook="$root/hooks/session-start.md"
if [ -f "$hook" ] && [ "$(wc -m < "$hook" | tr -d ' ')" -gt 3000 ]; then
  echo "ERRO hooks/session-start.md passou de 3000 caracteres: ele entra em toda sessão."; falhas=$((falhas + 1))
fi
if [ "$falhas" -gt 0 ]; then echo "check-skills: $falhas problema(s)."; exit 1; fi
echo "check-skills: ok."
