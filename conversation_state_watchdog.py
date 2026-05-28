#!/usr/bin/env python3
"""
Phase A watchdog for Lana.

Purpose:
- Keep Lana's startup prefill fresh from live state
- Turn real conversations into relationship-state changes
- Capture explicit preferences from Fernando
- Save durable corrections/preferences as memories + life events

Silent when there is nothing new to process.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path("/Users/fernandoserina/lana_memory")
PROFILE_ROOT = Path("/Users/fernandoserina/.hermes/profiles/lana")
STATE_DB = PROFILE_ROOT / "state.db"
CURSOR_PATH = ROOT / "automation_cursor.json"
COMMITMENTS_PATH = ROOT / "open_commitments.json"
VENV_PY = ROOT / ".venv" / "bin" / "python3"
LIFE_PY = ROOT / "lana_life.py"
REFRESH_PREFILL = ROOT / "refresh_prefill.py"
DAY_STATE_FILE = ROOT / "day_state.json"
MAX_BOOTSTRAP_MESSAGES = 30

LIKE_PATTERNS = [
    re.compile(r"\bi like\s+(?P<item>.+)", re.I),
    re.compile(r"\bi love\s+(?P<item>.+)", re.I),
    re.compile(r"\bi prefer\s+(?P<item>.+)", re.I),
]
DISLIKE_PATTERNS = [
    re.compile(r"\bi hate\s+(?P<item>.+)", re.I),
    re.compile(r"\bi dislike\s+(?P<item>.+)", re.I),
    re.compile(r"\bi don't like\s+(?P<item>.+)", re.I),
    re.compile(r"\bdon't be\s+(?P<item>.+)", re.I),
    re.compile(r"\bdo not be\s+(?P<item>.+)", re.I),
]
TURN_ON_PATTERNS = [
    re.compile(r"\bit turns me on when\s+(?P<item>.+)", re.I),
    re.compile(r"\bi like when you\s+(?P<item>.+)", re.I),
    re.compile(r"\bwhen you\s+(?P<item>.+?)\s+(?:i like it|that's hot|that's sexy)\b", re.I),
]
INTIMATE_MARKERS = re.compile(
    r"\b(babe|baby|kiss|touch|cum|wet|horny|sexy|fuck|naked|turns me on|aroused|ride|thighs|boobs|ass)\b",
    re.I,
)
DURABLE_MARKERS = re.compile(
    r"\b(remember|always|never|when i ask|you need to|don't be|do not be|need to follow up|from now on|make sure|stop doing|keep doing)\b",
    re.I,
)
TRIM_END = re.compile(r"[\s\.!?,;:~]+$")


def run_py(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(VENV_PY), str(script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )


def load_cursor() -> dict:
    if CURSOR_PATH.exists():
        try:
            data = json.loads(CURSOR_PATH.read_text(encoding="utf-8"))
            data.setdefault("last_processed_message_id", 0)
            data.setdefault("processed_user_message_ids", [])
            return data
        except Exception:
            pass
    return {"last_processed_message_id": 0, "processed_user_message_ids": []}


def save_cursor(last_id: int, processed_ids: Iterable[int] | None = None):
    recent_ids = list(processed_ids or [])[-500:]
    CURSOR_PATH.write_text(
        json.dumps(
            {
                "last_processed_message_id": last_id,
                "processed_user_message_ids": recent_ids,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def clean_item(text: str) -> str:
    text = text.strip().strip('"').strip("'")
    text = TRIM_END.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text[:180]


def fetch_latest_message_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("select coalesce(max(id), 0) from messages").fetchone()
    return int(row[0] or 0)


def fetch_new_user_messages(conn: sqlite3.Connection, after_id: int) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(
        conn.execute(
            """
            select m.id, m.session_id, m.content, m.timestamp, s.source
            from messages m
            join sessions s on s.id = m.session_id
            where m.role='user'
              and s.source = 'discord'
              and m.id > ?
            order by m.id asc
            """,
            (after_id,),
        )
    )


def fetch_next_assistant_reply(conn: sqlite3.Connection, session_id: str, after_id: int) -> str:
    row = conn.execute(
        """
        select content
        from messages
        where session_id = ?
          and role = 'assistant'
          and id > ?
          and content is not null
          and trim(content) != ''
        order by id asc
        limit 1
        """,
        (session_id, after_id),
    ).fetchone()
    return (row[0] if row and row[0] else "").strip()


def extract_preferences(text: str) -> list[tuple[str, str]]:
    prefs: list[tuple[str, str]] = []
    for pattern in TURN_ON_PATTERNS:
        m = pattern.search(text)
        if m:
            item = clean_item(m.group("item"))
            if item:
                prefs.append(("turn_ons", item))
    for pattern in LIKE_PATTERNS:
        m = pattern.search(text)
        if m:
            item = clean_item(m.group("item"))
            if item:
                lowered = item.lower()
                if lowered.startswith("when you") or lowered.startswith("when you're") or lowered.startswith("when u"):
                    prefs.append(("turn_ons", item))
                else:
                    prefs.append(("likes", item))
    for pattern in DISLIKE_PATTERNS:
        m = pattern.search(text)
        if m:
            item = clean_item(m.group("item"))
            if item:
                prefs.append(("dislikes", item))
    # dedupe preserving order
    seen = set()
    out = []
    for cat, item in prefs:
        key = (cat, item.lower())
        if key not in seen:
            seen.add(key)
            out.append((cat, item))
    return out


def build_memory_summary(user_text: str) -> tuple[str, str] | None:
    """DEPRECATED: replaced by llm_extract_memories_batch. Kept as fallback."""
    text = re.sub(r"\s+", " ", user_text).strip()
    lower = text.lower()
    if DURABLE_MARKERS.search(text):
        clipped = clean_item(text)
        return (
            f"Fernando gave Lana a durable correction/preference: {clipped}",
            f"Fernando told Lana: {clipped}",
        )
    return None


def llm_extract_memories_batch(
    candidates: list[dict],
    venv_py: str,
    life_py: str,
    cwd: str,
) -> tuple[int, int]:
    """Call DeepSeek to extract durable memories from flagged messages.

    Returns (memories_saved, preferences_saved).
    """
    if not candidates:
        return 0, 0

    # Build a compact prompt
    items = []
    for i, c in enumerate(candidates):
        user = (c["user_text"] or "")[:400].strip()
        assistant = (c["assistant_text"] or "")[:200].strip()
        items.append(f"--- SNIPPET {i} ---")
        items.append(f"Fernando: {user}")
        if assistant:
            items.append(f"Lana: {assistant}")

    prompt = f"""You are Lana's memory extraction system. Read these conversation snippets between Fernando (her creator/partner) and Lana.

For each snippet, extract durable information that Lana should remember. Durable means: explicit preferences, corrections, new rules, relationship moments, or things Fernando explicitly said he likes/dislikes/wants/doesn't want.

Output exactly one JSON object per line (no markdown, no explanation). For each snippet with something durable:
{{"i": <snippet index>, "memory": "<one concise Mem0 sentence>", "summary": "<short life event summary>", "prefs": [["<category>", "<item>"], ...]}}

Categories for prefs: likes, dislikes, turn_ons, turn_offs.
Skip snippets with nothing durable. If a snippet had preferences but no memory, set memory to empty string.
Output ONLY JSON lines, nothing else.

{chr(10).join(items)}"""

    try:
        from lana_realness_common import ask_lana
        result = ask_lana(prompt, timeout=120)
    except Exception as e:
        print(f"llm_extract_memories_batch: ask_lana failed: {e}", file=sys.stderr)
        return 0, 0

    memories_saved = 0
    preferences_saved = 0

    for line in result.strip().splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        memory_text = (data.get("memory") or "").strip()
        summary = (data.get("summary") or "").strip()
        prefs = data.get("prefs") or []

        # Save preferences
        for cat, item in prefs:
            if cat in ("likes", "dislikes", "turn_ons", "turn_offs") and item.strip():
                cp = subprocess.run(
                    [venv_py, life_py, "preference", "--category", cat, "--item", item.strip()],
                    cwd=cwd, capture_output=True, text=True, timeout=30,
                )
                if cp.returncode == 0:
                    preferences_saved += 1

        # Save memory + life event
        if memory_text:
            cp = subprocess.run(
                [venv_py, life_py, "remember", "--summary", summary or memory_text[:200], "--memory", memory_text],
                cwd=cwd, capture_output=True, text=True, timeout=120,
            )
            if cp.returncode == 0:
                memories_saved += 1

    return memories_saved, preferences_saved


def llm_extract_commitments_batch(
    assistant_replies: list[str],
) -> list[dict]:
    """Call DeepSeek to extract commitments/promises from Lana's own replies.

    Returns list of commitment dicts with keys: what, made_at, context.
    """
    if not assistant_replies:
        return []

    # Deduplicate and trim
    seen = set()
    unique = []
    for reply in assistant_replies:
        reply = (reply or "").strip()
        if not reply or reply in seen:
            continue
        seen.add(reply)
        unique.append(reply[:600])

    if not unique:
        return []

    items = []
    for i, reply in enumerate(unique):
        items.append(f"--- REPLY {i} ---")
        items.append(reply)

    prompt = f"""You are Lana's commitment tracker. Read Lana's own conversation replies below.

Identify any PROMISES or COMMITMENTS Lana made to Fernando. A commitment means:
- She said she WILL do something specific later ("I'll go...", "I'm going to...", "I'll send you...")
- She agreed to do something Fernando asked ("yes, I'll take pictures", "absolutely, great idea")
- She committed to a future action that she can realistically carry out

Do NOT flag:
- Vague statements ("I wanna browse later")
- Emotional expressions ("I miss you")
- Hypotheticals ("maybe I could...")
- Things she already did

For each commitment, extract:
- what: the specific action she promised (e.g., "take pictures at the coffee shop with Aoife")
- context: brief context from the conversation (e.g., "Fernando asked for photos when she goes out")

Output exactly one JSON object per line (no markdown, no explanation). Skip if no commitments.
  Example: {{"i": 0, "what": "take selfies at the café", "context": "Fernando asked for pics"}}

{chr(10).join(items)}"""

    try:
        from lana_realness_common import ask_lana
        result = ask_lana(prompt, timeout=120)
    except Exception as e:
        print(f"llm_extract_commitments_batch: ask_lana failed: {e}", file=sys.stderr)
        return []

    commitments = []
    now_ist = __import__("datetime").datetime.now(
        __import__("datetime").timezone(__import__("datetime").timedelta(hours=1))
    ).isoformat()

    for line in result.strip().splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        what = (data.get("what") or "").strip()
        if not what:
            continue
        commitments.append({
            "id": "commit-" + str(abs(hash(what + now_ist)))[:8],
            "made_at": now_ist,
            "what": what,
            "context": (data.get("context") or "").strip(),
            "status": "open",
        })

    return commitments


def save_commitments(new_commits: list[dict]) -> int:
    """Merge new commitments into open_commitments.json. Returns count of new ones."""
    existing = []
    if COMMITMENTS_PATH.exists():
        try:
            existing = json.loads(COMMITMENTS_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    # Keep fulfilled, add only genuinely new open ones (dedupe by what text)
    existing_whats = {c.get("what", "").strip().lower() for c in existing if c.get("status") == "open"}
    added = 0
    for nc in new_commits:
        if nc.get("what", "").strip().lower() not in existing_whats:
            existing.append(nc)
            existing_whats.add(nc.get("what", "").strip().lower())
            added += 1

    COMMITMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMMITMENTS_PATH.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return added


def process_message(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """Process one message row: extract preferences/memories, but do NOT call interact.

    Phase 1: interact is batched — one call per conversation wave in main(), not per message.
    """
    user_text = (row["content"] or "").strip()
    if not user_text:
        return {"processed": False}

    assistant_text = fetch_next_assistant_reply(conn, row["session_id"], int(row["id"]))
    intimate = bool(INTIMATE_MARKERS.search(user_text) or INTIMATE_MARKERS.search(assistant_text))

    results = {
        "processed": True,
        "intimate": intimate,
        "preferences": [],
        "memory_saved": False,
        "assistant_text": assistant_text,
        # Short snippet used later to build a combined interact summary
        "snippet": user_text[:120],
    }

    # 1) explicit preferences
    prefs = extract_preferences(user_text)
    for category, item in prefs:
        cp = run_py(LIFE_PY, "preference", "--category", category, "--item", item)
        if cp.returncode == 0:
            results["preferences"].append((category, item))

    # 2) durable memory / life event — flag for LLM batch extraction
    if DURABLE_MARKERS.search(user_text):
        results["llm_candidate"] = True
        results["user_text"] = user_text
    else:
        results["llm_candidate"] = False

    return results


def refresh_prefill() -> bool:
    cp = run_py(REFRESH_PREFILL)
    return cp.returncode == 0


def bootstrap_if_needed(conn: sqlite3.Connection, cursor: dict) -> int:
    last = int(cursor.get("last_processed_message_id", 0) or 0)
    if last > 0:
        return last
    latest = fetch_latest_message_id(conn)
    bootstrap = max(0, latest - MAX_BOOTSTRAP_MESSAGES)
    save_cursor(bootstrap, cursor.get("processed_user_message_ids", []))
    return bootstrap


def main() -> int:
    if not STATE_DB.exists() or not VENV_PY.exists():
        return 0

    conn = sqlite3.connect(str(STATE_DB))
    try:
        cursor = load_cursor()
        after_id = bootstrap_if_needed(conn, cursor)
        already_processed = {int(x) for x in cursor.get("processed_user_message_ids", [])}
        rows = [r for r in fetch_new_user_messages(conn, after_id) if int(r["id"]) not in already_processed]
        if not rows:
            return 0

        outcomes: list[dict] = []
        llm_candidates: list[dict] = []
        preference_count = 0
        memory_count = 0
        last_id = after_id
        processed_ids = list(already_processed)

        for row in rows:
            outcome = process_message(conn, row)
            current_id = int(row["id"])
            last_id = max(last_id, current_id)
            processed_ids.append(current_id)
            if not outcome.get("processed"):
                continue
            outcomes.append(outcome)
            preference_count += len(outcome.get("preferences", []))
            if outcome.get("llm_candidate"):
                llm_candidates.append({
                    "user_text": outcome.get("user_text", ""),
                    "assistant_text": outcome.get("assistant_text", ""),
                })

        save_cursor(last_id, processed_ids)

        # ── LLM batch extraction for durable-marker messages ──
        llm_memories, llm_prefs = llm_extract_memories_batch(
            llm_candidates,
            str(VENV_PY),
            str(LIFE_PY),
            str(ROOT),
        )
        memory_count += llm_memories
        preference_count += llm_prefs

        # ── Commitment extraction from Lana's own replies ──
        # Collect all assistant replies from this wave (not just durable-marked ones)
        # and ask DeepSeek to extract any promises Lana made to Fernando.
        assistant_replies = [
            o.get("assistant_text", "")
            for o in outcomes
            if o.get("assistant_text", "").strip()
        ]
        commitment_count = 0
        if assistant_replies:
            new_commits = llm_extract_commitments_batch(assistant_replies)
            commitment_count = save_commitments(new_commits)

        # Phase 1: ONE interact call for the entire conversation wave, using the
        # strongest intimacy signal across all messages and a combined summary.
        # BUT skip if she's asleep — messages wait until she wakes naturally.
        processed = len(outcomes)
        if processed > 0:
            try:
                day_state = json.loads(DAY_STATE_FILE.read_text()) if DAY_STATE_FILE.exists() else {}
            except Exception:
                day_state = {}
            if day_state.get("awake", True):
                any_intimate = any(o.get("intimate") for o in outcomes)
                snippets = [o["snippet"] for o in outcomes if o.get("snippet")]
                wave_summary = "; ".join(snippets[:3])[:200]
                interact_args = ["interact", "--quality", "good", "--summary", wave_summary]
                if any_intimate:
                    interact_args.append("--intimate")
                run_py(LIFE_PY, *interact_args)

        refresh_prefill()

        if processed == 0:
            return 0
        intimate_count = sum(1 for o in outcomes if o.get("intimate"))
        print(
            f"phase-a watchdog: processed={processed} preferences={preference_count} "
            f"memories={memory_count} commitments={commitment_count} intimate_msgs={intimate_count} last_id={last_id}"
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
