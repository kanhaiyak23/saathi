#!/bin/bash
set -e
ollama serve &
until curl -s localhost:11434/api/tags >/dev/null; do sleep 1; done
ollama pull "$SAATHI_MODEL"   # no-op when the model is already baked into the image
exec python3 server.py
