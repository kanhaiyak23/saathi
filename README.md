# Saathi · साथी

**A patient, private English practice partner that runs entirely on a laptop.**
No account, no API key, no internet after setup. Every sentence your friend types stays on their machine.

Built with the open-weight **Gemma 3 4B** model running locally through **Ollama**.

## What it does

- **Practice conversations** in real-life scenarios: office small talk, job interview, café, doctor, customer-support call, hotel check-in, or free chat.
- **Gentle corrections** after every message: the natural way to say it, the exact wrong words → right words, and a one-line reason **in the learner's own language** (Hindi, Hinglish, Marathi, Tamil, Spanish…).
- **Replies pitched to their level** (beginner / intermediate / advanced), always ending with an easy question so the conversation keeps going.
- **🔊 Listen** reads replies aloud with the Mac's built-in voices; **🌐 Translate** shows the reply in their language.
- **Mistake notebook → Review mode**: every mistake is saved locally and comes back as a flashcard until it's mastered.
- **Progress** shows which kinds of mistakes (tense, articles, prepositions…) to focus on.
- **Swap models** from Settings: any model installed in Ollama shows up.

## Run it (macOS, 8 GB RAM is enough)

```bash
brew install ollama        # once
./start.sh                 # starts Ollama, downloads gemma3:4b (~3.3 GB) the first time, opens the app
```

Or manually:

```bash
ollama serve &
ollama pull gemma3:4b
python3 server.py          # → http://localhost:8765
```

Only the Python standard library is used: no `pip install`.

Tip: press **fn** twice on a Mac to dictate instead of typing (on-device dictation) for speaking practice.

### Use a different model

| Laptop RAM | Suggested model | Command |
|---|---|---|
| 8 GB | `gemma3:4b` (default) | `ollama pull gemma3:4b` |
| 8 GB, faster | `llama3.2:3b` | `ollama pull llama3.2:3b` |
| 16 GB+ | `gemma3:12b` (better explanations) | `ollama pull gemma3:12b` |

Then pick it in **Settings**, or run `SAATHI_MODEL=gemma3:12b ./start.sh`.

## How it works

```
Browser UI (static/index.html)
   │  fetch /api/chat
   ▼
server.py  (Python stdlib HTTP server + SQLite in ./data)
   │  POST /api/chat with a JSON schema in "format"
   ▼
Ollama  →  gemma3:4b running on the Mac's GPU (Metal)
```

All prompts live in [`prompts.py`](prompts.py). Making a 4B model reliable took three tricks:

1. **Structured output.** Ollama's `format` parameter forces the model to return JSON matching a schema, so there's no fragile parsing.
2. **Self-describing keys.** Small models ignore prose instructions but obey key names. The schema uses `wrong_words`, `right_words`, and a key literally called `why_in_hindi` (built from the learner's language), so explanations come back in Hindi.
3. **Guardrails in code, not prompts.** A tip is kept only if its `wrong_words` actually appear in what the learner typed, which removes hallucinated "mistakes". Review answers are graded deterministically first (mistake gone + fix present); the model is only asked for ambiguous rewrites.

## Privacy

- The server listens on `127.0.0.1` only.
- Conversations are never written to disk. Only corrected mistakes and daily counts are stored, in `data/saathi.db`.
- Delete `data/` to wipe everything.


## Self-hosting (optional)

Saathi is meant to run on the learner's own laptop. If you want a shared copy anyway, the `Dockerfile` bundles Ollama and Gemma 3 4B into one CPU container (needs about 5 GB RAM), and `render.yaml` is a Render blueprint.
A hosted copy sends sentences to that server and shares one mistake notebook between all visitors.

## License

MIT
