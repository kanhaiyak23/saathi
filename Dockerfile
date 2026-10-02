# One CPU container: Ollama + open-weight model + Saathi.
# Works on Hugging Face Spaces (runs as uid 1000, port 7860) and on Render (sets $PORT itself).
FROM ollama/ollama:latest

ARG MODEL=gemma3:4b
RUN apt-get update && apt-get install -y --no-install-recommends python3 curl && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /home/app && chown 1000:1000 /home/app

ENV HOME=/home/app OLLAMA_MODELS=/home/app/.ollama/models OLLAMA_KEEP_ALIVE=-1 \
    SAATHI_MODEL=${MODEL} HOST=0.0.0.0 PORT=7860
USER 1000
WORKDIR /home/app/saathi

# Bake the model weights into the image so the app starts without a download.
RUN sh -c 'ollama serve & pid=$!; sleep 5; ollama pull "$SAATHI_MODEL"; kill $pid'

COPY --chown=1000:1000 . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 7860
ENTRYPOINT ["./docker-entrypoint.sh"]
