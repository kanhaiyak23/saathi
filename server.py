"""Saathi: a patient, private language-practice partner that runs 100% on your laptop.

Zero dependencies beyond the Python standard library. The model runs locally in Ollama.
Run:  python3 server.py   then open http://localhost:8765
"""

import json
import os
import random
import sqlite3
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from prompts import REVIEW_SCHEMA, native_key, review_system_prompt, tutor_schema, tutor_system_prompt

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "saathi.db"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("SAATHI_MODEL", "gemma3:4b")
PORT = int(os.environ.get("PORT", "8765"))
HISTORY_TURNS = 10  # keep context small so a 4B model stays fast on 8 GB RAM

DEFAULT_PROFILE = {
    "name": "Friend",
    "native_lang": "Hindi",
    "target_lang": "English",
    "level": "beginner",
    "interests": "cricket, cooking, Bollywood movies",
    "goal": "speak confidently in job interviews",
    "model": DEFAULT_MODEL,
}


# ---------- storage (local SQLite file, never leaves the machine) ----------

def db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            original TEXT, mistake TEXT, fix TEXT, why TEXT, category TEXT, scenario TEXT,
            attempts INTEGER DEFAULT 0, mastered INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS stats (day TEXT PRIMARY KEY, messages INTEGER DEFAULT 0, correct INTEGER DEFAULT 0);
        """
    )
    return conn


def get_profile():
    with db() as conn:
        row = conn.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    return {**DEFAULT_PROFILE, **(json.loads(row["data"]) if row else {})}


def save_profile(data):
    profile = {**get_profile(), **{k: str(v)[:300] for k, v in data.items() if k in DEFAULT_PROFILE}}
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO profile (id, data) VALUES (1, ?)", (json.dumps(profile),))
    return profile


# ---------- local model via Ollama ----------

def ollama_chat(model, messages, schema, temperature=0.6):
    body = {
        "model": model,
        "messages": messages,
        "format": schema,  # structured output: the model must return JSON matching this schema
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": 4096},
        "keep_alive": "30m",
    }
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        out = json.loads(resp.read())
    return json.loads(out["message"]["content"])


def installed_models():
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5) as resp:
            return [m["name"] for m in json.loads(resp.read())["models"]]
    except (urllib.error.URLError, OSError):
        return None


# ---------- features ----------

def squash(s):
    return " ".join("".join(c for c in s.lower() if c.isalnum() or c.isspace() or c == "'").split())


def normalize_tip(t, profile):
    return {"mistake": t.get("wrong_words", "").strip(" '\"‘’“”"),
            "fix": t.get("right_words", "").strip(" '\"‘’“”"),
            "why": t.get(native_key(profile), ""), "category": t.get("category", "grammar")}


def chat(payload):
    profile = get_profile()
    scenario = payload.get("scenario", "free")
    history = payload.get("history", [])[-HISTORY_TURNS * 2:]
    text = payload["message"].strip()[:1000]

    messages = [{"role": "system", "content": tutor_system_prompt(profile, scenario)}]
    for turn in history:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": str(turn["content"])[:1000]})
    messages.append({"role": "user", "content": text})

    raw = ollama_chat(profile["model"], messages, tutor_schema(profile))
    tips = [normalize_tip(t, profile) for t in raw.get("tips", [])]
    # Guardrail for small models: keep a tip only if the "wrong" words really appear in what they typed.
    tips = [t for t in tips if t["mistake"] and t["fix"] and t["mistake"].lower() != t["fix"].lower()
            and squash(t["mistake"]) in squash(text)]
    result = {
        "feedback": {"is_correct": not tips, "corrected": raw.get("corrected_full_message", text), "tips": tips},
        "reply": raw.get("reply", ""),
        "reply_native": raw.get("reply_translated", ""),
    }

    with db() as conn:
        for t in tips:
            conn.execute(
                "INSERT INTO mistakes (original, mistake, fix, why, category, scenario) VALUES (?,?,?,?,?,?)",
                (text, t["mistake"], t["fix"], t["why"], t["category"], scenario),
            )
        conn.execute(
            "INSERT INTO stats (day, messages, correct) VALUES (date('now','localtime'), 1, ?) "
            "ON CONFLICT(day) DO UPDATE SET messages = messages + 1, correct = correct + excluded.correct",
            (1 if not tips else 0,),
        )
    return result


def review_card():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM mistakes WHERE mastered = 0 ORDER BY attempts ASC, id DESC LIMIT 20"
        ).fetchall()
    if not rows:
        return {"card": None}
    r = random.choice(rows)
    return {"card": {"id": r["id"], "original": r["original"], "mistake": r["mistake"],
                     "category": r["category"], "why": r["why"]}}


def review_check(payload):
    profile = get_profile()
    with db() as conn:
        r = conn.execute("SELECT * FROM mistakes WHERE id = ?", (int(payload["id"]),)).fetchone()
    if not r:
        return {"error": "card not found"}
    answer = payload["answer"].strip()[:500]
    a, wrong, fix = squash(answer), squash(r["mistake"]), squash(r["fix"])
    if wrong in a and wrong not in fix:
        result = {"correct": False, "feedback": f"'{r['mistake']}' is still there. Try again!"}
    elif fix in a:
        result = {"correct": True, "feedback": "✓"}
    else:
        result = ask_model_to_grade(profile, r, answer)
    with db() as conn:
        conn.execute("UPDATE mistakes SET attempts = attempts + 1, mastered = ? WHERE id = ?",
                     (1 if result.get("correct") else 0, r["id"]))
    result["expected"] = r["fix"]
    return result


def ask_model_to_grade(profile, r, answer):
    messages = [
        {"role": "system", "content": review_system_prompt(profile)},
        {"role": "user", "content": json.dumps({
            "original_sentence": r["original"], "mistake": r["mistake"],
            "expected_fix": r["fix"], "learner_answer": answer,
        }, ensure_ascii=False)},
    ]
    return ollama_chat(profile["model"], messages, REVIEW_SCHEMA, temperature=0.2)


def progress():
    with db() as conn:
        cats = conn.execute(
            "SELECT category, COUNT(*) AS n, SUM(mastered) AS done FROM mistakes GROUP BY category ORDER BY n DESC"
        ).fetchall()
        days = conn.execute("SELECT * FROM stats ORDER BY day DESC LIMIT 14").fetchall()
        recent = conn.execute(
            "SELECT mistake, fix, why, category FROM mistakes ORDER BY id DESC LIMIT 15"
        ).fetchall()
    return {
        "categories": [dict(c) for c in cats],
        "days": [dict(d) for d in days],
        "recent": [dict(r) for r in recent],
    }


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = (ROOT / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/profile":
            self.send_json({"profile": get_profile(), "models": installed_models()})
        elif self.path == "/api/review":
            self.send_json(review_card())
        elif self.path == "/api/progress":
            self.send_json(progress())
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            routes = {"/api/chat": chat, "/api/profile": save_profile, "/api/review": review_check}
            if self.path not in routes:
                return self.send_json({"error": "not found"}, 404)
            result = routes[self.path](payload)
            self.send_json({"profile": result} if self.path == "/api/profile" else result)
        except urllib.error.URLError:
            self.send_json({"error": "Can't reach Ollama. Start it with: ollama serve"}, 503)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.send_json({"error": f"Bad request or model output: {e}"}, 400)


if __name__ == "__main__":
    db().close()
    print(f"Saathi is running at http://localhost:{PORT}  (model: {get_profile()['model']}, Ollama: {OLLAMA})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
