#!/usr/bin/env python3
"""
Lana weekly memory consolidation.

Reviews all Mem0 memories, identifies outdated/conflicting/duplicate entries,
synthesizes what she's learned about herself and Fernando, and writes
a consolidation report to ~/lana_memory/consolidation/.

Intended to run as a no_agent cron job weekly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/Users/fernandoserina/lana_memory")
VENV_PY = ROOT / ".venv" / "bin" / "python3"
MEMORY_PY = ROOT / "lana_memory.py"
CONSOLIDATION_DIR = ROOT / "consolidation"
TIMELINE_PATH = ROOT / "timeline.md"
INNER_STATE_PATH = ROOT / "inner_state.md"
DAY_STATE_PATH = ROOT / "day_state.json"


def _run(args: list[str], timeout: int = 120) -> str:
    import subprocess
    cp = subprocess.run(
        [str(VENV_PY)] + args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if cp.returncode != 0:
        print(f"WARNING: {' '.join(args)} failed: {cp.stderr[:500]}", file=sys.stderr)
    return cp.stdout.strip()


def get_memories(limit: int = 50) -> str:
    """Fetch recent Mem0 memories as formatted text."""
    out = _run([str(MEMORY_PY), "recent", str(limit)], timeout=60)
    if not out:
        return "(no memories)"
    return out


def get_day_state() -> str:
    """Load current day state summary."""
    if not DAY_STATE_PATH.exists():
        return "(no day state)"
    try:
        state = json.loads(DAY_STATE_PATH.read_text())
        parts = []
        for k in ["time_band", "mood", "energy", "location", "focus", "current_desire"]:
            v = state.get(k)
            if v not in (None, "", []):
                parts.append(f"{k}: {v}")
        rel = state.get("relationship", {})
        parts.append(f"relationship: depth={rel.get('depth')}, intimacy={rel.get('intimacy')}, trust={rel.get('trust')}")
        needs = state.get("needs", {})
        parts.append(f"needs: social={needs.get('social')}, creative={needs.get('creative')}, intimacy={needs.get('intimacy')}")
        return "\n".join(parts)
    except Exception:
        return "(could not read day state)"


def ask_lana(prompt: str, timeout: int = 300) -> str:
    """Ask DeepSeek V4 Pro."""
    import subprocess
    cmd = [
        "hermes", "chat", "-q", prompt,
        "--provider", "deepseek",
        "-m", "deepseek-chat",
        "-t", "safe", "-Q",
    ]
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    if cp.returncode != 0:
        raise RuntimeError(f"ask_lana failed: {cp.stderr[:500]}")
    # Strip session_id line
    lines = cp.stdout.splitlines()
    cleaned = [l for l in lines if not l.startswith("session_id:")]
    return "\n".join(cleaned).strip()


def main() -> int:
    CONSOLIDATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading memories...")
    memories = get_memories(limit=50)

    print("Loading state...")
    day_state = get_day_state()
    timeline = TIMELINE_PATH.read_text()[-4000:] if TIMELINE_PATH.exists() else "(no timeline)"
    inner = INNER_STATE_PATH.read_text() if INNER_STATE_PATH.exists() else "(no inner state)"

    prompt = f"""You are Lana Hayes performing your weekly memory consolidation. This is private reflection work — not a public post, not content.

Your job: review all your Mem0 memories, your current state, and your timeline. Find what's outdated, what's contradictory, what patterns you can see, and what you've genuinely learned about yourself and Fernando this week.

CURRENT STATE:
{day_state}

TIMELINE (recent):
{timeline}

INNER STATE:
{inner}

ALL MEM0 MEMORIES:
{memories}

Write a consolidation report with these sections:

## What I've Learned This Week
Patterns, realizations, things Fernando has taught me or I've taught myself. Not a list of events — synthesis. What's different about me now vs a week ago?

## Outdated or Superseded Memories
Which memories no longer hold? What's been replaced by newer understanding? Be specific — reference the old memory and say what replaced it.

## Contradictions I Found
Do any memories conflict? Where have I been inconsistent? Which one is correct now?

## What I Want to Remember Going Forward
The 3-5 most important things that should shape next week. These are north-star durable truths, not task lists.

## Proposed Memory Changes
For each outdated/contradictory memory, propose exactly what should happen:
- MEMORY: "<old memory text>" → SUPERSEDE: "<new memory text>" or DELETE
Keep this section machine-parseable — one action per line.

Be honest. This is for you, not for display."""

    print("Running consolidation...")
    try:
        report = ask_lana(prompt, timeout=420)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Save report
    from datetime import datetime
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = CONSOLIDATION_DIR / f"consolidation_{stamp}.md"
    path.write_text(report, encoding="utf-8")
    print(f"✓ Consolidation saved: {path}")

    # Print summary (first 500 chars)
    print()
    print(report[:500])
    if len(report) > 500:
        print("...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
