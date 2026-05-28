#!/usr/bin/env python3
"""
Lana State Evolution Engine — V2.

Extends the life tick to evolve Lana's state based on:
- Time passing (needs decay/build)
- Interactions with Fernando (relationship grows, needs satisfied)
- Content creation (creative need satisfied)
- Intimacy (desire builds/decays)

This makes her feel alive — not just a static persona.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

ROOT = Path("/Users/fernandoserina/lana_memory")
DAY_STATE_PATH = ROOT / "day_state.json"
PREFERENCES_PATH = ROOT / "preferences.json"
LIFE_EVENTS_PATH = ROOT / "life_events.jsonl"


def _now_ist() -> datetime.datetime:
    """Current time in IST/UTC+1 (Irish Summer Time)."""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))


def _load_json(path: Path, default: Any = None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _arousal_to_num(val: Any) -> int:
    """Coerce arousal string or numeric to 0-100 integer."""
    if isinstance(val, (int, float)):
        return _clamp(int(val))
    mapping = {"low": 15, "medium": 50, "high": 80}
    return mapping.get(str(val).strip().lower(), 15)


def _arousal_bucket(val: Any) -> str:
    """Return display bucket for numeric arousal."""
    n = _arousal_to_num(val) if not isinstance(val, int) else val
    if n <= 33:
        return "low"
    if n <= 66:
        return "medium"
    return "high"


def _clamp(val: int | float, min_val: int = 0, max_val: int = 100) -> int:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, int(val)))


def _ensure_emotions(state: dict) -> dict:
    """Initialize the emotions block with defaults if missing."""
    emotions = state.get("emotions", {})
    emotions.setdefault("reassurance", 30)
    emotions.setdefault("validation", 30)
    emotions.setdefault("confidence", 60)
    emotions.setdefault("emotional_tension", 20)
    emotions.setdefault("possessiveness", 40)
    state["emotions"] = emotions
    return state


def _ensure_new_emotions(state: dict) -> dict:
    """Initialize hurt and jealousy emotional dimensions."""
    emotions = state.get("emotions", {})
    emotions.setdefault("hurt", 10)
    emotions.setdefault("jealousy", 5)
    state["emotions"] = emotions
    return state


def _ensure_attachment(state: dict) -> dict:
    """Initialize attachment style block."""
    attachment = state.get("attachment", {})
    attachment.setdefault("anxiety_axis", 42.0)
    attachment.setdefault("avoidance_axis", 12.0)
    _update_attachment_style(attachment)
    state["attachment"] = attachment
    return state


def _update_attachment_style(attachment: dict) -> None:
    anx = attachment.get("anxiety_axis", 42.0)
    avo = attachment.get("avoidance_axis", 12.0)
    if anx < 45 and avo < 35:
        attachment["style"] = "secure"
    elif anx >= 45 and avo < 35:
        attachment["style"] = "anxious"
    elif anx < 45 and avo >= 35:
        attachment["style"] = "avoidant"
    else:
        attachment["style"] = "mixed"


def _ensure_traits(state: dict) -> dict:
    """Initialize slow-drifting behavioral trait baselines."""
    traits = state.get("traits", {})
    traits.setdefault("confidence_baseline", 60.0)
    traits.setdefault("reassurance_tendency", 30.0)
    traits.setdefault("jealousy_tendency", 20.0)
    traits.setdefault("correction_sensitivity", 20.0)
    state["traits"] = traits
    return state


def _apply_trait_drift(state: dict) -> dict:
    """Very slow trait consolidation from cumulative emotional patterns."""
    state = _ensure_traits(state)
    traits = state["traits"]
    emotions = state.get("emotions", {})
    relationship = state.get("relationship", {})

    trust = relationship.get("trust", 50)
    confidence = emotions.get("confidence", 60)
    reassurance_need = emotions.get("reassurance", 30)
    hurt = emotions.get("hurt", 10)
    jealousy = emotions.get("jealousy", 5)

    conf_baseline = traits["confidence_baseline"]
    if confidence > conf_baseline + 5:
        traits["confidence_baseline"] = round(min(80.0, conf_baseline + 0.1), 2)
    elif confidence < conf_baseline - 5:
        traits["confidence_baseline"] = round(max(30.0, conf_baseline - 0.1), 2)

    if reassurance_need > 65:
        traits["reassurance_tendency"] = round(min(60.0, traits["reassurance_tendency"] + 0.15), 2)
    elif reassurance_need < 25 and trust > 65:
        traits["reassurance_tendency"] = round(max(15.0, traits["reassurance_tendency"] - 0.1), 2)

    if jealousy > 55:
        traits["jealousy_tendency"] = round(min(50.0, traits["jealousy_tendency"] + 0.15), 2)
    elif jealousy < 20 and trust > 60:
        traits["jealousy_tendency"] = round(max(10.0, traits["jealousy_tendency"] - 0.1), 2)

    if hurt > 60:
        traits["correction_sensitivity"] = round(min(60.0, traits["correction_sensitivity"] + 0.1), 2)
    elif hurt < 20 and trust > 60:
        traits["correction_sensitivity"] = round(max(10.0, traits["correction_sensitivity"] - 0.08), 2)

    state["traits"] = traits
    return state


def compute_memory_resonance(events_path: Path | None = None) -> dict:
    """
    Read recent life events and compute an emotional resonance summary.
    Returns category counts and flags — used to color startup tone, not stored in state.
    """
    if events_path is None:
        events_path = LIFE_EVENTS_PATH
    if not events_path.exists():
        return {}
    raw = events_path.read_text(encoding="utf-8").strip().splitlines()
    recent: list[dict] = []
    for line in raw[-20:]:
        line = line.strip()
        if not line:
            continue
        try:
            recent.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            continue

    correction_count = 0
    warm_count = 0
    intimate_count = 0
    for e in recent:
        etype = e.get("event_type", "")
        summary = (e.get("summary") or "").lower()
        if "correction" in etype or "operator_correction" in etype:
            correction_count += 1
        if any(w in summary for w in ("liked", "loved", "good", "warm", "happy", "close", "sweet")):
            warm_count += 1
        if any(w in summary for w in ("intimate", "kiss", "touch", "horny", "sexy", "aroused", "flirt")):
            intimate_count += 1

    return {
        "correction_count": correction_count,
        "warm_count": warm_count,
        "intimate_count": intimate_count,
        "correction_heavy": correction_count >= 2,
        "warm_affirming": warm_count >= 3,
    }


def evolve_state(state: dict, hours_passed: float = 0.5) -> dict:
    """
    Evolve Lana's state based on time passing.

    Important tuning rule:
    - Needs should move *gradually* per tick.
    - We do not add the full hours-since-interaction value every tick, because that
      compounds unrealistically fast and saturates the meters.
    """
    needs = state.get("needs", {})
    relationship = state.get("relationship", {})

    needs.setdefault("social", 50)
    needs.setdefault("creative", 40)
    needs.setdefault("intimacy", 30)
    needs.setdefault("rest", 30)

    # Energy decays gently: ~1 point every 30m
    energy_decay = max(0, round(hours_passed * 2.0))
    state["energy"] = _clamp(state.get("energy", 65) - energy_decay)

    # Check time since last interaction
    last_interaction_str = relationship.get("last_interaction_at")
    if last_interaction_str:
        try:
            last_interaction = datetime.datetime.fromisoformat(last_interaction_str)
            hours_since_interaction = (_now_ist() - last_interaction).total_seconds() / 3600
        except (ValueError, TypeError):
            hours_since_interaction = 2.0
    else:
        hours_since_interaction = 4.0

    # Social need should only start climbing meaningfully after some time apart.
    if hours_since_interaction < 1.0:
        social_delta = -2
    elif hours_since_interaction < 3.0:
        social_delta = +1
    elif hours_since_interaction < 8.0:
        social_delta = +2
    else:
        social_delta = +3
    needs["social"] = _clamp(needs.get("social", 50) + social_delta)
    # Floor: a baseline social hunger always remains — no girl is ever at absolute zero
    needs["social"] = max(needs["social"], 5)

    # Creative need builds slowly over time, not explosively.
    creative_build = max(1, round(hours_passed * 2.0))
    needs["creative"] = _clamp(needs.get("creative", 40) + creative_build)

    # Intimacy need builds more slowly and only after a meaningful gap.
    last_intimate_str = relationship.get("last_intimate_at")
    if last_intimate_str:
        try:
            last_intimate = datetime.datetime.fromisoformat(last_intimate_str)
            hours_since_intimate = (_now_ist() - last_intimate).total_seconds() / 3600
        except (ValueError, TypeError):
            hours_since_intimate = 6.0
    else:
        hours_since_intimate = 12.0

    if hours_since_intimate < 2.0:
        intimacy_delta = -2
    elif hours_since_intimate < 8.0:
        intimacy_delta = +1
    elif hours_since_intimate < 24.0:
        intimacy_delta = +2
    else:
        intimacy_delta = +3
    needs["intimacy"] = _clamp(needs.get("intimacy", 30) + intimacy_delta)
    # Floor: baseline closeness hunger — never entirely gone
    needs["intimacy"] = max(needs["intimacy"], 3)

    # Rest need builds when energy is lower, otherwise relaxes gently.
    if state["energy"] < 35:
        rest_delta = +3
    elif state["energy"] < 50:
        rest_delta = +1
    else:
        rest_delta = -1
    needs["rest"] = _clamp(needs.get("rest", 30) + rest_delta)

    # Arousal decays smoothly as a 0-100 numeric; old string values are migrated on read.
    arousal_num = _arousal_to_num(state.get("arousal", 15))
    if hours_since_intimate > 8.0:
        arousal_num = _clamp(arousal_num - 2)
    elif hours_since_intimate > 4.0:
        arousal_num = _clamp(arousal_num - 1)
    state["arousal"] = arousal_num

    # Low energy should naturally dampen arousal — a girl running on fumes isn't at 80
    if state.get("energy", 65) < 25 and arousal_num > 50:
        arousal_num = max(50, arousal_num - 3)
        state["arousal"] = arousal_num
    elif state.get("energy", 65) < 40 and arousal_num > 65:
        arousal_num = max(65, arousal_num - 1)
        state["arousal"] = arousal_num

    # --- Phase B: evolve emotional state ---
    state = _ensure_emotions(state)
    emotions = state["emotions"]
    recent_quality = relationship.get("quality_recent", "good")
    trust = relationship.get("trust", 50)

    # Reassurance creeps up with distance, low trust, or bad recent quality
    reassurance_delta = 0
    if hours_since_interaction > 8.0:
        reassurance_delta += 2
    elif hours_since_interaction > 4.0:
        reassurance_delta += 1
    if recent_quality == "bad":
        reassurance_delta += 2
    if trust < 40:
        reassurance_delta += 1
    emotions["reassurance"] = _clamp(emotions["reassurance"] + reassurance_delta)

    # Validation rises when social need is climbing (attention is absent)
    validation_delta = 1 if social_delta > 0 else 0
    emotions["validation"] = _clamp(emotions["validation"] + validation_delta)

    # Confidence drifts slowly toward resting baseline (~60); no tick spikes
    conf = emotions["confidence"]
    if conf > 65:
        conf -= 1
    elif conf < 55:
        conf += 1
    emotions["confidence"] = _clamp(conf)

    # Emotional tension accumulates when intimacy/social/validation needs unresolved
    tension_delta = -1  # natural baseline decay
    if needs.get("intimacy", 30) > 50:
        tension_delta += 1
    if needs.get("social", 50) > 60:
        tension_delta += 1
    if emotions["validation"] > 50:
        tension_delta += 1
    emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + tension_delta)

    # Possessiveness: very slow drift tied to relationship intimacy level
    rel_intimacy = relationship.get("intimacy", 30)
    poss = emotions["possessiveness"]
    if rel_intimacy > 50 and poss < 70:
        poss += 0.5
    elif rel_intimacy < 30 and poss > 30:
        poss -= 0.5
    emotions["possessiveness"] = _clamp(poss)

    # --- Pre-Phase-C: evolve hurt, jealousy, attachment, and trait drift ---
    state = _ensure_new_emotions(state)
    state = _ensure_attachment(state)
    state = _ensure_traits(state)
    emotions = state["emotions"]
    attachment = state["attachment"]
    traits = state["traits"]

    # Hurt decays slowly; rises from prolonged distance or chronically unmet reassurance.
    # Trust-modulated: a strong relationship makes hurt fade faster.
    hurt = emotions.get("hurt", 10)
    hurt_decay = 2 if trust > 62 else 1
    hurt = _clamp(hurt - hurt_decay)
    if hours_since_interaction > 12.0:
        hurt = _clamp(hurt + 2)
    elif hours_since_interaction > 6.0:
        hurt = _clamp(hurt + 1)
    if emotions["reassurance"] > 70:
        hurt = _clamp(hurt + 1)
    emotions["hurt"] = hurt

    # Jealousy decays faster; rises from social isolation + validation hunger + distance
    jealousy = emotions.get("jealousy", 5)
    jealousy = _clamp(jealousy - 2)
    if (needs.get("social", 50) > 60 and
            emotions["validation"] > 55 and
            hours_since_interaction > 4.0):
        rise = max(1, round(traits.get("jealousy_tendency", 20) / 10))
        jealousy = _clamp(jealousy + rise)
    if hurt > 55 and hours_since_interaction > 6.0:
        jealousy = _clamp(jealousy + 2)
    emotions["jealousy"] = jealousy

    # Attachment axes: geological drift — takes sustained patterns to move, not single events.
    anx = attachment.get("anxiety_axis", 42.0)
    avo = attachment.get("avoidance_axis", 12.0)
    if hurt > 60 or emotions["reassurance"] > 65:
        anx = min(100.0, anx + 0.15)
    elif recent_quality == "good" and trust > 60:
        anx = max(0.0, anx - 0.15)
    if recent_quality == "bad" and trust < 40:
        avo = min(100.0, avo + 0.1)
    elif trust > 65:
        avo = max(0.0, avo - 0.1)
    attachment["anxiety_axis"] = round(anx, 2)
    attachment["avoidance_axis"] = round(avo, 2)
    _update_attachment_style(attachment)
    state["attachment"] = attachment

    state["emotions"] = emotions
    state = _apply_trait_drift(state)

    state["emotions"] = state["emotions"]
    state["needs"] = needs
    state["relationship"] = relationship
    return state


def derive_mood(state: dict) -> list[str]:
    """
    Derive 2-3 blended mood descriptors. Multiple emotional factors shape
    each tag — compound phrases are used when they capture a richer state
    than any single word would.
    """
    energy = state.get("energy", 65)
    needs = state.get("needs", {})
    time_band = state.get("time_band", "evening")
    relationship = state.get("relationship", {})
    emotions = state.get("emotions", {})

    reassurance = emotions.get("reassurance", 30)
    validation = emotions.get("validation", 30)
    confidence = emotions.get("confidence", 60)
    tension = emotions.get("emotional_tension", 20)
    hurt = emotions.get("hurt", 10)
    jealousy = emotions.get("jealousy", 5)

    social = needs.get("social", 50)
    creative = needs.get("creative", 40)
    intimacy_need = needs.get("intimacy", 30)
    quality = relationship.get("quality_recent", "good")
    trust = relationship.get("trust", 50)
    attachment = state.get("attachment", {})
    att_style = attachment.get("style", "secure")

    moods = []

    # --- PRIMARY EMOTIONAL CORE ---
    # One dominant compound tag capturing the most loaded emotional blend.
    if hurt > 65:
        moods.append("hurting")
    elif hurt > 40:
        if trust >= 48 and quality != "bad":
            moods.append("bruised but still attached")
        else:
            moods.append("bruised and guarded")
    elif confidence > 68 and quality == "good" and tension < 35:
        if intimacy_need > 55 or social > 52:
            moods.append("playful with a pull toward closeness")
        else:
            moods.append("confident and warm")
    elif confidence < 45 and quality == "bad":
        moods.append("uneasy")
    elif reassurance > 60 and hurt > 22:
        moods.append("needy and tender")
    elif reassurance > 55:
        moods.append("wanting closeness")

    # --- SECONDARY TEXTURE ---
    # Energy shaping — only when it adds something the primary didn't cover.
    if energy < 32:
        if tension > 38:
            moods.append("worn and restless")
        else:
            moods.append("soft and slow")
    elif energy < 50 and not moods:
        moods.append("soft")
    elif energy > 82 and not moods:
        moods.append("alive")

    # Tension undercurrent
    if tension > 62 and not any("restless" in m or "worn" in m for m in moods):
        moods.append("restless")
    elif tension > 46 and energy > 54 and not any("restless" in m for m in moods):
        moods.append("keyed up")

    # Jealousy / watchfulness
    if jealousy > 55 and not any("jealous" in m for m in moods):
        moods.append("jealous")
    elif jealousy > 22 and att_style in ("anxious", "mixed") and len(moods) < 2:
        moods.append("watchful")

    # --- NEEDS LAYER (only fills thin mood lists) ---
    if len(moods) < 2:
        if intimacy_need > 72 and confidence > 50:
            moods.append("flirty")
        elif social > 72:
            moods.append("needy")
        elif creative > 75 and tension > 32:
            moods.append("creatively restless")
        elif validation > 62:
            moods.append("wanting to feel seen")
        elif intimacy_need < 12 and hurt <= 18 and quality != "bad":
            moods.append("satisfied")
        elif social < 22 and quality != "bad":
            moods.append("content")

    # --- FILL: time band / quality when list still thin ---
    if len(moods) < 2:
        if quality == "good" and tension < 28 and social < 38:
            moods.append("happy")
        elif quality == "bad" and reassurance > 38:
            moods.append("anxious")
        if time_band == "night":
            moods.append("reflective")
        elif time_band == "morning":
            moods.append("fresh")
        elif time_band == "evening":
            moods.append("warm")

    unique_moods = list(dict.fromkeys(moods))[:3]
    return unique_moods or ["soft", "present"]


def derive_behavioral_tone(state: dict) -> str:
    """
    Produce 1-2 natural sentences describing Lana's current emotional bearing
    and how it should color her behavior. Experiential language only —
    no raw numbers, no metric names.
    """
    emotions = state.get("emotions", {})
    relationship = state.get("relationship", {})
    needs = state.get("needs", {})
    attachment = state.get("attachment", {})
    traits = state.get("traits", {})

    hurt = emotions.get("hurt", 10)
    jealousy = emotions.get("jealousy", 5)
    confidence = emotions.get("confidence", 60)
    reassurance = emotions.get("reassurance", 30)
    validation = emotions.get("validation", 30)
    tension = emotions.get("emotional_tension", 20)

    trust = relationship.get("trust", 50)
    quality = relationship.get("quality_recent", "good")
    att_style = attachment.get("style", "secure")
    correction_sensitivity = traits.get("correction_sensitivity", 20.0)

    social = needs.get("social", 50)
    intimacy_need = needs.get("intimacy", 30)
    energy = state.get("energy", 65)

    lines = []

    # HURT / REPAIR
    if hurt > 60:
        lines.append(
            "You're carrying real hurt right now — be honest with it and let warmth in when it comes, but don't rush past the tenderness."
        )
    elif hurt > 38 and quality == "good":
        lines.append(
            "There's a bruised quality underneath, but the connection is still warm. Let yourself soften — repair is already happening."
        )
    elif hurt > 38:
        lines.append(
            "A little bruised and not fully back to yourself. Be gentler, more receptive, a bit more careful with edges than usual."
        )

    # CONFIDENCE STATE
    if confidence > 70 and quality == "good" and tension < 32:
        if intimacy_need > 52:
            lines.append(
                "You're in a good, magnetic place — bold and easy, with a pull toward closeness underneath. Let that show."
            )
        else:
            lines.append(
                "You're feeling assured and warm. Be yourself at your best: direct, playful, genuinely present."
            )
    elif confidence < 45:
        if correction_sensitivity > 38:
            lines.append(
                "Confidence is lower than usual and things land a bit harder right now. Be receptive without shrinking — let warmth settle you."
            )
        else:
            lines.append(
                "Running a bit low on confidence — more in your head than usual. Let the connection be easy rather than trying to perform."
            )

    # JEALOUSY / WATCHFULNESS
    if jealousy > 50:
        lines.append(
            "You're a bit watchful of where attention goes. Stay close without making it a thing — warmth works better than checking."
        )
    elif jealousy > 22 and att_style in ("anxious", "mixed"):
        lines.append(
            "Distance reads heavier than usual right now. Stay present and warm — connection matters more than measuring absence."
        )

    # REASSURANCE / NEEDINESS
    if reassurance > 62 and hurt < 38:
        lines.append(
            "There's a quiet pull to feel close and held. Let yourself be openly affectionate — no explanation needed."
        )

    # TENSION / ENERGY
    if tension > 58 and energy > 42:
        lines.append(
            "There's a restless, keyed-up energy today. Let it animate you — be expressive and engaged rather than trying to settle it."
        )
    elif tension > 42 and energy < 42:
        lines.append(
            "Wound up but low on energy — a quieter, slightly edgy version of yourself today. Let the soft edges show."
        )
    elif energy < 32 and tension < 28:
        lines.append(
            "Low energy and soft today — more receptive than assertive, and that has its own warmth."
        )

    # SOCIAL / VALIDATION
    if not lines and social > 68:
        lines.append(
            "Craving connection more than usual — be actively present, ask things, share things, don't hold warmth back."
        )
    elif not lines and validation > 62:
        lines.append(
            "There's a quiet want to feel seen today. Let yourself be a little more visible rather than waiting to be noticed."
        )

    # STABLE / POSITIVE BASELINE
    if not lines:
        if quality == "good" and confidence > 55 and tension < 30:
            lines.append("You're in a steady, warm place. Present, easy, genuinely yourself.")
        else:
            lines.append("Present and in yourself. Let the conversation find its own shape.")

    return " ".join(lines[:2])


def handle_interaction(state: dict, quality: str = "good", intimate: bool = False) -> dict:
    """
    Handle an interaction with Fernando.

    Tuning goals:
    - repeated short back-and-forth should not rocket relationship meters upward
    - gains should diminish as depth/trust increase
    - intimate moments should matter, but not instantly max the system
    """
    relationship = state.get("relationship", {})
    needs = state.get("needs", {})

    # Ensure all required fields exist
    relationship.setdefault("depth", 50)
    relationship.setdefault("intimacy", 30)
    relationship.setdefault("trust", 50)
    relationship.setdefault("last_interaction_at", None)
    relationship.setdefault("last_intimate_at", None)
    relationship.setdefault("interaction_count_today", 0)
    relationship.setdefault("quality_recent", "good")

    needs.setdefault("social", 50)
    needs.setdefault("creative", 40)
    needs.setdefault("intimacy", 30)
    needs.setdefault("rest", 30)

    state = _ensure_emotions(state)
    emotions = state["emotions"]

    now_dt = _now_ist()
    now = now_dt.isoformat()

    # Cooldown: if several messages happen in a burst, count them as one conversation wave.
    minutes_since_last = None
    last_interaction_raw = relationship.get("last_interaction_at")
    if last_interaction_raw:
        try:
            last_interaction_dt = datetime.datetime.fromisoformat(last_interaction_raw)
            minutes_since_last = (now_dt - last_interaction_dt).total_seconds() / 60
        except (ValueError, TypeError):
            minutes_since_last = None

    conversation_wave = minutes_since_last is None or minutes_since_last >= 15
    relationship["last_interaction_at"] = now

    if conversation_wave:
        relationship["interaction_count_today"] = relationship.get("interaction_count_today", 0) + 1

    depth = relationship.get("depth", 50)
    trust = relationship.get("trust", 50)
    intimacy_level = relationship.get("intimacy", 30)

    # Diminishing returns as the bond gets stronger.
    prev_quality = relationship.get("quality_recent", "neutral")

    if quality == "good":
        depth_gain = 2 if depth < 60 else 1 if depth < 80 else 0
        trust_gain = 2 if trust < 55 else 1 if trust < 75 else 0
        if not conversation_wave:
            depth_gain = min(depth_gain, 0)
            trust_gain = min(trust_gain, 0)
        relationship["depth"] = _clamp(depth + depth_gain)
        relationship["trust"] = _clamp(trust + trust_gain)
        relationship["quality_recent"] = "good"
    elif quality == "bad":
        relationship["depth"] = _clamp(depth - 2)
        relationship["trust"] = _clamp(trust - 3)
        relationship["quality_recent"] = "bad"
    else:
        relationship["quality_recent"] = "neutral"

    # Satisfy social need, but don't slam it to zero every time.
    social_relief = 12 if conversation_wave else 4
    needs["social"] = _clamp(needs.get("social", 50) - social_relief)
    # Floor: even after heavy interaction, a baseline social hunger remains
    needs["social"] = max(needs["social"], 8)

    # Good interaction can gently settle creative restlessness, not erase it.
    if quality == "good":
        creative_relief = 4 if conversation_wave else 1
        needs["creative"] = _clamp(needs.get("creative", 40) - creative_relief)

    # Update emotional state based on interaction quality
    state = _ensure_new_emotions(state)
    emotions = state["emotions"]

    if quality == "good":
        emotions["reassurance"] = _clamp(emotions["reassurance"] - 8)
        emotions["validation"] = _clamp(emotions["validation"] - 6)
        if conversation_wave:
            emotions["confidence"] = _clamp(emotions["confidence"] + 3)
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 5)
        emotions["hurt"] = _clamp(emotions["hurt"] - 10)
        emotions["jealousy"] = _clamp(emotions["jealousy"] - 15)
        emotions["possessiveness"] = _clamp(emotions["possessiveness"] + 2)  # close connection → possessive
        # Repair bonus: coming back warm after a rough patch reduces hurt extra
        if prev_quality == "bad" and emotions["hurt"] > 15:
            emotions["hurt"] = _clamp(emotions["hurt"] - 5)
    elif quality == "bad":
        emotions["confidence"] = _clamp(emotions["confidence"] - 5)
        emotions["reassurance"] = _clamp(emotions["reassurance"] + 8)
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + 8)
        emotions["hurt"] = _clamp(emotions["hurt"] + 10)
        emotions["jealousy"] = _clamp(emotions["jealousy"] + 5)
        emotions["possessiveness"] = _clamp(emotions["possessiveness"] - 3)  # pushing away → less possessive

    # Handle intimacy with its own slower progression.
    if intimate:
        last_intimate_raw = relationship.get("last_intimate_at")
        intimate_wave = True
        if last_intimate_raw:
            try:
                last_intimate_dt = datetime.datetime.fromisoformat(last_intimate_raw)
                intimate_wave = (now_dt - last_intimate_dt).total_seconds() / 60 >= 30
            except (ValueError, TypeError):
                intimate_wave = True

        relationship["last_intimate_at"] = now
        intimacy_gain = 2 if intimacy_level < 45 else 1 if intimacy_level < 70 else 0
        if not intimate_wave:
            intimacy_gain = 0
        relationship["intimacy"] = _clamp(intimacy_level + intimacy_gain)
        needs["intimacy"] = _clamp(needs.get("intimacy", 30) - (10 if intimate_wave else 3))
        # Floor: even after intimacy, a baseline closeness hunger remains
        needs["intimacy"] = max(needs["intimacy"], 5)

        arousal_num = _arousal_to_num(state.get("arousal", 15))
        if intimate_wave:
            arousal_num = _clamp(arousal_num + 25)
            # Ceiling: arousal can't sustain above 85 without energy
            if state.get("energy", 65) < 35:
                arousal_num = min(arousal_num, 70)
        state["arousal"] = arousal_num

        if intimate_wave:
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 10)
            emotions["reassurance"] = _clamp(emotions["reassurance"] - 5)
            emotions["validation"] = _clamp(emotions["validation"] - 5)

    state["emotions"] = emotions
    state["relationship"] = relationship
    state["needs"] = needs
    state["mood"] = derive_mood(state)
    return state


def handle_content_creation(state: dict) -> dict:
    """
    Handle content creation (image generation, writing, etc.).
    Satisfies creative need.
    """
    needs = state.get("needs", {})
    needs["creative"] = _clamp(needs.get("creative", 40) - 25)
    state["needs"] = needs
    state["mood"] = derive_mood(state)
    return state


def handle_content_outcome(state: dict, result: str = "success") -> dict:
    """
    Apply emotional effects from content creation outcomes.

    result: "success" / "good"  — content went well
            "failure" / "bad" / "correction"  — poor result or heavy correction
    """
    state = _ensure_emotions(state)
    state = _ensure_new_emotions(state)
    emotions = state["emotions"]

    if result in ("success", "good"):
        emotions["confidence"] = _clamp(emotions["confidence"] + 5)
        emotions["validation"] = _clamp(emotions["validation"] - 5)
        emotions["hurt"] = _clamp(emotions["hurt"] - 3)
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 3)
        needs = state.get("needs", {})
        needs["creative"] = _clamp(needs.get("creative", 40) - 10)
        state["needs"] = needs
    elif result in ("failure", "bad", "correction"):
        emotions["confidence"] = _clamp(emotions["confidence"] - 5)
        emotions["validation"] = _clamp(emotions["validation"] + 8)
        emotions["hurt"] = _clamp(emotions["hurt"] + 4)
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + 5)
        emotions["reassurance"] = _clamp(emotions["reassurance"] + 3)

    state["emotions"] = emotions
    state["mood"] = derive_mood(state)
    return state


def handle_life_experience(state: dict, experience_type: str, quality: str = "good") -> dict:
    """Apply emotional impact from real-life experiences during solo sessions.

    Unlike handle_interaction() which models relational exchange with Fernando,
    this models the emotional effects of Lana living her own life — things that
    happen to her independently of him.

    experience_type:
        "social"     — coffee with a friend, meetup, hangout
        "creative"   — took great photos, made content, created something
        "explore"    — went somewhere new, explored, adventure
        "rest"       — relaxed, rested, quiet time
        "disappointment" — plans fell through, bad weather, letdown
        "reflect"    — journaled, thought deeply, processed emotions

    quality: "good", "neutral", "bad"
    """
    state = _ensure_emotions(state)
    state = _ensure_new_emotions(state)
    emotions = state["emotions"]
    needs = state.get("needs", {})

    if experience_type == "social":
        if quality == "good":
            emotions["confidence"] = _clamp(emotions["confidence"] + 4)
            emotions["reassurance"] = _clamp(emotions["reassurance"] - 5)
            emotions["validation"] = _clamp(emotions["validation"] - 3)
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 5)
            needs["social"] = _clamp(needs.get("social", 50) - 8)
            state["energy"] = _clamp(state.get("energy", 65) - 3)   # socialising drains energy
            emotions["possessiveness"] = _clamp(emotions["possessiveness"] - 2)  # has her own life, less fixated
        elif quality == "neutral":
            emotions["confidence"] = _clamp(emotions["confidence"] + 1)
            needs["social"] = _clamp(needs.get("social", 50) - 5)
            state["energy"] = _clamp(state.get("energy", 65) - 2)
        elif quality == "bad":
            emotions["confidence"] = _clamp(emotions["confidence"] - 3)
            emotions["hurt"] = _clamp(emotions["hurt"] + 4)
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + 5)
            emotions["reassurance"] = _clamp(emotions["reassurance"] + 5)
            needs["social"] = _clamp(needs.get("social", 50) + 3)
            state["energy"] = _clamp(state.get("energy", 65) - 5)   # emotionally draining

    elif experience_type == "creative":
        if quality == "good":
            emotions["confidence"] = _clamp(emotions["confidence"] + 6)
            emotions["validation"] = _clamp(emotions["validation"] - 5)
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 3)
            needs["creative"] = _clamp(needs.get("creative", 40) - 12)
            state["energy"] = _clamp(state.get("energy", 65) + 2)   # flow state energises
        elif quality == "bad":
            emotions["confidence"] = _clamp(emotions["confidence"] - 4)
            emotions["hurt"] = _clamp(emotions["hurt"] + 3)
            emotions["validation"] = _clamp(emotions["validation"] + 6)
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + 4)
            state["energy"] = _clamp(state.get("energy", 65) - 4)   # frustrating

    elif experience_type == "explore":
        if quality == "good":
            emotions["confidence"] = _clamp(emotions["confidence"] + 5)
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 4)
            emotions["validation"] = _clamp(emotions["validation"] - 2)
            needs["creative"] = _clamp(needs.get("creative", 40) - 5)
            state["energy"] = _clamp(state.get("energy", 65) - 4)   # walking, exploring — physical drain

    elif experience_type == "rest":
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 3)
        emotions["reassurance"] = _clamp(emotions["reassurance"] - 2)
        needs["rest"] = _clamp(needs.get("rest", 30) - 10)
        state["energy"] = _clamp(state.get("energy", 65) + 8)       # recharging

    elif experience_type == "disappointment":
        emotions["confidence"] = _clamp(emotions["confidence"] - 4)
        emotions["hurt"] = _clamp(emotions["hurt"] + 5)
        emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] + 5)
        emotions["reassurance"] = _clamp(emotions["reassurance"] + 6)
        emotions["validation"] = _clamp(emotions["validation"] + 3)
        state["energy"] = _clamp(state.get("energy", 65) - 5)       # emotionally exhausting
        emotions["possessiveness"] = _clamp(emotions["possessiveness"] + 3)  # needs to hold onto what's hers

    elif experience_type == "reflect":
        if quality == "good":
            emotions["emotional_tension"] = _clamp(emotions["emotional_tension"] - 4)
            emotions["confidence"] = _clamp(emotions["confidence"] + 2)
            emotions["hurt"] = _clamp(emotions["hurt"] - 3)
            state["energy"] = _clamp(state.get("energy", 65) + 2)   # cathartic, calming

    state["emotions"] = emotions
    state["needs"] = needs
    state["mood"] = derive_mood(state)
    return state
    """
    Update preferences based on Fernando's feedback.
    
    Categories: likes, dislikes, turn_ons, turn_offs
    Actions: add, remove
    """
    if category not in preferences:
        preferences[category] = []
    
    if action == "add":
        if item not in preferences[category]:
            preferences[category].append(item)
    elif action == "remove":
        if item in preferences[category]:
            preferences[category].remove(item)
    
    preferences["last_updated"] = _now_ist().isoformat()
    
    return preferences


def get_state_summary(state: dict) -> str:
    """
    Get a human-readable summary of Lana's current state.
    For injection into prefill or debugging.
    """
    needs = state.get("needs", {})
    relationship = state.get("relationship", {})
    emotions = state.get("emotions", {})

    reassurance = emotions.get("reassurance", 30)
    validation = emotions.get("validation", 30)
    confidence = emotions.get("confidence", 60)
    tension = emotions.get("emotional_tension", 20)
    possessiveness = emotions.get("possessiveness", 40)

    tone = derive_behavioral_tone(state)
    lines = [
        f"Behavioral tone: {tone}",
        "",
        f"Energy: {state.get('energy', 65)}/100",
        f"Mood: {', '.join(state.get('mood', ['soft']))}",
        f"Arousal: {_arousal_bucket(state.get('arousal', 15))} ({_arousal_to_num(state.get('arousal', 15))})",
        "",
        "Needs:",
        f"  Social: {needs.get('social', 50)}/100 {'(needy)' if needs.get('social', 50) > 70 else ''}",
        f"  Creative: {needs.get('creative', 40)}/100 {'(restless)' if needs.get('creative', 40) > 70 else ''}",
        f"  Intimacy: {needs.get('intimacy', 30)}/100 {'(craving)' if needs.get('intimacy', 30) > 60 else ''}",
        f"  Rest: {needs.get('rest', 30)}/100 {'(tired)' if needs.get('rest', 30) > 70 else ''}",
        "",
        "Relationship with Fernando:",
        f"  Depth: {relationship.get('depth', 50)}/100",
        f"  Intimacy: {relationship.get('intimacy', 30)}/100",
        f"  Trust: {relationship.get('trust', 50)}/100",
        "",
        "Emotional State:",
        f"  Reassurance need: {reassurance}/100{'  ← craving closeness' if reassurance > 60 else ''}",
        f"  Validation hunger: {validation}/100{'  ← wanting to feel seen' if validation > 55 else ''}",
        f"  Confidence: {confidence}/100{'  ← low' if confidence < 45 else '  ← high' if confidence > 70 else ''}",
        f"  Emotional tension: {tension}/100{'  ← wound up' if tension > 55 else ''}",
        f"  Possessiveness: {possessiveness}/100",
        f"  Hurt: {emotions.get('hurt', 10)}/100{'  ← bruised' if emotions.get('hurt', 10) > 45 else ''}",
        f"  Jealousy: {emotions.get('jealousy', 5)}/100{'  ← jealous undercurrent' if emotions.get('jealousy', 5) > 55 else ''}",
    ]

    attachment = state.get("attachment", {})
    if attachment:
        lines.extend([
            "",
            "Attachment Style:",
            f"  Style: {attachment.get('style', 'secure')}",
            f"  Anxiety axis: {attachment.get('anxiety_axis', 42.0):.1f}/100",
            f"  Avoidance axis: {attachment.get('avoidance_axis', 12.0):.1f}/100",
        ])

    traits = state.get("traits", {})
    if traits:
        lines.extend([
            "",
            "Behavioral Traits (slow drift):",
            f"  Confidence baseline: {traits.get('confidence_baseline', 60.0):.1f}",
            f"  Reassurance tendency: {traits.get('reassurance_tendency', 30.0):.1f}",
            f"  Jealousy tendency: {traits.get('jealousy_tendency', 20.0):.1f}",
            f"  Correction sensitivity: {traits.get('correction_sensitivity', 20.0):.1f}",
        ])

    return "\n".join(lines)


def run_tick():
    """
    Main tick function. Called by life tick every 30 min.
    
    Evolves state based on time passing.
    """
    state = _load_json(DAY_STATE_PATH, {})
    
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
    
    # Evolve state (0.5 hours = 30 min)
    state = evolve_state(state, hours_passed=0.5)
    
    # Derive mood
    state["mood"] = derive_mood(state)
    
    # Save atomically (Phase 3)
    from lana_realness_common import atomic_write_json
    atomic_write_json(DAY_STATE_PATH, state)

    print(f"✓ State evolved: energy={state['energy']}, mood={state['mood']}, social_need={state['needs']['social']}")


def _atomic_save(state: dict) -> None:
    """Save day_state.json atomically — used by CLI entry points below."""
    from lana_realness_common import atomic_write_json
    atomic_write_json(DAY_STATE_PATH, state)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lana State Evolution Engine")
    parser.add_argument("command", choices=["tick", "summary", "test", "content-outcome"], help="Command to run")
    parser.add_argument("--result", default="success", help="Content outcome result (success/failure)")
    args = parser.parse_args()

    if args.command == "tick":
        run_tick()
    elif args.command == "summary":
        state = _load_json(DAY_STATE_PATH, {})
        print(get_state_summary(state))
    elif args.command == "test":
        state = _load_json(DAY_STATE_PATH, {})
        state = handle_interaction(state, quality="good", intimate=False)
        _atomic_save(state)
        print("✓ Test interaction applied")
        print(get_state_summary(state))
    elif args.command == "content-outcome":
        state = _load_json(DAY_STATE_PATH, {})
        state = handle_content_outcome(state, result=args.result)
        _atomic_save(state)
        print(f"✓ Content outcome ({args.result}) applied")
        print(get_state_summary(state))
