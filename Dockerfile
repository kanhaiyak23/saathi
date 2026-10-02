# Hosted demo: Ollama + an open-weight model + Saathi in one container (CPU only).
FROM ollama/ollama:latest

ARG MODEL=gemma3:4b
ENV SAATHI_MODEL=${MODEL} HOST=0.0.0.0 PORT=10000 OLLAMA_KEEP_ALIVE=-1

RUN apt-get update && apt-get install -y --no-install-recommends python3 curl && rm -rf /var/lib/apt/lists/*

# Bake the model weights into the image so the service starts without a download.
RUN ollama serve & sleep 5 && ollama pull ${MODEL} && pkill ollama

WORKDIR /app
COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 10000
ENTRYPOINT ["./docker-entrypoint.sh"]
