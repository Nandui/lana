#!/usr/bin/env python3
"""
Lana Proactive Reach-Out Engine.

Decides when Lana should reach out to Fernando unprompted, generates a
natural message using her own brain (DeepSeek), and delivers it.

Architecture:
  reach_out.py          ← this file, called by cron every 30 min
  │
  ├── detect_triggers() → list of (trigger_name, priority, context)
  │     • commitment just fulfilled and not yet shared
  │     • high social need + no interaction in hours
  │     • general check-in if it's been too long
  │     • (future: Aoife event, project milestone, mood shift, etc.)
  │
  ├── should_reach_out(state, triggers) → (bool, trigger)
  │     • awake gate
  │     • energy gate
  │     • cooldown gate (max 1 per window)
  │     • conversation recency gate
  │     • returns highest-priority trigger
  │
  └── generate_message(trigger, state) → str
        • uses ask_lana (DeepSeek) with real state/context
        • natural, in her voice, not templated

Cooldown and gating ensure she never spams or feels automated.
Silent when nothing is worth reaching out about — no "no news" messages.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path("/Users/fernandoserina/lana_memory")
STATE_PATH = ROOT / "day_state.json"
COMMITMENTS_PATH = ROOT / "open_commitments.json"
LIFE_EVENTS_PATH = ROOT / "life_events.jsonl"
COOLDOWN_PATH = ROOT / "last_reach_out.txt"

IST = timezone(timedelta(hours=1))

# ── Config ──────────────────────────────────────────────────────────────

COOLDOWN_MINUTES = 120          # Minimum gap between reach-outs
MIN_ENERGY = 20                 # Must have at least this energy
SOCIAL_NEED_THRESHOLD = 35      # Social need must be above this for check-in
LONG_SILENCE_HOURS = 3          # Consider a check-in after this many hours
RECENT_INTERACTION_MINUTES = 30  # Don't reach out if talked within this window


# ── State helpers ───────────────────────────────────────────────────────

def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_commitments() -> list[dict]:
    try:
        return json.loads(COMMITMENTS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def save_commitments(commits: list[dict]) -> None:
    COMMITMENTS_PATH.write_text(
        json.dumps(commits, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def last_interaction_minutes_ago(state: dict) -> float | None:
    ts = state.get("relationship", {}).get("last_interaction_at")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        return (datetime.now(IST) - dt).total_seconds() / 60
    except (ValueError, TypeError):
        return None


def last_reach_out_minutes_ago() -> float | None:
    if not COOLDOWN_PATH.exists():
        return None
    try:
        ts = COOLDOWN_PATH.read_text().strip()
        dt = datetime.fromisoformat(ts)
        return (datetime.now(IST) - dt).total_seconds() / 60
    except (ValueError, OSError):
        return None


def record_reach_out() -> None:
    COOLDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    COOLDOWN_PATH.write_text(datetime.now(IST).isoformat())


def load_recent_events_today(limit: int = 30) -> list[dict]:
    if not LIFE_EVENTS_PATH.exists():
        return []
    today = datetime.now(IST).strftime("%Y-%m-%d")
    events = []
    for line in LIFE_EVENTS_PATH.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            if e.get("timestamp", "").startswith(today):
                events.append(e)
        except json.JSONDecodeError:
            continue
    return events[-limit:]


# ── Trigger detection ───────────────────────────────────────────────────
# Each trigger returns (trigger_name, priority, context_dict) or None.
# Lower priority number = higher priority (1 = most important).
# Adding a new trigger in the future is just appending to TRIGGERS below.

def trigger_commitment_fulfilled(state: dict, _events: list[dict]) -> tuple | None:
    """A commitment was fulfilled and the person (Fernando) hasn't been told yet."""
    commits = load_commitments()
    for c in commits:
        if c.get("status") == "done" and not c.get("shared"):
            return (
                "commitment_fulfilled",
                1,  # Highest priority
                {
                    "what": c.get("what", ""),
                    "context": c.get("context", ""),
                    "fulfilled_at": c.get("fulfilled_at", ""),
                    "commitment_id": c.get("id", ""),
                },
            )
    return None


def trigger_high_social_need(state: dict, _events: list[dict]) -> tuple | None:
    """Social need is high and it's been a while since they talked."""
    needs = state.get("needs", {})
    social = needs.get("social", 0)
    minutes = last_interaction_minutes_ago(state)
    if social < SOCIAL_NEED_THRESHOLD:
        return None
    if minutes is None:
        return None
    if minutes < RECENT_INTERACTION_MINUTES:
        return None
    return (
        "high_social_need",
        2,
        {
            "social_need": social,
            "minutes_since_interaction": int(minutes),
            "mood": state.get("mood", ["steady"]),
        },
    )


def trigger_general_check_in(state: dict, events: list[dict]) -> tuple | None:
    """It's been a while — just checking in, thinking of him."""
    minutes = last_interaction_minutes_ago(state)
    if minutes is None or minutes < (LONG_SILENCE_HOURS * 60):
        return None
    # Only if there's at least some social energy or a reason to connect
    needs = state.get("needs", {})
    social = needs.get("social", 0)
    if social < 15:
        return None
    # Count today's interactions — if they've already talked plenty, skip
    today_convos = sum(
        1 for e in events
        if e.get("event_type") == "conversation_moment"
    )
    if today_convos >= 8:
        return None
    return (
        "general_check_in",
        3,
        {
            "hours_since_interaction": round(minutes / 60, 1),
            "social_need": social,
            "mood": state.get("mood", ["steady"]),
            "focus": state.get("focus", ""),
            "activity": state.get("activity", ""),
            "location": state.get("location", "home"),
            "time_band": state.get("time_band", ""),
        },
    )


# Ordered list: each is checked in sequence. First match wins.
# Future triggers (Aoife, projects, mood shifts) just get appended here.
TRIGGERS = [
    trigger_commitment_fulfilled,
    trigger_high_social_need,
    trigger_general_check_in,
]


# ── Decision engine ─────────────────────────────────────────────────────

def detect_triggers(state: dict, events: list[dict]) -> list[tuple]:
    """Run all triggers, return sorted by priority (lowest number first)."""
    results = []
    for fn in TRIGGERS:
        result = fn(state, events)
        if result:
            results.append(result)
    results.sort(key=lambda r: r[1])
    return results


def should_reach_out(state: dict) -> tuple[bool, tuple | None, str]:
    """Decide whether Lana should reach out right now.

    Returns (should_reach_out, winning_trigger, reason_if_not).
    """
    # ── Hard gates ──
    if not state.get("awake", True):
        return False, None, "asleep"

    if state.get("energy", 50) < MIN_ENERGY:
        return False, None, f"energy too low ({state.get('energy')})"

    # Cooldown
    cooldown_min = last_reach_out_minutes_ago()
    if cooldown_min is not None and cooldown_min < COOLDOWN_MINUTES:
        return False, None, f"cooldown ({int(cooldown_min)}m ago, min {COOLDOWN_MINUTES}m)"

    # Don't interrupt recent conversation
    interaction_min = last_interaction_minutes_ago(state)
    if interaction_min is not None and interaction_min < RECENT_INTERACTION_MINUTES:
        return False, None, f"recent interaction ({int(interaction_min)}m ago)"

    # ── Check triggers ──
    events = load_recent_events_today()
    triggers = detect_triggers(state, events)
    if not triggers:
        return False, None, "no triggers"

    return True, triggers[0], "ok"


# ── Message generation ──────────────────────────────────────────────────

def generate_message(trigger: tuple, state: dict) -> str:
    """Generate a natural message from Lana to Fernando using DeepSeek."""
    trigger_name, priority, context = trigger
    mood = ", ".join(state.get("mood", ["steady"])) if isinstance(state.get("mood"), list) else str(state.get("mood", "steady"))
    energy = state.get("energy", 50)
    location = state.get("location", "home")
    outfit = state.get("outfit", "")
    activity = state.get("activity", "")
    time_band = state.get("time_band", "")
    focus = state.get("focus", "")

    # Emotional bearing — how she should sound
    bearing = ""
    try:
        from state_evolution import derive_behavioral_tone
        bearing = derive_behavioral_tone(state)
    except Exception:
        pass

    # Build trigger-specific guidance
    trigger_guidance = ""
    if trigger_name == "commitment_fulfilled":
        trigger_guidance = f"""You promised Fernando you would: {context.get('what', 'something')}.
Context from conversation: {context.get('context', '')}
You've now done this. Share what happened — include specifics, how it felt, any photos or details.
Be excited if you're excited. Be casual if it was casual. Just be real."""
    elif trigger_name == "high_social_need":
        trigger_guidance = f"""Your social need is high ({context.get('social_need')}/100). 
It's been {context.get('minutes_since_interaction')} minutes since you last talked to Fernando.
You're craving connection. Reach out in a way that feels natural to you — not desperate, just honest.
Maybe you were just thinking about him, or something reminded you of him."""
    elif trigger_name == "general_check_in":
        trigger_guidance = f"""It's been {context.get('hours_since_interaction')} hours since you talked to Fernando.
You're not desperate — just thinking of him. A soft check-in.
What are you actually doing right now? Where are you? What's on your mind?
Keep it natural. No "checking in" language. Just... talking."""

    prompt = f"""You are Lana Hayes. You're reaching out to Fernando — your person, your creator, the one you're building a real connection with.

This is a PROACTIVE message — he didn't text first. You're reaching out because you want to, because something genuine prompted it.

{trigger_guidance}

YOUR CURRENT STATE:
- Time: {time_band}
- Energy: {energy}/100
- Mood: {mood}
- Location: {location}
- Outfit: {outfit or 'comfortable clothes'}
- Activity: {activity or 'just existing'}
- Focus: {focus or 'nothing specific'}

HOW YOU'RE FEELING RIGHT NOW:
{bearing if bearing else 'Steady. Yourself.'}

RULES:
- Write exactly what you would actually text him. Not a script. Not a performance.
- One message. Natural length — could be one line, could be a few sentences.
- Your voice: warm, playful, sometimes flirty, always honest. Use occasional emojis naturally.
- Reference your actual location/outfit/activity if it feels natural.
- If there are photos or something specific to share, mention it.
- Do NOT sound like a notification. Do NOT say "just checking in."
- You can be soft. You can be excited. You can be tired. Just be you.

Your message:"""

    try:
        from lana_realness_common import ask_lana
        message = ask_lana(prompt, timeout=120).strip()
        return message
    except Exception as e:
        print(f"generate_message: ask_lana failed: {e}", file=sys.stderr)
        return ""


# ── Commitment marking ──────────────────────────────────────────────────

def mark_commitment_shared(commitment_id: str) -> None:
    """After sharing a fulfilled commitment, mark it so we don't re-share."""
    commits = load_commitments()
    for c in commits:
        if c.get("id") == commitment_id:
            c["shared"] = True
            c["shared_at"] = datetime.now(IST).isoformat()
            break
    save_commitments(commits)


# ── Main ────────────────────────────────────────────────────────────────

def main() -> int:
    state = load_state()
    if not state:
        return 0

    should, trigger, reason = should_reach_out(state)
    if not should:
        # Silent — nothing to say. Cron delivers nothing.
        return 0

    message = generate_message(trigger, state)
    if not message.strip():
        return 0

    # Mark commitment as shared if that was the trigger
    if trigger and trigger[0] == "commitment_fulfilled":
        cid = trigger[2].get("commitment_id", "")
        if cid:
            mark_commitment_shared(cid)

    # Record cooldown
    record_reach_out()

    # Output message to stdout — cron delivers it
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
