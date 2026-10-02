#!/bin/bash
# One-command launcher: starts Ollama if needed, downloads the model once, opens Saathi.
set -e
cd "$(dirname "$0")"
MODEL="${SAATHI_MODEL:-gemma3:4b}"

command -v ollama >/dev/null || { echo "Install Ollama first:  brew install ollama"; exit 1; }
if ! curl -s localhost:11434/api/tags >/dev/null; then
  echo "Starting Ollama…"; (ollama serve >/dev/null 2>&1 &); sleep 3
fi
ollama list | grep -q "^$MODEL" || ollama pull "$MODEL"

(sleep 2 && open "http://localhost:${PORT:-8765}") &
SAATHI_MODEL="$MODEL" python3 server.py
