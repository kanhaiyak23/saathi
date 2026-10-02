---
title: Saathi — a patient English practice partner I built for ✏️[FRIEND], running Gemma 3 on an 8 GB MacBook
published: false
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

**Saathi** (साथी, "companion" in Hindi) is an English conversation partner that never gets tired, never judges, and never leaves your laptop.

I built it for **✏️[FRIEND]**, my ✏️[RELATIONSHIP]. ✏️[2–3 SENTENCES OF THEIR REAL SITUATION. For example: what they need English for, where they get stuck (reading is fine but speaking freezes them?), and why classes or practising with people hasn't worked.]

Here's what I noticed they needed: not another app that turns a sentence red, but someone who would:

- **stay patient** through the same mistake for the tenth time,
- **explain in Hindi**, because "use the present perfect continuous" means nothing when you're nervous,
- **practise the situations they actually dread**: interviews, office small talk, phone calls,
- and **keep their half-finished sentences private** instead of sending them to someone else's server.

So that's what Saathi does. You pick a scenario (job interview, café, doctor, customer-support call, hotel check-in, office small talk, or free chat) and just talk. After every message you get:

1. **The natural way to say it.** *"I have been working at this company for three years."*
2. **The exact words to change.** ~~since~~ → **for**
3. **One short reason in your own language.** *"'Doesn't' का प्रयोग 'he' के साथ होता है।"*
4. **A reply that keeps the conversation going**, pitched to your level and always ending with an easy question. A 🔊 button reads it aloud, and a 🌐 button shows it in Hindi.

Every mistake goes into a local notebook. The **Review** tab brings them back as flashcards until you get them right, and **Progress** shows which kinds of mistakes keep coming back. For ✏️[FRIEND] that's ✏️[e.g. articles and tenses].

## Demo

Saathi deliberately has no hosted version. The whole point is that it runs on the learner's own laptop, so here it is running on mine:

✏️[VIDEO LINK: YouTube (unlisted) or Loom]

![Saathi correcting a sentence with explanations in Hindi](✏️[SCREENSHOT URL: drag a screenshot into the dev.to editor to get one])

## Code

{% embed https://github.com/kanhaiyak23/saathi %}

About 700 lines in total: a Python server that uses only the standard library, a prompt file, and a single HTML page. To run it:

```bash
brew install ollama
git clone https://github.com/kanhaiyak23/saathi && cd saathi
./start.sh
```

## How I Built It

**The stack is deliberately small:**

- **Model:** [Gemma 3 4B](https://ollama.com/library/gemma3), Google's open-weight model. It's multilingual, handles Hindi in Devanagari well, and fits comfortably in 8 GB of RAM.
- **Inference:** [Ollama](https://ollama.com), running locally on the Mac's GPU through Metal. A full turn (correction, reply and translation) takes **about 5–11 seconds on a base M2 MacBook Air with 8 GB**.
- **App:** a Python standard-library HTTP server, SQLite for the mistake notebook, and one HTML file for the UI. No `pip install`, no build step, and no account.

The interesting part was turning a 4B model into a tutor you can actually trust. My first version would happily put *"'go' is incorrect here, use 'went'"* in the field meant for the wrong word, explain everything in English, and occasionally invent mistakes that weren't there. Four changes fixed it:

**1. Structured output instead of parsing.** Ollama's `format` parameter takes a JSON schema and constrains decoding to it, so the model physically can't return broken JSON.

**2. Let the key names do the prompting.** Small models skim long instructions, but they pay close attention to keys. Renaming fields to `wrong_words` / `right_words`, and generating a key literally called `why_in_hindi` from the learner's language, fixed most of the format problems in one go. The last stubborn one was explanations still coming back in English. My example in the prompt said *"(in Hindi) 'Yesterday' is past…"*, and the model copied it word for word, English and all. Replacing it with an example actually written in Hindi fixed that immediately.

**3. Guardrails in code, not in the prompt.** A tip is only shown if its `wrong_words` really appear in what the learner typed, so hallucinated mistakes simply disappear. Review answers are graded deterministically first (old mistake gone, fix present), and the model is only consulted for creative rewrites. My first version of that check happily accepted a completely unrelated sentence as a correct answer.

**4. A fallback for forgetful models.** Sometimes the model rewrites the sentence perfectly but forgets to list what it changed. In that case Saathi compares the original and corrected sentences word by word and builds the tips itself, ignoring reordered words and dropped words, which are usually style rather than mistakes.

Here's real output for *"He don't like to eat spicy foods"*, before and after those changes:

| | Before | After |
|---|---|---|
| mistake → fix | "Use 'does not' instead of 'don't'." → "Use 'does not'." | `He don't` → `He doesn't` |
| why | "It is more formal here." | "'Doesn't' का प्रयोग 'he' के साथ होता है।" |
| vague tips | "Word order is important." | dropped: those words never appeared in the sentence |

**I also tried going smaller, and it didn't work.** I tested Gemma 3 1B and Qwen 2.5 1.5B to see whether a tiny model would do. Gemma 1B "corrected" *I am working* to *You are working*. Qwen's corrections were passable, but its Hindi was garbled and it sometimes replied in Hindi instead of English. For a tutor, a wrong correction is worse than none, so 4B is the floor. Being able to test three models in ten minutes with one setting, and pick the smallest one that's actually good, is exactly the kind of thing open weights make easy.

## Why Does Open Innovation Matter?

**Privacy isn't a feature here, it's the product.** People learning a language write their most vulnerable sentences: about their job, their family, their health, and all of it in a language they're insecure about. With an open-weight model on their own laptop, none of it ever leaves the machine. The server only listens on `127.0.0.1`, conversations are never written to disk, and deleting one folder wipes everything.

**Unlimited practice has to be free practice.** Fluency comes from volume. With a paid API, every extra sentence costs money, and "practise as much as you want" quietly becomes "practise as much as you can afford". Saathi costs nothing per message, forever.

**It works offline.** On a train, during a power cut with no Wi-Fi, anywhere.

**You can swap the brain.** Settings lists every model installed in Ollama. Someone with a 16 GB laptop can switch to `gemma3:12b` for richer explanations without changing a line of code. Because the weights are open, the obvious next step is fine-tuning on a Hindi-English learner-error dataset, which no closed API would let me do on my own terms.

**Anyone can fix it.** Every prompt lives in one file, `prompts.py`. If Saathi explains something badly in Tamil or Marathi, a native speaker can open that file and fix it. That's how a tutor for one friend can become a tutor for many people.

## Handing It Over

✏️[THE REAL MOMENT. Write 1–2 short paragraphs:
- Where and how you gave it to them (installed on their laptop? sat next to them?)
- What they practised first
- A mistake Saathi caught that they didn't know they were making
- What they said: quote them, even in Hindi with a translation
- What they asked for next]

## My Agent Session

I built Saathi with Claude Code as a pair programmer. It scaffolded the app, then we iterated on the prompt and schema against real Gemma output (wrong fields, English explanations, invented mistakes, an over-generous review grader) until the corrections were trustworthy. The session also covers testing smaller models and deciding not to host it.

✏️[DEVRELAY EMBED: save this session at devrelay.com and paste the agent_session tag here, or delete this section]

## Prize Categories

None of the partner categories fit this build. I'm entering for the overall prize.
