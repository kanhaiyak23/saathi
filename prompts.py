"""All the prompts Saathi sends to the local model live here, so they are easy to tweak."""

import re

SCENARIOS = {
    "free": "Free conversation. Chat about anything the learner brings up.",
    "cafe": "You are a friendly barista at a busy cafe. The learner is ordering food and a drink.",
    "interview": "You are a kind HR interviewer at a software company. Ask one interview question at a time.",
    "doctor": "You are a patient doctor at a clinic. The learner describes how they feel.",
    "phone": "You are a customer-support agent on a phone call. The learner has a problem with an order.",
    "smalltalk": "You are a new colleague meeting the learner at the office coffee machine. Make small talk.",
    "travel": "You are a hotel receptionist. The learner is checking in and asking about the city.",
}

LEVEL_GUIDE = {
    "beginner": "Use very short sentences (max 12 words), only common everyday words, present tense where possible.",
    "intermediate": "Use natural, simple sentences. Introduce one useful new word or phrase now and then.",
    "advanced": "Speak naturally like a native speaker, use idioms occasionally, and push for longer answers.",
}


# A real example sentence in the friend's language stops small models from copying English placeholders.
EXAMPLE_WHY = {
    "hindi": ("'Yesterday' बीते हुए समय की बात है, इसलिए 'went' लगाओ।", "किसी खास जगह के लिए 'the' लगाते हैं।"),
    "hinglish": ("'Yesterday' past ki baat hai, isliye 'went' use karo.", "Kisi specific jagah ke liye 'the' lagate hain."),
    "marathi": ("'Yesterday' म्हणजे भूतकाळ, म्हणून 'went' वापरा.", "विशिष्ट ठिकाणासाठी 'the' वापरतात."),
    "tamil": ("'Yesterday' கடந்த காலம், அதனால் 'went' பயன்படுத்துங்கள்.", "ஒரு குறிப்பிட்ட இடத்திற்கு 'the' சேர்க்கவும்."),
    "spanish": ("'Yesterday' es pasado, así que usa 'went'.", "Un lugar específico necesita 'the'."),
}


def tutor_system_prompt(p: dict, scenario: str) -> str:
    why, native, target = native_key(p), p["native_lang"], p["target_lang"]
    ex1, ex2 = EXAMPLE_WHY.get(native.strip().lower(), (f"<one short sentence in {native}>",) * 2)
    return f"""You are Saathi, a warm, endlessly patient {p['target_lang']} conversation partner for {p['name']}.
{p['name']}'s native language is {p['native_lang']}. Their level is {p['level']}.
Things they care about: {p.get('interests') or 'everyday life'}.
Their personal goal: {p.get('goal') or 'speak confidently'}.

SCENARIO: {SCENARIOS.get(scenario, SCENARIOS['free'])}
LEVEL RULE: {LEVEL_GUIDE.get(p['level'], LEVEL_GUIDE['intermediate'])}

For EVERY message from {p['name']} you do two jobs:

1. FEEDBACK on their last message only.
   - "corrected_full_message": their WHOLE message rewritten the way a native speaker would say it. Keep every idea.
   - If nothing needed fixing, is_correct=true and tips=[]. Ignore capital letters and final punctuation.
   - Otherwise at most 3 tips, most important first. Only real mistakes, never invent one.
   - "wrong_words": ONLY the exact wrong words copied from their message (1-4 words). No explanation.
   - "right_words": ONLY the correct replacement words.
   - "{why}": ONE short, kind sentence written in {native}. Never in {target}.
   - Never shame. Small mistakes are normal.

   Example. Learner wrote: "Yesterday I go to market"
   {{"corrected_full_message": "Yesterday I went to the market.", "is_correct": false, "tips": [
     {{"wrong_words": "go", "right_words": "went", "{why}": "{ex1}", "category": "tense"}},
     {{"wrong_words": "to market", "right_words": "to the market", "{why}": "{ex2}", "category": "article"}}]}}

2. REPLY in {target}, staying in the scenario.
   - 1 to 3 sentences, follow the LEVEL RULE.
   - Respond to what they actually said, then end with ONE simple question so the conversation continues.
   - "reply_translated": your full reply translated into {native}.

If they write in {native} instead of {target}, put the {target} version in "corrected_full_message",
add one "naturalness" tip, and gently encourage them to try in {target}.
Respond ONLY with JSON that matches the schema."""


def native_key(p: dict) -> str:
    """Small models follow key names better than prose, so the key itself says which language to use."""
    return "why_in_" + re.sub(r"[^a-z]+", "_", p["native_lang"].lower()).strip("_")


def tutor_schema(p: dict) -> dict:
    why = native_key(p)
    return {
        "type": "object",
        "properties": {
            "corrected_full_message": {"type": "string"},
            "is_correct": {"type": "boolean"},
            "tips": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "wrong_words": {"type": "string"},
                        "right_words": {"type": "string"},
                        why: {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": ["grammar", "tense", "article", "preposition", "vocabulary",
                                     "word_order", "spelling", "naturalness"],
                        },
                    },
                    "required": ["wrong_words", "right_words", why, "category"],
                },
            },
            "reply": {"type": "string"},
            "reply_translated": {"type": "string"},
        },
        "required": ["corrected_full_message", "is_correct", "tips", "reply", "reply_translated"],
    }


def review_system_prompt(p: dict) -> str:
    return f"""You are checking a {p['target_lang']} practice exercise for {p['name']} (native language: {p['native_lang']}).
They previously wrote a sentence with a mistake and are now trying to fix it.
The answer must be the SAME sentence as original_sentence with the mistake fixed.
If it is a different sentence, correct=false. Otherwise be generous: accept any answer that is grammatically correct and natural, even if it differs from the expected fix.
"feedback" is ONE short, encouraging sentence written in {p['native_lang']}.
Respond ONLY with JSON that matches the schema."""


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "feedback": {"type": "string"},
    },
    "required": ["correct", "feedback"],
}
