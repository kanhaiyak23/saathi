---
title: Saathi — an offline English practice partner I built for [FRIEND NAME], running Gemma 3 on an 8 GB MacBook
published: false
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

<!-- ✏️ Replace everything in [BRACKETS]. Delete this comment before publishing. -->

## What I Built

**Saathi** (साथी, "companion" in Hindi) is a patient English conversation partner that runs entirely on a laptop.

I built it for **[FRIEND NAME]**, my [friend / cousin / mom / colleague]. [One or two sentences of real story, e.g. "They have a job interview coming up and they understand English well but freeze when they have to speak it. Classes are expensive, and practising with people feels embarrassing."]

What they needed wasn't another app that marks them wrong. They needed someone who:

- **never gets tired** of the same mistake,
- **explains in Hindi**, because "use present perfect continuous" means nothing when you're nervous,
- **practises the real situations** they're worried about: interviews, office small talk, phone calls,
- and **doesn't send their broken sentences to some company's server**.

After each message, Saathi shows:

1. the natural way to say it,
2. the exact wrong words → right words (`it take → it takes`),
3. a one-line reason **in their own language**,
4. then it carries on the conversation and asks a simple follow-up question.

Every mistake goes into a local notebook. The **Review** tab turns them into flashcards until they're mastered, and **Progress** shows what to focus on (for [FRIEND NAME] it's [articles and tenses]).

## Demo

<!-- Record a 60–90s screen video (Cmd+Shift+5 on Mac): pick "Job interview", type a sentence with mistakes, show the Hindi tips, press 🔊 Listen, then show Review and Progress. Upload to YouTube/Loom and paste the link below. -->

[VIDEO LINK]

![Saathi correcting a sentence with explanations in Hindi]([SCREENSHOT URL])

## Code

{% embed [GITHUB REPO URL] %}

Zero dependencies beyond the Python standard library plus Ollama. `./start.sh` and you're running.

## How I Built It

- **Model:** [Gemma 3 4B](https://ollama.com/library/gemma3), an open-weight model. It's multilingual (handles Hindi in Devanagari well) and fits in 8 GB of RAM.
- **Local inference:** [Ollama](https://ollama.com), running on the Mac's GPU via Metal. About **5–11 seconds per turn** on a base M2 MacBook Air with 8 GB.
- **App:** a ~250-line Python standard-library server, SQLite for the mistake notebook, and one HTML file for the UI.

Getting a 4B model to be a *reliable* tutor was the interesting part. My first version returned "mistakes" like *"'go' is incorrect here, use 'went'"* in the field meant for the wrong word, explained everything in English, and sometimes invented errors. Three fixes made it solid:

1. **Structured output.** Ollama's `format` parameter takes a JSON schema and constrains decoding to it. No regex parsing, no broken JSON.
2. **Let the key names do the prompting.** Small models skim instructions, but they read keys. Renaming fields to `wrong_words` / `right_words`, and generating a key literally called `why_in_hindi` from the learner's language, fixed most of the output-format problems at once. Adding one example explanation *actually written in Hindi* (not "(in Hindi) …") fixed the rest.
3. **Guardrails in code.** A tip only survives if its `wrong_words` really appear in what the learner typed, so hallucinated mistakes get dropped. Review answers are graded deterministically first (old mistake gone, fix present). The model is only consulted for creative rewrites.

Real before → after output on *"He don't like to eat spicy foods"*:

| | Before | After |
|---|---|---|
| mistake → fix | "Use 'does not' instead of 'don't'." → "Use 'does not'." | `He don't` → `He doesn't` |
| why | "It is more formal here." | "‘Doesn’t’ का प्रयोग ‘he’ के साथ होता है।" |
| vague tips | "Word order is important." | dropped: those words never appeared in the sentence |

## Why Does Open Innovation Matter?

- **It's private by design.** Language learners write their most vulnerable sentences: about work, family, health. With an open-weight model on their own laptop, none of it ever leaves the machine. The server only listens on `127.0.0.1`.
- **It costs nothing to run.** [FRIEND NAME] can practise for hours every day with no subscription or per-token bill. A closed API would turn "practise as much as you want" into "practise as much as you can afford".
- **It works offline.** On the train, with patchy Wi-Fi, anywhere.
- **It's swappable and tunable.** Settings lists every model in Ollama. A friend with 16 GB can switch to `gemma3:12b` for richer explanations. Because the weights are open, the next step is fine-tuning on a Hindi-English learner-error dataset, which no closed API would let me do.
- **It's inspectable.** Every prompt is in one file (`prompts.py`). If Saathi explains something badly, anyone can open it and fix it.

## Handing It Over

<!-- The bonus points! Install it on their laptop (or yours), let them use it for 15 minutes, and write what happened. Quote them if you can. -->

[What did they say? What surprised them? What mistake did Saathi catch that they didn't know they made? What do they want next?]

## My Agent Session

I built Saathi with Claude Code as my pair programmer: scaffolding the app, then iterating on the prompt and schema against real Gemma outputs until the corrections were reliable.

[DEVRELAY EMBED OR LINK]

## Prize Categories

[List the partner categories you're entering, or delete this section.]
