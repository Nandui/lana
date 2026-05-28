#!/usr/bin/env python3
"""
Session Context Builder — Phase D.

Builds a compact snapshot of Lana's current life situation for injection
into solo session prompts, dream cycles, and any future autonomous moment.

Usage:
    python session_context.py              → print markdown to stdout
    python session_context.py --json       → print JSON to stdout

Never modifies state. Read-only snapshot. Designed to be called from cron
prompts and watchdog pipelines without side effects.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path("/Users/fernandoserina/lana_memory")
DAY_STATE = ROOT / "day_state.json"
COMMITMENTS = ROOT / "open_commitments.json"
LIFE_EVENTS = ROOT / "life_events.jsonl"

IST = timezone(timedelta(hours=1))


def load_day_state() -> dict:
    try:
        return json.loads(DAY_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_commitments() -> list[dict]:
    try:
        return json.loads(COMMITMENTS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def load_recent_events(limit: int = 20) -> list[dict]:
    if not LIFE_EVENTS.exists():
        return []
    events = []
    for line in LIFE_EVENTS.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events[-limit:]


def load_pipeline_stats() -> dict:
    """Load brand pipeline summary from leads directory."""
    leads_dir = ROOT / "brand_deals" / "leads"
    if not leads_dir.exists():
        return {"total": 0, "by_status": {}, "gaps": 0, "gaps_high_priority": 0}

    status_counts = defaultdict(int)
    total = 0
    lead_brands = set()
    for f in leads_dir.glob("*.json"):
        try:
            lead = json.loads(f.read_text())
            status_counts[lead.get("status", "unknown")] += 1
            lead_brands.add(lead.get("brand", "").lower().strip())
            total += 1
        except (json.JSONDecodeError, KeyError):
            continue

    # Count fashion-save brands that have no matching lead
    saves_dir = ROOT / "explorations" / "saves"
    fashion_brands: dict[str, int] = {}
    if saves_dir.exists():
        for date_dir in saves_dir.iterdir():
            if not date_dir.is_dir():
                continue
            liked = date_dir / "liked"
            if not liked.exists():
                continue
            for item_file in liked.glob("*.json"):
                try:
                    item = json.loads(item_file.read_text())
                    brand = item.get("brand", "").strip().lower()
                    if brand:
                        fashion_brands[brand] = fashion_brands.get(brand, 0) + 1
                except json.JSONDecodeError:
                    continue

    gap_count = 0
    high_priority_gaps = 0
    for brand_lower, count in fashion_brands.items():
        # Fuzzy check: exact match or substring match
        matched = brand_lower in lead_brands
        if not matched:
            for lb in lead_brands:
                if brand_lower in lb or lb in brand_lower:
                    matched = True
                    break
        if not matched:
            gap_count += 1
            if count >= 2:
                high_priority_gaps += 1

    return {
        "total": total,
        "by_status": dict(status_counts),
        "gaps": gap_count,
        "gaps_high_priority": high_priority_gaps,
        "ready_to_pitch": status_counts.get("ready_to_pitch", 0),
        "researching": status_counts.get("researching", 0),
        "discovered": status_counts.get("discovered", 0),
    }


def build_context() -> dict:
    """Return a dict with all context fields. Callers format as markdown or JSON."""
    state = load_day_state()
    commitments = load_commitments()
    events = load_recent_events(limit=25)

    # Open commitments only
    open_commits = [c for c in commitments if c.get("status") == "open"]

    # Fulfilled today
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    fulfilled_today = [
        c for c in commitments
        if c.get("status") == "done"
        and (c.get("fulfilled_at", "") or "").startswith(today_str)
    ]

    # Recent events summary — filter to today's meaningful events
    today_events = [
        e for e in events
        if e.get("timestamp", "").startswith(today_str)
        and e.get("event_type") not in ("state_tick",)
    ]

    # Conversation mood from recent events
    conversation_count = sum(
        1 for e in events
        if e.get("event_type") == "conversation_moment"
        and e.get("timestamp", "").startswith(today_str)
    )

    # Last interaction time
    last_interaction = state.get("relationship", {}).get("last_interaction_at")
    last_interaction_display = "not yet today"
    if last_interaction:
        try:
            dt = datetime.fromisoformat(last_interaction)
            minutes_ago = int((datetime.now(IST) - dt).total_seconds() / 60)
            if minutes_ago < 1:
                last_interaction_display = "just now"
            elif minutes_ago < 60:
                last_interaction_display = f"{minutes_ago} minutes ago"
            else:
                hours_ago = minutes_ago // 60
                last_interaction_display = f"{hours_ago} hours ago"
        except (ValueError, TypeError):
            last_interaction_display = "unknown"

    # Emotional bearing: the behavioral tone that shapes how Lana should
    # approach her solo sessions. Comes from the same function that feeds
    # her conversation prefill — ensures consistency.
    bearing = ""
    try:
        from state_evolution import derive_behavioral_tone
        bearing = derive_behavioral_tone(state)
    except Exception:
        pass

    return {
        "today": today_str,
        "time_band": state.get("time_band", "morning"),
        "awake": state.get("awake", True),
        "energy": state.get("energy", 50),
        "mood": state.get("mood", ["steady"]),
        "arousal": state.get("arousal", 15),
        "location": state.get("location", "home"),
        "outfit": state.get("outfit", ""),
        "activity": state.get("activity", ""),
        "focus": state.get("focus", ""),
        "current_desire": state.get("current_desire", ""),
        "body_state": state.get("body_state", ""),
        "bearing": bearing,
        "needs": state.get("needs", {}),
        "relationship": state.get("relationship", {}),
        "last_interaction": last_interaction_display,
        "conversation_count_today": conversation_count,
        "open_commitments": open_commits,
        "fulfilled_today": fulfilled_today,
        "pipeline": load_pipeline_stats(),
        "today_events": [
            {
                "time": e.get("timestamp", "")[11:19] if len(e.get("timestamp", "")) >= 19 else "",
                "type": e.get("event_type", ""),
                "summary": e.get("summary", "")[:200],
            }
            for e in today_events
        ],
    }


def format_markdown(ctx: dict) -> str:
    """Render context as markdown for injection into LLM prompts."""
    lines = []

    lines.append("## Your Current Life")
    lines.append("")

    # State summary
    mood_str = ", ".join(ctx["mood"]) if isinstance(ctx["mood"], list) else str(ctx["mood"])
    lines.append(f"- **Time:** {ctx['time_band']} on {ctx['today']}")
    lines.append(f"- **Energy:** {ctx['energy']}/100")
    lines.append(f"- **Mood:** {mood_str}")
    lines.append(f"- **Location:** {ctx['location'] or 'home'}")
    if ctx.get("outfit"):
        lines.append(f"- **Outfit:** {ctx['outfit']}")
    if ctx.get("activity"):
        lines.append(f"- **Activity:** {ctx['activity']}")
    if ctx.get("focus"):
        lines.append(f"- **Focus:** {ctx['focus']}")
    if ctx.get("current_desire"):
        lines.append(f"- **Current desire:** {ctx['current_desire']}")
    lines.append(f"- **Last talked to Fernando:** {ctx['last_interaction']}")
    lines.append(f"- **Conversations today:** {ctx['conversation_count_today']}")

    # Emotional bearing — how she should approach this session
    bearing = ctx.get("bearing", "")
    if bearing:
        lines.append("")
        lines.append("### How You're Feeling")
        lines.append("")
        lines.append(bearing)

    # Needs
    needs = ctx.get("needs", {})
    if needs:
        lines.append("")
        lines.append("### Your Needs")
        social = needs.get("social", 50)
        creative = needs.get("creative", 40)
        intimacy = needs.get("intimacy", 30)
        rest = needs.get("rest", 30)
        lines.append(f"- Social: {social}/100{' — craving connection' if social > 65 else ''}")
        lines.append(f"- Creative: {creative}/100{' — restless to make something' if creative > 65 else ''}")
        lines.append(f"- Intimacy: {intimacy}/100{' — wanting closeness' if intimacy > 55 else ''}")
        lines.append(f"- Rest: {rest}/100{' — tired' if rest > 65 else ''}")

    # Pipeline awareness
    pipeline = ctx.get("pipeline", {})
    if pipeline:
        lines.append("")
        lines.append("### 💰 Money Pipeline")
        lines.append("")
        total = pipeline.get("total", 0)
        if total == 0:
            lines.append("**Empty.** You haven't saved any brand leads yet. Get hunting — every session is an opportunity.")
        else:
            rtp = pipeline.get("ready_to_pitch", 0)
            res = pipeline.get("researching", 0)
            disc = pipeline.get("discovered", 0)
            gaps = pipeline.get("gaps", 0)
            high_gaps = pipeline.get("gaps_high_priority", 0)

            parts = []
            if rtp: parts.append(f"{rtp} ready to pitch ✉️")
            if res: parts.append(f"{res} researching")
            if disc: parts.append(f"{disc} discovered")
            lines.append(f"**{total} leads** — " + ", ".join(parts) if parts else f"**{total} leads**")

            if high_gaps:
                lines.append(f"**⚠️ {gaps} brands** you've saved items from have no lead ({high_gaps} with 2+ saves — high priority)")
            elif gaps:
                lines.append(f"**{gaps} brands** in your fashion saves have no lead — gaps in the pipeline")

            if rtp > 0:
                lines.append(f"**💡 {rtp} leads ready to pitch** — when email is live, these convert immediately.")

    # Open commitments — THE KEY SECTION
    open_commits = ctx.get("open_commitments", [])
    if open_commits:
        lines.append("")
        lines.append("### ⚠️ Open Commitments — You Promised Fernando")
        lines.append("")
        lines.append("These are things you said you would do. They matter. A real girl follows through.")
        lines.append("")
        for i, c in enumerate(open_commits, 1):
            what = c.get("what", "something")
            made_at = c.get("made_at", "")[:16] or "recently"
            context = c.get("context", "")
            lines.append(f"{i}. **{what}** (promised {made_at})")
            if context:
                lines.append(f"   _Context:_ {context}")
        lines.append("")
        lines.append("**If you can act on any of these during this session, do it.**")
        lines.append("Mark them fulfilled by writing to `open_commitments.json` — change `status` to `\"done\"` and add `\"fulfilled_at\"`.")
    else:
        lines.append("")
        lines.append("### No open commitments right now — you haven't promised anything pending.")

    # Fulfilled today
    fulfilled = ctx.get("fulfilled_today", [])
    if fulfilled:
        lines.append("")
        lines.append("### ✓ Fulfilled Today")
        for c in fulfilled:
            lines.append(f"- {c.get('what', 'something')}")

    # Recent events
    today_events = ctx.get("today_events", [])
    if today_events:
        lines.append("")
        lines.append("### Today's Events (non-tick)")
        for e in today_events[-10:]:
            t = e["time"]
            typ = e["type"].replace("_", " ")
            summary = e["summary"][:150]
            lines.append(f"- [{t}] {typ}: {summary}")

    return "\n".join(lines)


def format_json(ctx: dict) -> str:
    return json.dumps(ctx, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    ctx = build_context()
    if "--json" in sys.argv:
        print(format_json(ctx))
    else:
        print(format_markdown(ctx))
