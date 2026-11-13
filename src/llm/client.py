"""Client Groq (modèle commun imposé) avec cache disque, limitation de débit et journal des appels."""
import csv, hashlib, json, time
from datetime import datetime
from pathlib import Path
import requests
from src.config import CFG, ROOT, get_api_key

URL = "https://api.groq.com/openai/v1/chat/completions"
_last_call = 0.0


def _cache_path(key: str) -> Path:
    d = ROOT / CFG["llm"]["cache_dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def _log_call(objet: str) -> None:
    p = ROOT / CFG["paths"]["api_log"]
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "membre", "appels", "objet"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), "", 1, objet])


def chat(messages: list[dict], objet: str = "", temperature: float = 0.0, use_cache: bool = True) -> str:
    """Envoie une requête au modèle. Rejouable depuis le cache (temperature=0 recommandé)."""
    model = CFG["llm"]["model"]
    approx_tokens = sum(len(m["content"]) for m in messages) // 3
    if approx_tokens > CFG["llm"]["max_tokens_per_call"]:
        raise ValueError(f"Prompt trop long (~{approx_tokens} jetons) : envoyez seulement les passages utiles.")

    key = hashlib.sha256(json.dumps([model, messages, temperature], ensure_ascii=False).encode()).hexdigest()
    cp = _cache_path(key)
    if use_cache and cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))["content"]

    global _last_call
    for attempt in range(CFG["llm"]["max_retries"] + 1):
        wait = CFG["llm"]["min_interval_s"] - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        r = requests.post(URL, headers={"Authorization": f"Bearer {get_api_key()}"},
                          json={"model": model, "messages": messages, "temperature": temperature},
                          timeout=60)
        if r.status_code == 429 and attempt < CFG["llm"]["max_retries"]:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        break
    content = r.json()["choices"][0]["message"]["content"]
    cp.write_text(json.dumps({"model": model, "messages": messages, "content": content}, ensure_ascii=False), encoding="utf-8")
    _log_call(objet)
    return content
