"""
Lana memory maintenance — forgetting + cold storage.

Implements the Microsoft Memory Architecture (2026) idea: long-lived prompt
memories rot unless you actively forget the noise and consolidate gist for the
stale-but-still-meaningful records.

Pipeline per run:
1. Pull every Mem0 memory for USER_ID.
2. Compute decayed_score = base_importance * exp(-lambda * age_days).
3. Memories with decayed_score < COLD_STORE_THRESHOLD → moved to cold storage JSONL,
   removed from Mem0.
4. Memories older than GIST_AGE_DAYS with raw importance < GIST_IMPORTANCE_THRESHOLD
   → summarized to a one-line gist via DeepSeek, gist written to cold store, original
   removed from Mem0.

Usage:
    python memory_maintenance.py --dry-run        # report what would change
    python memory_maintenance.py                  # execute

Flags:
    ENABLE_FORGETTING — module-level kill switch. If False, the script is a no-op.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/lana_memory"))

import lana_memory  # noqa: E402

ENABLE_FORGETTING = True

ROOT = Path(os.path.expanduser("~/lana_memory"))
COLD_STORE_PATH = ROOT / "memory" / "cold_store.jsonl"

# Decay tuning. Half-life ~ 69 days, so a memory rated 5 falls under 1.0 at ~160d.
DECAY_LAMBDA = 0.01
COLD_STORE_THRESHOLD = 1.0

# Gist consolidation tuning.
GIST_AGE_DAYS = 14
GIST_IMPORTANCE_THRESHOLD = 3


def _parse_created(item: dict) -> datetime | None:
    raw = item.get("created_at") or item.get("updated_at")
    if not raw:
        return None
    try:
        ts = raw.replace("Z", "+00:00") if isinstance(raw, str) else raw
        dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _age_days(item: dict) -> float:
    dt = _parse_created(item)
    if dt is None:
        return 0.0
    delta = datetime.now(timezone.utc) - dt
    return max(delta.total_seconds() / 86400.0, 0.0)


def _importance(item: dict) -> float:
    meta = item.get("metadata") if isinstance(item, dict) else None
    if isinstance(meta, dict) and meta.get("importance") is not None:
        try:
            return float(meta["importance"])
        except (TypeError, ValueError):
            pass
    if item.get("importance") is not None:
        try:
            return float(item["importance"])
        except (TypeError, ValueError):
            pass
    return float(lana_memory.DEFAULT_IMPORTANCE)


def _decayed_score(item: dict) -> float:
    return _importance(item) * math.exp(-DECAY_LAMBDA * _age_days(item))


def _load_mem0_items() -> list[dict]:
    mem = lana_memory.get_memory()
    raw = mem.get_all(filters={"user_id": lana_memory.USER_ID})
    if isinstance(raw, dict):
        items = raw.get("results", [])
    elif isinstance(raw, list):
        items = raw
    else:
        items = []
    return [i for i in items if isinstance(i, dict)]


def _append_cold(record: dict) -> None:
    COLD_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COLD_STORE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _summarize_gist(text: str) -> str | None:
    """Compress a stale memory to a one-line gist via DeepSeek. None on failure."""
    prompt = (
        "Summarize this memory of Lana Hayes into ONE short sentence (under 25 words). "
        "Keep the durable meaning; drop transient detail. Return ONLY the sentence.\n\n"
        f"Memory: {text}"
    )
    cmd = [
        "hermes",
        "chat",
        "-q",
        prompt,
        "--provider",
        lana_memory.MEMORY_PROVIDER,
        "-m",
        lana_memory.MEMORY_MODEL,
        "-t",
        "safe",
        "-Q",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            return None
        cleaned = lana_memory._strip_hermes_output(result.stdout).strip()
        # Strip leading bullets/quotes the model sometimes adds.
        cleaned = cleaned.lstrip("-•* \"'").rstrip(" \"'")
        return cleaned or None
    except Exception:
        return None


def _classify(item: dict) -> tuple[str, dict]:
    """Return (action, info) for a single memory."""
    decayed = _decayed_score(item)
    importance = _importance(item)
    age = _age_days(item)
    info = {
        "id": item.get("id"),
        "memory": (item.get("memory") or item.get("text") or "")[:120],
        "importance": importance,
        "age_days": round(age, 2),
        "decayed_score": round(decayed, 4),
    }
    if decayed < COLD_STORE_THRESHOLD:
        return "cold_archive", info
    if age > GIST_AGE_DAYS and importance < GIST_IMPORTANCE_THRESHOLD:
        return "gist_consolidate", info
    return "keep", info


def run(dry_run: bool = False) -> dict:
    if not ENABLE_FORGETTING:
        return {"status": "disabled", "kept": 0, "cold_archived": 0, "gist_consolidated": 0}

    items = _load_mem0_items()
    mem = lana_memory.get_memory()

    actions = {"keep": [], "cold_archive": [], "gist_consolidate": []}
    for item in items:
        action, info = _classify(item)
        actions[action].append((item, info))

    cold_archived = 0
    gist_consolidated = 0
    errors: list[dict] = []

    for item, info in actions["cold_archive"]:
        record = {
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "reason": "decayed_below_threshold",
            "decayed_score": info["decayed_score"],
            "importance": info["importance"],
            "age_days": info["age_days"],
            "original": item,
        }
        if dry_run:
            cold_archived += 1
            continue
        try:
            _append_cold(record)
            if item.get("id"):
                mem.delete(item["id"])
            cold_archived += 1
        except Exception as e:
            errors.append({"id": item.get("id"), "stage": "cold_archive", "error": str(e)})

    for item, info in actions["gist_consolidate"]:
        original_text = item.get("memory") or item.get("text") or ""
        gist = None
        if not dry_run:
            gist = _summarize_gist(original_text)
            if not gist:
                errors.append({"id": item.get("id"), "stage": "gist_summary_failed"})
                continue
        record = {
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "reason": "gist_consolidated",
            "decayed_score": info["decayed_score"],
            "importance": info["importance"],
            "age_days": info["age_days"],
            "gist": gist or "(dry-run: gist not generated)",
            "original": item,
        }
        if dry_run:
            gist_consolidated += 1
            continue
        try:
            _append_cold(record)
            if item.get("id"):
                mem.delete(item["id"])
            gist_consolidated += 1
        except Exception as e:
            errors.append({"id": item.get("id"), "stage": "gist_consolidate", "error": str(e)})

    return {
        "status": "dry_run" if dry_run else "ok",
        "total_inspected": len(items),
        "kept": len(actions["keep"]),
        "cold_archived": cold_archived,
        "gist_consolidated": gist_consolidated,
        "errors": errors,
        "preview": {
            "cold_archive": [info for _, info in actions["cold_archive"][:10]],
            "gist_consolidate": [info for _, info in actions["gist_consolidate"][:10]],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lana memory forgetting + cold-storage maintenance.")
    parser.add_argument("--dry-run", action="store_true", help="Report planned actions without modifying Mem0 or cold store.")
    args = parser.parse_args()
    report = run(dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
