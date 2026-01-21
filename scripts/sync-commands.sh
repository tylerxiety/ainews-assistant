#!/bin/bash
# Converts .claude/commands/*.md to .gemini/commands/*.toml
# Source of truth: .claude/commands/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLAUDE_DIR="$REPO_ROOT/.claude/commands"
GEMINI_DIR="$REPO_ROOT/.gemini/commands"

mkdir -p "$GEMINI_DIR"

for file in "$CLAUDE_DIR"/*.md; do
  [ -f "$file" ] || continue

  name=$(basename "$file" .md)

  # Extract description from YAML frontmatter
  desc=$(awk '/^---$/{p++} p==1 && /^description:/{gsub(/^description: */, ""); print; exit}' "$file")

  # Extract body (everything after the closing ---)
  body=$(awk '/^---$/{p++; next} p>=2{print}' "$file")

  # Write TOML file
  cat > "$GEMINI_DIR/${name}.toml" << EOF
description = "$desc"
prompt = """
$body
"""
EOF

done

echo "Synced $(ls -1 "$CLAUDE_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') commands to .gemini/commands/"
