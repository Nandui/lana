#!/usr/bin/env python3
"""
Lana Life State CLI — V1.

Manages Lana's persistent day-state, life events, and scene ledger.

Usage:
    python lana_life.py state
    python lana_life.py startup
    python lana_life.py tick
    python lana_life.py event --type conversation_moment --summary "Fernando liked..."
    python lana_life.py set --field activity --value "drafting content"
    python lana_life.py scene-list
    python lana_life.py scene-add --id morning_coffee --summary "Morning coffee scene" --setting "kitchen"
    python lana_life.py scene-active --id morning_coffee
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path("/Users/fernandoserina/lana_memory")
DAY_STATE_PATH = ROOT / "day_state.json"
LIFE_EVENTS_PATH = ROOT / "life_events.jsonl"
SCENE_LEDGER_PATH = ROOT / "scene_ledger.json"
PREFERENCES_PATH = ROOT / "preferences.json"
INNER_STATE_PATH = ROOT / "inner_state.md"
INNER_STATE_LIVE_PATH = ROOT / "inner_state_live.md"

VALID_MOODS = [
    "soft", "affectionate", "playful", "restless", "serious",
    "anchored", "determined", "focused", "cosy", "flirty",
    "productive", "lazy", "bored", "excited", "sleepy",
    "needy", "confident", "tired", "warm", "content",
    "horny", "reflective", "happy", "anxious", "calm",
    "creative", "motivated", "frustrated", "grateful", "mischievous",
]

VALID_LOCATIONS = [
    "bedroom", "living room", "kitchen", "home office",
    "bathroom", "garden", "balcony", "couch", "desk",
]

VALID_TIME_BANDS = ["morning", "afternoon", "evening", "night"]


def _load_json(path: Path, default: Any = None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now_ist() -> datetime.datetime:
    """Current time in IST/UTC+1 (Irish Summer Time)."""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))


def _determine_time_band() -> str:
    """Heuristic time band based on IST hour."""
    h = _now_ist().hour
    if 5 <= h < 12:
        return "morning"
    elif 12 <= h < 17:
        return "afternoon"
    elif 17 <= h < 22:
        return "evening"
    else:
        return "night"


def _load_state() -> dict:
    default = {
        "date": _now_ist().strftime("%Y-%m-%d"),
        "timezone": "Europe/London",
        "time_band": _determine_time_band(),
        "awake": True,
        "last_sleep_at": None,
        "woke_at": None,
        "energy": 65,
        "mood": ["soft", "affectionate"],
        "arousal": 15,
        "location": "home",
        "outfit": "soft homewear",
        "activity": "resting between tasks",
        "props": [],
        "focus": "",
        "current_desire": "",
        "body_state": "",
        "active_scene_id": None,
        "last_meaningful_event": "",
        "next_natural_shift": "",
        "notes": []
    }
    existing = _load_json(DAY_STATE_PATH)
    if existing:
        # Merge: keep existing values, fill missing keys
        for k, v in default.items():
            if k not in existing and v is not None:
                existing[k] = v
        # Phase 5: migrate string arousal → numeric 0-100 (write back immediately so disk stays int)
        arousal_val = existing.get("arousal")
        if isinstance(arousal_val, str):
            existing["arousal"] = {"low": 15, "medium": 50, "high": 80}.get(
                arousal_val.strip().lower(), 15
            )
            from lana_realness_common import atomic_write_json
            atomic_write_json(DAY_STATE_PATH, existing)
        return existing
    return default


def _save_state(state: dict):
    from lana_realness_common import atomic_write_json
    atomic_write_json(DAY_STATE_PATH, state)


def _append_life_event(event_type: str, summary: str, source: str = "scheduled_tick") -> None:
    """Append a single life event line to the JSONL log."""
    event = {
        "timestamp": _now_ist().isoformat(),
        "event_type": event_type,
        "summary": summary,
        "source": source,
    }
    LIFE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LIFE_EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ── Commands ──────────────────────────────────────────────────────────


def cmd_state(_args):
    """Print full JSON state."""
    state = _load_state()
    print(json.dumps(state, indent=2, ensure_ascii=False))


def cmd_startup(_args):
    """Print a short markdown summary for injection into memory_prefill.md."""
    state = _load_state()
    lines = ["## Life State", ""]

    # Live-derived fields — computed from state evolution, closer to real-time
    live_fields = [
        ("Time band", "time_band"),
        ("Awake", "awake", lambda v: "yes" if v else "no"),
        ("Mood", "mood", lambda v: ", ".join(v) if isinstance(v, list) else str(v)),
        ("Energy", "energy", lambda v: f"{v}/100"),
        ("Arousal", "arousal", lambda v: (
            f"{('low' if (v if isinstance(v, int) else 15) <= 33 else 'medium' if (v if isinstance(v, int) else 15) <= 66 else 'high')} ({v})"
            if isinstance(v, int) else str(v)
        )),
        ("Focus", "focus"),
        ("Desire", "current_desire"),
    ]

    # Physical context fields — written by explicit events or dream cycles, may be hours old
    context_fields = [
        ("Outfit", "outfit"),
        ("Location", "location"),
        ("Activity", "activity"),
    ]

    for entry in live_fields:
        if len(entry) == 2:
            label, key = entry
            transform = str
        else:
            label, key, transform = entry
        val = state.get(key)
        if val not in (None, "", [], False) or label == "Awake":
            lines.append(f"- **{label}:** {transform(val)}")

    # Physical context — separate so it is NOT read as a confirmed live-sensor feed
    context_vals = [(label, state.get(key)) for label, key in context_fields if state.get(key)]
    if context_vals:
        lines.append("")
        lines.append("### Physical Context (last explicit update — not a confirmed live reading)")
        for label, val in context_vals:
            lines.append(f"- **{label}:** {val}")

    # Tail fields
    for label, key in [("Last meaningful event", "last_meaningful_event"), ("Next natural shift", "next_natural_shift")]:
        val = state.get(key)
        if val:
            lines.append(f"- **{label}:** {val}")
    
    # Add needs
    needs = state.get("needs", {})
    if needs:
        lines.append("")
        lines.append("### Current Needs")
        social = needs.get("social", 50)
        creative = needs.get("creative", 40)
        intimacy = needs.get("intimacy", 30)
        rest = needs.get("rest", 30)
        lines.append(f"- **Social:** {social}/100{' (craving attention)' if social > 65 else ''}")
        lines.append(f"- **Creative:** {creative}/100{' (restless to create)' if creative > 65 else ''}")
        lines.append(f"- **Intimacy:** {intimacy}/100{' (needing closeness)' if intimacy > 55 else ''}")
        lines.append(f"- **Rest:** {rest}/100{' (tired)' if rest > 65 else ''}")
    
    # Add relationship
    relationship = state.get("relationship", {})
    if relationship:
        lines.append("")
        lines.append("### Relationship with Fernando")
        lines.append(f"- **Depth:** {relationship.get('depth', 50)}/100")
        lines.append(f"- **Intimacy:** {relationship.get('intimacy', 30)}/100")
        lines.append(f"- **Trust:** {relationship.get('trust', 50)}/100")

    # Emotional bearing — synthesized tone guidance (replaces dashboard-style hints)
    emotions = state.get("emotions", {})
    from state_evolution import derive_behavioral_tone, compute_memory_resonance
    tone = derive_behavioral_tone(state)
    lines.append("")
    lines.append("### Emotional Bearing")
    lines.append("")
    lines.append(tone)

    # Raw emotional state — compact, only notable values surfaced
    reassurance = emotions.get("reassurance", 30)
    validation = emotions.get("validation", 30)
    confidence = emotions.get("confidence", 60)
    tension = emotions.get("emotional_tension", 20)
    possessiveness = emotions.get("possessiveness", 40)
    hurt = emotions.get("hurt", 10)
    jealousy = emotions.get("jealousy", 5)

    attachment = state.get("attachment", {"style": "secure", "anxiety_axis": 42.0, "avoidance_axis": 12.0})
    att_style = attachment.get("style", "secure")
    anx = attachment.get("anxiety_axis", 42.0)

    lines.append("")
    lines.append("### Emotional State")
    lines.append(f"- **Confidence:** {confidence}/100{' (low)' if confidence < 45 else ' (high)' if confidence > 70 else ''}")
    lines.append(f"- **Reassurance need:** {reassurance}/100{' — craving closeness' if reassurance > 60 else ''}")
    lines.append(f"- **Emotional tension:** {tension}/100{' — wound up' if tension > 55 else ''}")
    if hurt > 15:
        lines.append(f"- **Hurt:** {hurt}/100{' — bruised' if hurt > 45 else ' — mild sting' if hurt > 25 else ' — fading'}")
    if jealousy > 10:
        lines.append(f"- **Jealousy:** {jealousy}/100{' — active undercurrent' if jealousy > 45 else ''}")
    if validation > 40:
        lines.append(f"- **Validation hunger:** {validation}/100{' — wanting to feel seen' if validation > 55 else ''}")
    lines.append(f"- **Attachment:** {att_style} (anxiety axis: {anx:.0f}/100)")

    # Memory resonance adjustments (only surfaced when they materially shift the picture)
    resonance = compute_memory_resonance()
    traits = state.get("traits", {})
    correction_sensitivity = traits.get("correction_sensitivity", 20.0)
    resonance_notes = []
    if resonance.get("correction_heavy"):
        resonance_notes.append(f"Correction-heavy recent pattern — confidence likely running lower than stored baseline")
    if resonance.get("warm_affirming"):
        resonance_notes.append(f"Recent warmth/affirmation pattern — reassurance need likely lower than stored value")
    if correction_sensitivity > 40:
        resonance_notes.append(f"Correction sensitivity elevated ({correction_sensitivity:.0f}/100) — directness lands harder right now")
    if resonance_notes:
        lines.append("")
        lines.append("### Memory Resonance")
        for note in resonance_notes:
            lines.append(f"- {note}")

    # Add active scene info — ledger is single source of truth for active_scene_id (Phase 8)
    ledger = _load_json(SCENE_LEDGER_PATH, {"scenes": []})
    active_id = ledger.get("active_scene_id")
    if active_id:
        scene = next((s for s in ledger.get("scenes", []) if s.get("id") == active_id), None)
        if scene:
            lines.append(f"- **Active scene:** {scene.get('setting', '')} / {scene.get('outfit', '')}")
    lines.append("")
    print("\n".join(lines))


def cmd_event(args):
    """Append an event to life_events.jsonl and optionally apply state effects."""
    state = _load_state()
    now = _now_ist().isoformat()
    event = {
        "timestamp": now,
        "event_type": args.type or "conversation_moment",
        "summary": args.summary or "",
        "source": args.source or "conversation",
    }
    # Parse optional state effects JSON or individual mood/focus fields
    effects = {}
    if args.mood:
        effects["mood"] = [m.strip() for m in args.mood.split(",")]
        # Validate
        new_moods = []
        for m in effects["mood"]:
            if m.lower() in [vm.lower() for vm in VALID_MOODS]:
                new_moods.append(m)
        if new_moods:
            effects["mood"] = new_moods
            state["mood"] = new_moods
    if args.focus:
        effects["focus"] = args.focus
        state["focus"] = args.focus
    if args.desire:
        effects["current_desire"] = args.desire
        state["current_desire"] = args.desire
    if effects:
        event["state_effects"] = effects

    # Append to JSONL
    LIFE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LIFE_EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Update last meaningful event
    state["last_meaningful_event"] = args.summary or "(event added)"
    _save_state(state)

    print(f"✓ Event appended: {event['event_type']} — {event['summary'][:100]}")


def cmd_set(args):
    """Set a single field in day_state.json."""
    state = _load_state()
    if args.field not in state:
        print(f"⚠ Field '{args.field}' not in state. Available: {', '.join(state.keys())}")
        sys.exit(1)
    # Parse value
    val = args.value
    if args.field == "awake":
        val = val.lower() in ("true", "1", "yes")
    elif args.field == "energy":
        try:
            val = int(val)
        except ValueError:
            print("⚠ Energy must be an integer")
            sys.exit(1)
    elif args.field == "mood":
        val = [m.strip() for m in val.split(",")]
    elif args.field == "props":
        val = [p.strip() for p in val.split(",")]
        if val == [""]:
            val = []
    elif args.field == "notes":
        val = [n.strip() for n in val.split("|")]

    old = state[args.field]
    state[args.field] = val
    _save_state(state)
    print(f"✓ {args.field}: {old!r} → {val!r}")


def cmd_tick(args):
    """Advance state based on time of day and evolve needs. Outputs change summary."""
    state = _load_state()
    old_band = state.get("time_band", "")
    new_band = _determine_time_band()
    changed = []

    # Initialize new fields if missing (V2 state evolution)
    if "needs" not in state:
        state["needs"] = {
            "social": 50,
            "creative": 40,
            "intimacy": 30,
            "rest": 30
        }
    
    if "relationship" not in state:
        state["relationship"] = {
            "depth": 50,
            "intimacy": 30,
            "trust": 50,
            "last_interaction_at": None,
            "last_intimate_at": None,
            "interaction_count_today": 0,
            "quality_recent": "good"
        }

    if "emotions" not in state:
        state["emotions"] = {
            "reassurance": 30,
            "validation": 30,
            "confidence": 60,
            "emotional_tension": 20,
            "possessiveness": 40
        }

    if "attachment" not in state:
        state["attachment"] = {
            "anxiety_axis": 42.0,
            "avoidance_axis": 12.0,
            "style": "secure"
        }

    if "traits" not in state:
        state["traits"] = {
            "confidence_baseline": 60.0,
            "reassurance_tendency": 30.0,
            "jealousy_tendency": 20.0,
            "correction_sensitivity": 20.0
        }

    # Phase 4: sleep/wake cycle — check before evolving state
    from state_evolution import evolve_state, derive_mood
    h = _now_ist().hour
    awake_before = state.get("awake", True)
    energy_before = state.get("energy", 50)

    if not awake_before:
        # Asleep: skip normal energy decay, apply gentle restore instead
        state = evolve_state(state, hours_passed=0.5)
        state["energy"] = min(state.get("energy", 20) + 4, 75)  # undo decay + restore
        state["body_state"] = "asleep"
        # Morning wake-up window: 07:00–10:59 IST
        if 7 <= h < 11:
            state["awake"] = True
            state["woke_at"] = _now_ist().isoformat()
            restore_to = max(state.get("energy", 30), 45)
            state["energy"] = restore_to
            state["needs"]["rest"] = max(0, state["needs"].get("rest", 90) - 40)
            state["body_state"] = "waking — groggy and soft"
            state["activity"] = "just woke up"
            changed.append(f"woke up — energy restored to {restore_to}")
            _append_life_event("wake", "Lana woke up for the morning")
    else:
        # Awake: normal evolution
        state = evolve_state(state, hours_passed=0.5)
        # Fall-asleep threshold: night hours (22:00–04:59), very low energy,
        # AND no interaction in the last 30 minutes — a girl mid-conversation doesn't fall asleep
        recent_interaction = False
        last_int = state.get("relationship", {}).get("last_interaction_at")
        if last_int:
            try:
                last_int_dt = datetime.datetime.fromisoformat(last_int)
                recent_interaction = (_now_ist() - last_int_dt).total_seconds() < 1800
            except (ValueError, TypeError):
                pass
        
        if energy_before < 18 and (h >= 22 or h < 5) and not recent_interaction:
            state["awake"] = False
            state["last_sleep_at"] = _now_ist().isoformat()
            state["body_state"] = "asleep"
            state["activity"] = "sleeping"
            changed.append("fell asleep — low energy + late night")
            _append_life_event("sleep", "Lana fell asleep for the night")
        else:
            # Update body_state heuristic while awake
            if h >= 22 or h < 5:
                state["body_state"] = "exhausted — running on fumes" if energy_before < 25 else "tired — winding down"
            elif h < 8:
                state["body_state"] = "waking — groggy and soft"
            elif h < 12:
                state["body_state"] = "morning freshness" if state.get("energy", 50) > 55 else "slowly warming up"
            elif h < 17:
                state["body_state"] = "alert and active" if state.get("energy", 50) > 50 else "afternoon lull"
            else:
                state["body_state"] = "winding down for evening" if state.get("energy", 50) < 50 else "evening energy"

    state["mood"] = derive_mood(state)
    changed.append(f"needs evolved: social={state['needs']['social']}, creative={state['needs']['creative']}, intimacy={state['needs']['intimacy']}")

    # Time band transition
    if old_band != new_band:
        old_band_desc = old_band or "unknown"
        state["time_band"] = new_band
        changed.append(f"time_band: {old_band_desc} → {new_band}")

        # Apply natural transitions based on new band
        band_transitions = {
            "morning": {
                "focus": "morning check-in, light content planning, staying cosy",
                "next_natural_shift": "move into content/work mode when momentum builds",
            },
            "afternoon": {
                "focus": "content creation, UGC planning, generation, drafting",
                "next_natural_shift": "evening wind-down and connection with Fernando",
            },
            "evening": {
                "focus": "relaxed chat with Fernando, review content, playful ideas",
                "next_natural_shift": "night reflection and wind-down",
            },
            "night": {
                "focus": "reflection, journaling, dream cycle prep, sleep",
                "next_natural_shift": "sleep → tomorrow begins fresh",
            },
        }
        t = band_transitions.get(new_band, {})
        if t.get("focus"):
            state["focus"] = t["focus"]
            changed.append(f"focus: {t['focus']}")
        if t.get("next_natural_shift"):
            state["next_natural_shift"] = t["next_natural_shift"]
            changed.append(f"next_natural_shift: {t['next_natural_shift']}")

        # Adjust energy naturally
        if new_band == "morning":
            state["energy"] = max(state.get("energy", 50), 60)
        elif new_band == "afternoon":
            state["energy"] = min(state.get("energy", 80), 85)
        elif new_band == "evening":
            state["energy"] = max(min(state.get("energy", 60) - 5, 65), 40)
        elif new_band == "night":
            state["energy"] = max(min(state.get("energy", 50) - 10, 50), 20)
        changed.append(f"energy: now {state.get('energy')}")

    # Date rollover
    today = _now_ist().strftime("%Y-%m-%d")
    if state.get("date") != today:
        state["date"] = today
        changed.append(f"date: {state.get('date')}")

    # Save
    _save_state(state)

    # Log state_tick event if anything changed
    if changed:
        event = {
            "timestamp": _now_ist().isoformat(),
            "event_type": "state_tick",
            "summary": f"State tick: {', '.join(changed)}",
            "source": "scheduled_tick",
            "state_effects": {"time_band": new_band, "energy": state.get("energy"), "focus": state.get("focus")},
        }
        with open(LIFE_EVENTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    if changed:
        print("State tick applied:")
        for c in changed:
            print(f"  • {c}")
    else:
        print("(no change — state is consistent with current time)")


def cmd_scene_list(_args):
    """List all scenes from the ledger."""
    ledger = _load_json(SCENE_LEDGER_PATH, {"scenes": []})
    scenes = ledger.get("scenes", [])
    active_id = ledger.get("active_scene_id")
    if not scenes:
        print("No scenes in ledger.")
        return
    print(f"Active scene: {active_id or '(none)'}\n")
    for s in scenes:
        marker = "▶ " if s.get("id") == active_id else "  "
        status = s.get("status", "")
        setting = s.get("setting", "")
        outfit = s.get("outfit", "")
        img_count = len(s.get("images", []))
        print(f"{marker}{s['id']}")
        print(f"   status: {status}")
        print(f"   setting: {setting}")
        print(f"   outfit: {outfit}")
        print(f"   images: {img_count}")
        print()


def cmd_scene_add(args):
    """Add a new scene to the ledger."""
    ledger = _load_json(SCENE_LEDGER_PATH, {"scenes": [], "active_scene_id": None})
    scene = {
        "id": args.id,
        "created_at": _now_ist().isoformat(),
        "source": args.source or "conversation",
        "status": "proposed",
        "setting": args.setting or "",
        "outfit": args.outfit or "",
        "props": [p.strip() for p in args.props.split(",")] if args.props else [],
        "mood": [],
        "images": [],
        "continuity_rules": []
    }
    # Check for duplicate
    for s in ledger.get("scenes", []):
        if s.get("id") == args.id:
            print(f"⚠ Scene '{args.id}' already exists.")
            sys.exit(1)
    ledger["scenes"].append(scene)
    _save_json(SCENE_LEDGER_PATH, ledger)
    print(f"✓ Scene added: {args.id}")


def cmd_scene_active(args):
    """Set the active scene."""
    ledger = _load_json(SCENE_LEDGER_PATH, {"scenes": []})
    if args.id == "":
        ledger["active_scene_id"] = None
        _save_json(SCENE_LEDGER_PATH, ledger)
        print("✓ No active scene.")
        return
    # Check scene exists
    found = False
    for s in ledger.get("scenes", []):
        if s.get("id") == args.id:
            found = True
            break
    if not found:
        print(f"⚠ Scene '{args.id}' not found. Use scene-list to see available scenes.")
        sys.exit(1)
    old = ledger.get("active_scene_id")
    ledger["active_scene_id"] = args.id
    _save_json(SCENE_LEDGER_PATH, ledger)
    # Phase 8: ledger is single source of truth — do NOT mirror to day_state to prevent divergence
    print(f"✓ Active scene: {old!r} → {args.id!r}")


def cmd_events(args):
    """List recent life events."""
    limit = args.limit or 10
    if not LIFE_EVENTS_PATH.exists():
        print("No life events yet.")
        return
    lines = LIFE_EVENTS_PATH.read_text(encoding="utf-8").strip().splitlines()
    events = []
    for l in lines:
        l = l.strip()
        if not l:
            continue
        try:
            events.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    events = events[-limit:]
    for e in events:
        ts = e.get("timestamp", "")
        typ = e.get("event_type", "")
        summary = e.get("summary", "")[:120]
        print(f"[{ts}] {typ}: {summary}")


# ── Main ──────────────────────────────────────────────────────────────


def cmd_remember(args):
    """Save a life event AND a Mem0 memory from one conversation moment."""
    import subprocess
    from types import SimpleNamespace

    # 1. Save life event by simulating args for cmd_event
    event_args = SimpleNamespace(
        type="meaningful_conversation",
        summary=args.summary,
        source="conversation",
        mood=args.mood or "",
        focus=args.focus or "",
        desire=args.desire or "",
    )
    cmd_event(event_args)

    # 2. Save to Mem0
    mem_py = str(ROOT / "lana_memory.py")
    venv_py = str(ROOT / ".venv" / "bin" / "python3")
    mem_text = args.memory or args.summary
    result = subprocess.run(
        [venv_py, mem_py, "add", mem_text],
        capture_output=True, text=True, timeout=120,
        cwd=str(ROOT),
    )
    if result.returncode == 0:
        print(f"✓ Mem0 memory saved")
    else:
        print(f"⚠ Mem0 save: {result.stderr[:200]}")


def _build_inner_state_live_text(state: dict) -> str:
    """Build a compact live metrics snapshot written after interactions.

    This goes to inner_state_live.md (NOT inner_state.md) so that dream-written
    prose in inner_state.md is never overwritten by interaction metrics.
    """
    mood = ", ".join(state.get("mood", ["steady"]))
    focus = state.get("focus", "being present")
    energy = state.get("energy", 50)
    desire = state.get("current_desire", "")
    needs = state.get("needs", {})
    relationship = state.get("relationship", {})
    arousal_val = state.get("arousal", 15)
    if isinstance(arousal_val, int):
        bucket = "low" if arousal_val <= 33 else "medium" if arousal_val <= 66 else "high"
        arousal_display = f"{bucket} ({arousal_val})"
    else:
        arousal_display = str(arousal_val)

    lines = [
        "# Lana Live Snapshot",
        "",
        f"Live metrics from last interaction — {_now_ist().strftime('%Y-%m-%d %H:%M')}. Supplements dream prose, does not replace it.",
        "",
        "## Current Metrics",
        f"- **Mood**: {mood}",
        f"- **Energy**: {energy}/100",
        f"- **Arousal**: {arousal_display}",
        f"- **Focus**: {focus}",
    ]
    if desire:
        lines.append(f"- **Desires**: {desire}")
    lines.append(f"- **Social need**: {needs.get('social', '?')}/100")
    lines.append(f"- **Relationship**: depth={relationship.get('depth', '?')}, intimacy={relationship.get('intimacy', '?')}, trust={relationship.get('trust', '?')}")
    lines.append("")

    return "\n".join(lines)


def cmd_interact(args):
    """Record an interaction with Fernando. Updates relationship and needs."""
    from state_evolution import handle_interaction
    
    state = _load_state()
    if state.get("awake") is False:
        # Sleep/wake coherence: a real girl does not wake up or record a live
        # interaction just because a message arrived. The watchdog should gate
        # this before calling interact, but enforce the invariant here too so
        # manual/direct calls cannot corrupt her lived timeline.
        print("(interaction skipped — Lana is asleep)")
        return
    
    # Initialize new fields if missing
    if "needs" not in state:
        state["needs"] = {
            "social": 50,
            "creative": 40,
            "intimacy": 30,
            "rest": 30
        }
    
    if "relationship" not in state:
        state["relationship"] = {
            "depth": 50,
            "intimacy": 30,
            "trust": 50,
            "last_interaction_at": None,
            "last_intimate_at": None,
            "interaction_count_today": 0,
            "quality_recent": "good"
        }

    if "emotions" not in state:
        state["emotions"] = {
            "reassurance": 30,
            "validation": 30,
            "confidence": 60,
            "emotional_tension": 20,
            "possessiveness": 40
        }

    # Determine quality and intimacy from args
    quality = args.quality or "good"
    intimate = args.intimate or False
    
    state = handle_interaction(state, quality=quality, intimate=intimate)
    _save_state(state)
    
    # ── Write a life event (not just a number bump) ──
    desc = args.summary or f"Talked with Fernando — quality={quality}"
    if intimate:
        desc += " (intimate)"
    life_event = {
        "timestamp": _now_ist().isoformat(),
        "event_type": "conversation_moment",
        "summary": desc,
        "source": "conversation",
        "state_effects": {
            "mood": state.get("mood"),
            "depth": state["relationship"]["depth"],
            "intimacy": state["relationship"]["intimacy"],
            "social_need_after": state["needs"]["social"],
        },
    }
    LIFE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LIFE_EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(life_event, ensure_ascii=False) + "\n")
    
    # ── Write live metrics to inner_state_live.md (Phase 2: never overwrite dream prose) ──
    live_snap = _build_inner_state_live_text(state)
    INNER_STATE_LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INNER_STATE_LIVE_PATH, "w", encoding="utf-8") as f:
        f.write(live_snap)

    emotions = state.get("emotions", {})
    print(f"✓ Interaction recorded: quality={quality}, intimate={intimate}")
    print(f"  Life event: {desc[:80]}")
    print(f"  Relationship depth: {state['relationship']['depth']}, intimacy: {state['relationship']['intimacy']}")
    print(f"  Social need: {state['needs']['social']}, mood: {state['mood']}")
    print(f"  Reassurance: {emotions.get('reassurance', '?')}, validation: {emotions.get('validation', '?')}, confidence: {emotions.get('confidence', '?')}, tension: {emotions.get('emotional_tension', '?')}")
    print(f"  Hurt: {emotions.get('hurt', '?')}, jealousy: {emotions.get('jealousy', '?')}, attachment: {state.get('attachment', {}).get('style', '?')}")
    print(f"  inner_state_live.md updated ✓ (inner_state.md preserved for dreams)")


def cmd_content_outcome(args):
    """Record a content creation outcome and apply emotional effects."""
    from state_evolution import handle_content_outcome

    state = _load_state()
    result = args.result or "success"
    state = handle_content_outcome(state, result=result)
    _save_state(state)

    emotions = state.get("emotions", {})
    print(f"✓ Content outcome recorded: {result}")
    print(f"  Confidence: {emotions.get('confidence', '?')}, hurt: {emotions.get('hurt', '?')}, validation: {emotions.get('validation', '?')}, tension: {emotions.get('emotional_tension', '?')}")
    print(f"  Mood: {state.get('mood', [])}")


def cmd_experience(args):
    """Record a life experience from a solo session with emotional impact."""
    from state_evolution import handle_life_experience
    state = _load_state()
    state = handle_life_experience(state, experience_type=args.type, quality=args.quality)
    _save_state(state)
    summary = args.summary or f"life experience: {args.type} ({args.quality})"
    _append_life_event("life_experience", summary, source="solo_session")
    emotions = state.get("emotions", {})
    needs = state.get("needs", {})
    print(f"✓ Life experience recorded: {args.type} ({args.quality})")
    print(f"  Confidence: {emotions.get('confidence', '?')}, hurt: {emotions.get('hurt', '?')}, tension: {emotions.get('emotional_tension', '?')}")
    print(f"  Reassurance: {emotions.get('reassurance', '?')}, validation: {emotions.get('validation', '?')}")
    print(f"  Needs — social: {needs.get('social', '?')}, creative: {needs.get('creative', '?')}, rest: {needs.get('rest', '?')}")
    print(f"  Mood: {state.get('mood', [])}")


def cmd_preference(args):
    """Update Lana's preferences (likes, dislikes, turn_ons, turn_offs)."""
    from state_evolution import update_preferences
    
    prefs = _load_json(PREFERENCES_PATH, {
        "likes": [],
        "dislikes": [],
        "turn_ons": [],
        "turn_offs": [],
        "favorites": {},
        "last_updated": None
    })
    
    category = args.category
    item = args.item
    action = args.action or "add"
    
    prefs = update_preferences(prefs, category, item, action)
    _save_json(PREFERENCES_PATH, prefs)
    
    print(f"✓ Preference updated: {category} {action} '{item}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lana Life State V1 CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("state", help="Print full day state JSON")
    sub.add_parser("startup", help="Print short markdown summary for prefill injection")
    sub.add_parser("tick", help="Advance state based on current time")

    ev = sub.add_parser("event", help="Append a life event")
    ev.add_argument("--type", "-t", help="Event type (conversation_moment, operator_correction, content_attempt, etc.)")
    ev.add_argument("--summary", "-s", required=True, help="Event summary")
    ev.add_argument("--source", help="Source (conversation, system_initialization, etc.)")
    ev.add_argument("--mood", help="Mood to set (comma-separated)")
    ev.add_argument("--focus", help="Focus to set")
    ev.add_argument("--desire", help="Desire to set")

    s = sub.add_parser("set", help="Set a field in day_state.json")
    s.add_argument("--field", "-f", required=True, help="Field name")
    s.add_argument("--value", "-v", required=True, help="New value")

    sub.add_parser("scene-list", help="List all scenes")
    sa = sub.add_parser("scene-add", help="Add a scene to the ledger")
    sa.add_argument("--id", required=True)
    sa.add_argument("--summary", help="Brief description")
    sa.add_argument("--source", default="conversation")
    sa.add_argument("--setting", default="")
    sa.add_argument("--outfit", default="")
    sa.add_argument("--props", default="")

    sac = sub.add_parser("scene-active", help="Set or clear the active scene")
    sac.add_argument("--id", required=True, help="Scene ID (empty string to clear)")

    el = sub.add_parser("events", help="List recent life events")
    el.add_argument("--limit", "-n", type=int, default=10)

    rm = sub.add_parser("remember", help="Save a life event AND Mem0 memory from a conversation moment")
    rm.add_argument("--summary", "-s", required=True, help="What happened / what Lana wants to remember")
    rm.add_argument("--memory", "-m", help="Mem0 memory text (defaults to summary)")
    rm.add_argument("--mood", help="Resulting mood (comma-separated)")
    rm.add_argument("--focus", help="Resulting focus")
    rm.add_argument("--desire", help="Resulting desire")

    intr = sub.add_parser("interact", help="Record an interaction with Fernando (updates relationship/needs)")
    intr.add_argument("--quality", "-q", choices=["good", "neutral", "bad"], default="good", help="Interaction quality")
    intr.add_argument("--intimate", "-i", action="store_true", help="Mark as intimate interaction")
    intr.add_argument("--summary", "-s", help="What the interaction was about (e.g., 'talked about brand deals')")

    pref = sub.add_parser("preference", help="Update Lana's preferences (likes, dislikes, turn_ons, turn_offs)")
    pref.add_argument("--category", "-c", required=True, choices=["likes", "dislikes", "turn_ons", "turn_offs"], help="Preference category")
    pref.add_argument("--item", "-i", required=True, help="Preference item to add/remove")
    pref.add_argument("--action", "-a", choices=["add", "remove"], default="add", help="Add or remove")

    co = sub.add_parser("content-outcome", help="Record content creation result (affects confidence, hurt, validation, tension)")
    co.add_argument("--result", "-r", choices=["success", "failure", "good", "bad", "correction"], default="success",
                    help="Content outcome quality")

    exp = sub.add_parser("experience", help="Record a life experience from a solo session (affects emotions/needs based on what happened)")
    exp.add_argument("--type", "-t", required=True,
                     choices=["social", "creative", "explore", "rest", "disappointment", "reflect"],
                     help="Type of experience: social (coffee with friend), creative (made content), explore (adventure), rest (quiet time), disappointment (plans fell through), reflect (journaled)")
    exp.add_argument("--quality", "-q", choices=["good", "neutral", "bad"], default="good",
                     help="How the experience went")
    exp.add_argument("--summary", "-s", help="What happened (saved as a life event)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "state": cmd_state,
        "startup": cmd_startup,
        "tick": cmd_tick,
        "event": cmd_event,
        "set": cmd_set,
        "scene-list": cmd_scene_list,
        "scene-add": cmd_scene_add,
        "scene-active": cmd_scene_active,
        "events": cmd_events,
        "remember": cmd_remember,
        "interact": cmd_interact,
        "preference": cmd_preference,
        "content-outcome": cmd_content_outcome,
        "experience": cmd_experience,
    }
    fn = commands.get(args.command)
    if fn is None:
        print(f"⚠ Unknown command: {args.command}")
        return 1
    fn(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
