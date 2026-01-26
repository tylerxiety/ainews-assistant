#!/usr/bin/env bash
# Sync .claude/commands/*.md into ~/.codex/skills/<name>/SKILL.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC_DIR="$REPO_ROOT/.claude/commands"
DEST_DIR="$HOME/.codex/skills"

mkdir -p "$DEST_DIR"

tmp_list="$(mktemp)"
trap 'rm -f "$tmp_list"' EXIT

shopt -s nullglob

for file in "$SRC_DIR"/*.md; do
  [ -f "$file" ] || continue

  name="$(basename "$file" .md)"
  echo "$name" >> "$tmp_list"

  dest_dir="$DEST_DIR/$name"
  dest_file="$dest_dir/SKILL.md"

  mkdir -p "$dest_dir"
  if [ -L "$dest_file" ]; then
    rm -f "$dest_file"
  fi

  has_frontmatter=0
  if head -n 1 "$file" | grep -q '^---$'; then
    has_frontmatter=1
  fi

  desc_raw=""
  if [ "$has_frontmatter" -eq 1 ]; then
    desc_raw="$(awk '/^---$/{p++} p==1 && /^description:/{sub(/^description:[[:space:]]*/, ""); print; exit}' "$file")"
  fi
  desc_escaped="$(printf '%s' "$desc_raw" | sed 's/"/\\"/g')"

  {
    printf -- "---\n"
    printf 'name: "%s"\n' "$name"
    if [ -n "$desc_raw" ]; then
      printf 'description: "%s"\n' "$desc_escaped"
    else
      printf 'description: "%s"\n' "$name"
    fi
    printf -- "---\n\n"
    if [ "$has_frontmatter" -eq 1 ]; then
      awk 'BEGIN{p=0} /^---$/{p++; next} p>=2{print}' "$file"
    else
      cat "$file"
    fi
  } > "$dest_file"
done

for dir in "$DEST_DIR"/*; do
  [ -d "$dir" ] || continue
  base="$(basename "$dir")"
  if [ "$base" = ".system" ]; then
    continue
  fi
  if ! grep -qx "$base" "$tmp_list"; then
    rm -rf "$dir"
  fi
done
