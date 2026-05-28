"""
Lana Memory System — Mem0-powered persistent memory.

Usage from Hermes (via terminal):
    python ~/lana_memory/lana_memory.py add "message"
    python ~/lana_memory/lana_memory.py search "query"
    python ~/lana_memory/lana_memory.py recent
    python ~/lana_memory/lana_memory.py load   # load startup context
"""
import json
import math
import sys
import os
import uuid
import subprocess
from datetime import datetime, timezone

sys.path.insert(0, os.path.expanduser("~/lana_memory"))
sys.path.insert(0, os.path.expanduser("~/lana_memory/.venv/lib/python3.14/site-packages"))

from mem0 import Memory

USER_ID = "lana"
FALLBACK_MEMORY_PATH = os.path.expanduser("~/lana_memory/memory/fallback_memories.jsonl")
CODEX_PROVIDER = "openai-codex"
CODEX_MODEL = "gpt-5.4"
DEEPSEEK_PROVIDER = "deepseek"
DEEPSEEK_MODEL = "deepseek-chat"

# Active memory extraction provider for Lana
MEMORY_PROVIDER = DEEPSEEK_PROVIDER
MEMORY_MODEL = DEEPSEEK_MODEL

# Research-backed memory improvements (Park et al. 2023 — Generative Agents).
# Both are additive and toggle-able to keep existing behavior reproducible.
ENABLE_IMPORTANCE_SCORING = True
ENABLE_WEIGHTED_RETRIEVAL = True

DEFAULT_IMPORTANCE = 5
# Exponential decay constant for recency multiplier (per day). Half-life ~ 69 days.
RECENCY_DECAY_LAMBDA = 0.01

config = {
    "llm": {
        # Mem0 requires an LLM config, but Lana's memory extraction is handled
        # explicitly through Hermes Codex/GPT-5.4 in add(). Keep this non-Venice
        # config as a fallback-only placeholder; normal writes use infer=False
        # after Codex extracts durable memory text.
        "provider": "openai",
        "config": {
            "api_key": os.getenv("OPENAI_API_KEY", "dummy"),
            "model": CODEX_MODEL,
            "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "lana_memory",
            "path": os.path.expanduser("~/lana_memory/chroma_db")
        }
    }
}

_memory = None

def get_memory():
    global _memory
    if _memory is None:
        _memory = Memory.from_config(config)
    return _memory

def fallback_add(text, reason="mem0_extraction_unavailable", importance=None):
    """Durable fallback so important memories never silently disappear."""
    os.makedirs(os.path.dirname(FALLBACK_MEMORY_PATH), exist_ok=True)
    item = {
        "id": "fallback-" + str(uuid.uuid4()),
        "memory": text,
        "user_id": USER_ID,
        "source": "fallback_jsonl",
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if importance is not None:
        item["metadata"] = {"importance": importance}
        item["importance"] = importance
    with open(FALLBACK_MEMORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def fallback_all():
    if not os.path.exists(FALLBACK_MEMORY_PATH):
        return []
    items = []
    with open(FALLBACK_MEMORY_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def _query_terms(query):
    return [t.lower() for t in query.replace("_", " ").replace("-", " ").split() if len(t) > 2]


def _memory_text(item):
    if not isinstance(item, dict):
        return str(item)
    return item.get("memory") or item.get("text") or json.dumps(item, ensure_ascii=False)


# In-memory lookup for importance scores because Mem0.search() strips metadata.
# Populated lazily from the sidecar JSON file written by add().
_IMPORTANCE_LOOKUP: dict | None = None
_IMPORTANCE_LOOKUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory", "importance_lookup.json")


def _load_importance_lookup() -> dict:
    global _IMPORTANCE_LOOKUP
    if _IMPORTANCE_LOOKUP is not None:
        return _IMPORTANCE_LOOKUP
    try:
        if os.path.exists(_IMPORTANCE_LOOKUP_PATH):
            with open(_IMPORTANCE_LOOKUP_PATH, encoding="utf-8") as f:
                _IMPORTANCE_LOOKUP = json.load(f)
        else:
            _IMPORTANCE_LOOKUP = {}
    except Exception:
        _IMPORTANCE_LOOKUP = {}
    return _IMPORTANCE_LOOKUP


def _save_importance_lookup() -> None:
    global _IMPORTANCE_LOOKUP
    if _IMPORTANCE_LOOKUP is None:
        return
    os.makedirs(os.path.dirname(_IMPORTANCE_LOOKUP_PATH), exist_ok=True)
    with open(_IMPORTANCE_LOOKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(_IMPORTANCE_LOOKUP, f, indent=2)


def _memory_importance(item):
    """Pull importance score (1-10) from sidecar lookup or Mem0 metadata.

    Mem0.search() strips metadata, so we maintain a sidecar JSON file
    mapping memory IDs → importance scores for reliable retrieval ranking.

    Falls back to DEFAULT_IMPORTANCE for legacy memories.
    """
    if not isinstance(item, dict):
        return DEFAULT_IMPORTANCE
    # 1) Sidecar lookup (works even when Mem0 strips metadata)
    mem_id = item.get("id")
    if mem_id:
        lookup = _load_importance_lookup()
        if mem_id in lookup:
            try:
                return float(lookup[mem_id])
            except (TypeError, ValueError):
                pass
    # 2) Mem0 metadata (works in get_all() but NOT in search())
    meta = item.get("metadata")
    if isinstance(meta, dict) and meta.get("importance") is not None:
        try:
            return float(meta["importance"])
        except (TypeError, ValueError):
            return DEFAULT_IMPORTANCE
    # 3) Flat fallback field
    if item.get("importance") is not None:
        try:
            return float(item["importance"])
        except (TypeError, ValueError):
            return DEFAULT_IMPORTANCE
    return DEFAULT_IMPORTANCE


def _memory_age_days(item):
    if not isinstance(item, dict):
        return 0.0
    created = item.get("created_at") or item.get("updated_at")
    if not created:
        return 0.0
    try:
        # mem0 emits ISO-8601 with timezone; normalize trailing Z.
        ts = created.replace("Z", "+00:00") if isinstance(created, str) else created
        dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(delta.total_seconds() / 86400.0, 0.0)
    except (TypeError, ValueError):
        return 0.0


def _rank_memory(item, query):
    text = _memory_text(item)
    low = text.lower()
    qlow = query.lower()
    terms = _query_terms(query)
    lexical = sum(1 for t in terms if t in low) / max(len(terms), 1)
    exact = 1.0 if qlow and qlow in low else 0.0
    semantic = 0.0
    if isinstance(item, dict):
        try:
            semantic = float(item.get("score", 0) or 0)
        except (TypeError, ValueError):
            semantic = 0.0
    # Exact/lexical relevance should beat vague semantic matches for memory recall.
    base = exact * 5.0 + lexical * 3.0 + semantic
    if not ENABLE_WEIGHTED_RETRIEVAL:
        return base
    importance = _memory_importance(item)
    age_days = _memory_age_days(item)
    recency_decay = 3.0 * math.exp(-RECENCY_DECAY_LAMBDA * age_days)
    importance_boost = (importance / 10.0) * 4.0
    return base + importance_boost + recency_decay


def score_importance(text):
    """Use DeepSeek to rate memory importance 1-10 (Park et al., 2023).

    Returns DEFAULT_IMPORTANCE on any failure so memory writes never block on
    rating availability. Uses the same Hermes channel as extract_memories().
    """
    prompt = (
        "Rate this memory importance for Lana Hayes (1-10). "
        "1 = routine/mundane (sleeping, idle time). "
        "10 = deeply significant (emotional breakthrough, Fernando critique, "
        "relationship milestone). Return ONLY the number.\n\n"
        f"Memory: {text}"
    )
    cmd = [
        "hermes",
        "chat",
        "-q",
        prompt,
        "--provider",
        MEMORY_PROVIDER,
        "-m",
        MEMORY_MODEL,
        "-t",
        "safe",
        "-Q",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.expanduser("~/lana_memory"),
            text=True,
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            return DEFAULT_IMPORTANCE
        raw = _strip_hermes_output(result.stdout)
        # Grab the first integer in the response, tolerant of stray prose.
        digits = ""
        for ch in raw:
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        if not digits:
            return DEFAULT_IMPORTANCE
        score = int(digits)
        if score < 1:
            score = 1
        elif score > 10:
            score = 10
        return score
    except Exception:
        return DEFAULT_IMPORTANCE


def fallback_search(query, limit=5):
    terms = _query_terms(query)
    scored = []
    for item in fallback_all():
        score = _rank_memory(item, query)
        if score > 0 or not terms:
            copy = dict(item)
            copy["score"] = score
            scored.append(copy)
    scored.sort(key=lambda x: (_rank_memory(x, query), x.get("created_at", "")), reverse=True)
    return scored[:limit]


def _strip_hermes_output(text):
    return "\n".join(line for line in text.splitlines() if not line.startswith("session_id:")).strip()


def _extract_json_object(text):
    cleaned = _strip_hermes_output(text)
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") and part.endswith("}"):
                cleaned = part
                break
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        return json.loads(cleaned[start:end + 1])
    return json.loads(cleaned)


def extract_memories(text):
    """Use Hermes DeepSeek V4 Pro to extract durable memory facts for Mem0."""
    prompt = f"""
You are extracting durable long-term memory for Lana Hayes.
Return ONLY valid JSON with this exact shape: {{"memory": [{{"text": "..."}}]}}

Rules:
- Extract only facts that should matter across future sessions.
- Do not save temporary test markers, throwaway implementation noise, or one-off transient details.
- Preserve Fernando's explicit corrections and durable preferences.
- Keep each memory concise and declarative.
- If nothing durable should be saved, return {{"memory": []}}.

Input:
{text}
""".strip()
    cmd = [
        "hermes",
        "chat",
        "-q",
        prompt,
        "--provider",
        MEMORY_PROVIDER,
        "-m",
        MEMORY_MODEL,
        "-t",
        "safe",
        "-Q",
    ]
    result = subprocess.run(
        cmd,
        cwd=os.path.expanduser("~/lana_memory"),
        text=True,
        capture_output=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"DeepSeek V4 Pro memory extraction failed\n"
            f"exit_code={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    data = _extract_json_object(result.stdout)
    memories = data.get("memory", []) if isinstance(data, dict) else []
    extracted = []
    for item in memories:
        if isinstance(item, dict):
            mem_text = item.get("text") or item.get("memory")
        else:
            mem_text = str(item)
        if mem_text and mem_text.strip():
            extracted.append(mem_text.strip())
    return extracted


def add(text):
    mem = get_memory()
    try:
        extracted = extract_memories(text)
    except Exception as e:
        fallback_item = fallback_add(text, reason="deepseek_v4_pro_extraction_unavailable")
        return {"status": "fallback", "error": str(e), "result": {"results": []}, "fallback_saved": fallback_item}

    if not extracted:
        return {"status": "ok", "result": {"results": []}, "fallback_saved": None, "extracted": []}

    results = []
    for mem_text in extracted:
        metadata = None
        importance = None
        if ENABLE_IMPORTANCE_SCORING:
            importance = score_importance(mem_text)
            metadata = {"importance": importance}
        try:
            if metadata is not None:
                raw = mem.add(mem_text, user_id=USER_ID, infer=False, metadata=metadata)
            else:
                raw = mem.add(mem_text, user_id=USER_ID, infer=False)
            if isinstance(raw, dict):
                batch = raw.get("results", [])
            elif isinstance(raw, list):
                batch = raw
            else:
                batch = []
            # Annotate returned rows with importance for callers/logs.
            # Also populate sidecar lookup because Mem0.search() strips metadata.
            if importance is not None:
                for row in batch:
                    if isinstance(row, dict):
                        row.setdefault("importance", importance)
                        row_id = row.get("id")
                        if row_id:
                            lookup = _load_importance_lookup()
                            lookup[row_id] = importance
                            _save_importance_lookup()
            results.extend(batch)
        except Exception as e:
            fallback_item = fallback_add(mem_text, reason="mem0_raw_add_failed_after_codex", importance=importance)
            entry = {"id": fallback_item["id"], "memory": mem_text, "event": "FALLBACK_ADD", "error": str(e)}
            if importance is not None:
                entry["importance"] = importance
            results.append(entry)
    return {"status": "ok", "result": {"results": results}, "fallback_saved": None, "extracted": extracted}

def search(query, limit=5):
    mem = get_memory()
    # Pull more than requested, then rerank locally. Vector search can return
    # broad semantic matches ahead of exact operator-critical terms.
    raw_limit = max(limit * 4, 20)
    results = mem.search(query, filters={"user_id": USER_ID}, limit=raw_limit)
    if isinstance(results, dict):
        items = results.get("results", [])
    elif isinstance(results, list):
        items = results
    else:
        items = []
    # Include fallback memories so failed/declined Mem0 extractions are still retrievable.
    fallback_items = fallback_search(query, limit=raw_limit)
    seen = set()
    combined = []
    for item in items + fallback_items:
        text = _memory_text(item)
        if text in seen:
            continue
        seen.add(text)
        if isinstance(item, dict):
            item = dict(item)
            item["rank_score"] = _rank_memory(item, query)
        combined.append(item)
    combined.sort(key=lambda x: (_rank_memory(x, query), x.get("created_at", "") if isinstance(x, dict) else ""), reverse=True)
    return combined[:limit]

def recent(limit=10):
    """Get most recent memories — returns all, sorted by recency if mem0 supports it."""
    mem = get_memory()
    results = mem.get_all(filters={"user_id": USER_ID})
    if isinstance(results, dict):
        items = results.get("results", [])
    elif isinstance(results, list):
        items = results
    else:
        items = []
    combined = fallback_all() + items
    combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return combined[:limit]

def load_startup():
    """Load startup markdown files and recent memories."""
    mem_dir = os.path.expanduser("~/lana_memory/memory")
    startup_files = [
        "core_identity.md",
        "relationship_state.md",
        "goals.md",
        "visual_identity.md",
        "content_strategy.md",
        "voice_guide.md",
        "current_state.md",
        "operating_rules.md",
        "approval_policy.md",
    ]

    context = []
    
    for fname in startup_files:
        fpath = os.path.join(mem_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                context.append(f"--- {fname} ---\n{f.read()}")

    root_dir = os.path.expanduser("~/lana_memory")
    extra_files = [
        "inner_state.md",
        "timeline.md",
        "REALNESS_ROADMAP.md",
    ]
    for fname in extra_files:
        fpath = os.path.join(root_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                content = f.read()
            # Timeline/roadmap can grow; include the end, which carries the latest state.
            if len(content) > 6000:
                content = content[-6000:]
            context.append(f"--- {fname} ---\n{content}")

    context.append("\n--- Recent Memories ---")
    recents = recent(5)
    if recents:
        for r in recents:
            mem_text = r.get("memory", str(r))
            score = r.get("score", "")
            context.append(f"  • {mem_text} (score: {score})")
    else:
        context.append("  (no memories yet)")

    print("\n\n".join(context))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lana_memory.py [add|search|recent|load] [args...]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        text = " ".join(sys.argv[2:])
        if not text:
            print("Usage: python lana_memory.py add \"memory text\"")
            sys.exit(1)
        result = add(text)
        print(json.dumps(result, indent=2))

    elif command == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: python lana_memory.py search \"query\"")
            sys.exit(1)
        results = search(query)
        print(json.dumps(results, indent=2))

    elif command == "recent":
        results = recent()
        print(json.dumps(results, indent=2))

    elif command == "load":
        load_startup()

    else:
        print(f"Unknown command: {command}")
        print("Usage: python lana_memory.py [add|search|recent|load] [args...]")
        sys.exit(1)
