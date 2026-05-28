#!/usr/bin/env python3
"""Lana life tick runner.

Advances Lana's state every 30 minutes and refreshes the startup prefill
so new conversations inherit the latest day-state.

Phase 6: also triggers an auto-dream cycle when Lana is asleep, it's night,
and no dream has run in the last 20 hours.

Silent when nothing meaningful changed.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/fernandoserina/lana_memory")
PY = ROOT / ".venv" / "bin" / "python3"
LIFE = ROOT / "lana_life.py"
REFRESH = ROOT / "refresh_prefill.py"
DREAM = ROOT / "dream_cycle.py"
DAY_STATE = ROOT / "day_state.json"
DREAMS_DIR = ROOT / "dreams"
AUTO_DREAM_SENTINEL = ROOT / "auto_dream_last_trigger.txt"
AUTO_DREAM_FAILURE_LOG = ROOT / "auto_dream_failures.txt"


def run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PY), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ── Phase 6 helpers ────────────────────────────────────────────────────

def _load_day_state() -> dict:
    try:
        return json.loads(DAY_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _hours_since_last_dream() -> float:
    """Return hours since the most recent dream file was written, or inf if none."""
    if not DREAMS_DIR.exists():
        return float("inf")
    dream_files = sorted(DREAMS_DIR.glob("dream_*.md"))
    if not dream_files:
        return float("inf")
    mtime = os.path.getmtime(str(dream_files[-1]))
    return (datetime.datetime.now().timestamp() - mtime) / 3600


def _should_trigger_auto_dream(state: dict) -> bool:
    """True when all conditions for a quiet-night auto-dream are met."""
    # Must be asleep and in the night band
    if state.get("awake", True):
        return False
    if state.get("time_band", "") != "night":
        return False

    # Only once per calendar day (sentinel guard)
    today_str = datetime.date.today().isoformat()
    if AUTO_DREAM_SENTINEL.exists():
        last = AUTO_DREAM_SENTINEL.read_text(encoding="utf-8").strip()
        if last == today_str:
            return False

    # Require at least 20 h gap since last dream
    if _hours_since_last_dream() < 20:
        return False

    return True


def _trigger_auto_dream(state: dict) -> bool:
    """Run dream_cycle.py with a quiet-night reflection event."""
    if not DREAM.exists():
        return False
    band = state.get("time_band", "night")
    event = (
        f"Quiet night reflection — it is {band} and Lana is asleep, "
        "processing the day's experiences and feelings."
    )
    result = run(str(DREAM), "--event", event, timeout=480)
    success = result.returncode == 0
    if success:
        AUTO_DREAM_SENTINEL.write_text(
            datetime.date.today().isoformat(), encoding="utf-8"
        )
        print("auto-dream: triggered and completed")
    else:
        AUTO_DREAM_FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTO_DREAM_FAILURE_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] exit={result.returncode}\n")
            f.write("STDOUT:\n" + (result.stdout or "")[-2000:] + "\n")
            f.write("STDERR:\n" + (result.stderr or "")[-4000:] + "\n---\n")
        print(f"auto-dream: failed (exit {result.returncode}) details={AUTO_DREAM_FAILURE_LOG}")
    return success


# ── Main ───────────────────────────────────────────────────────────────

def main() -> int:
    tick = run(str(LIFE), "tick")
    if tick.returncode != 0:
        print(f"ERROR: tick exit={tick.returncode} stderr={tick.stderr[:300]}")
        return tick.returncode

    # Keep startup context fresh after every tick, even if the textual output is quiet.
    refresh = run(str(REFRESH))
    if refresh.returncode != 0:
        print(f"ERROR: refresh exit={refresh.returncode} stderr={refresh.stderr[:300]}")
        return refresh.returncode

    output = (tick.stdout or "").strip()
    if output and "no change" not in output.lower():
        print(output)

    # Phase 6: auto-dream — runs only when asleep + night + >20 h since last dream
    state = _load_day_state()
    if _should_trigger_auto_dream(state):
        _trigger_auto_dream(state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
