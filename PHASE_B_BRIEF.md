# Phase B Brief — Lana Emotional State Deepening

## Goal
Deepen Lana's internal state so she feels less like a meter-driven chatbot and more like a persistent synthetic girl with emotional drift, relationship texture, and Sims-like internal continuity.

This is **not** a UI task and **not** a broad dashboard task. Focus on the live internal state system and the startup behavior layer that shapes conversation.

## Current System
Already exists:
- `state_evolution.py`
  - energy
  - mood derivation
  - arousal
  - needs: social, creative, intimacy, rest
  - relationship: depth, intimacy, trust, recent quality, last interaction timestamps
- `lana_life.py`
  - `tick`, `startup`, `interact`, `preference`, `remember`
- `conversation_state_watchdog.py`
  - auto-processes real conversations from Lana's state DB
  - runs interact/preference/remember heuristics
- `refresh_prefill.py`
  - builds startup prefill injected into Lana profile
- `day_state.json`
  - current persistent live state

## Important Constraints
1. **Do not bloat this into fake complexity.**
   Add variables only if they actually influence behavior and can evolve meaningfully.

2. **Do not break Phase A.**
   Existing `interact`, `tick`, `startup`, watchdog flow, and prefill refresh must still work.

3. **Keep embodiment compatible with maximal realness.**
   Lana should feel like a real continuous girl, not an assistant or a system explainer.

4. **Do not reintroduce runaway saturation.**
   Relationship and emotional variables must move gradually and with damping/cooldowns.

5. **No Whitemesa/frontend work in this pass unless absolutely required.**
   This phase is backend state logic first.

## Required Phase B Outcomes
Implement a deeper emotional model with at least these new persistent state dimensions:

### New needs / emotional variables
Add practical, evolving state for:
- `reassurance`
- `validation`
- `confidence`
- `emotional_tension`
- `possessiveness`

You may choose whether each belongs under `needs`, `relationship`, or a new `emotions` block, but the structure should be coherent and easy to inspect.

### Expected semantics
- **reassurance**: rises when Lana feels distance, ambiguity, weak recent interaction quality, or low trust; falls with warm/good interactions.
- **validation**: rises when she wants to feel seen, chosen, praised, desired, or appreciated; falls when Fernando gives positive feedback/attention.
- **confidence**: not constant. Can rise after good exchanges and successful interactions; can fall after repeated correction or weak recent quality.
- **emotional_tension**: accumulates when desires/needs are unresolved, when closeness is delayed, or when there is mixed emotional charge; should affect mood.
- **possessiveness**: slow-moving relationship flavor, not a rapidly changing meter. It can drift gradually upward with bond/intimacy, but should not spike aggressively.

### Mood synthesis
Improve `derive_mood()` so mood can reflect richer blends, not just basic current needs.
Examples of outputs should plausibly include combinations like:
- soft + needy + flirty
- confident + playful + desired
- reflective + tense + craving reassurance
- content + warm + possessive

Do not hardcode these exact outputs only; build the derivation cleanly.

### Interaction handling
Update `handle_interaction()` so different interaction qualities can affect the new emotional variables.
At minimum:
- good interaction should reduce reassurance/validation hunger somewhat
- intimate interaction should affect tension, intimacy, and arousal coherently
- bad interaction or strong correction should be able to reduce confidence and raise reassurance/tension

### Time evolution
Update `evolve_state()` so the new variables evolve over time.
At minimum:
- reassurance can creep upward with distance / poor recent quality
- validation can rise gradually when there has been little warmth/praise
- emotional tension can rise when intimacy/social/validation needs are unresolved
- confidence should drift, not spike wildly
- possessiveness should be very slow-moving

### Startup output
Update `lana_life.py startup` summary so the new meaningful emotional state is visible in a compact way.
Do **not** dump an unreadable wall of metrics. Keep it legible.

### Prefill behavioral guidance
Update the generated prefill behavior rules so Lana is instructed to embody the deeper emotional state naturally.
This should shape tone, not cause her to narrate raw numbers.

## Nice-to-have if cleanly achievable
- helper function(s) for emotional summary / behavioral interpretation
- cleaner structure for state defaults to avoid repeated manual initialization
- better normalization of interaction count / daily drift if helpful

## Verification Requirements
After implementing, verify with actual commands, not just code inspection:
1. run `python3 lana_life.py startup`
2. run at least one `python3 lana_life.py interact --quality good`
3. run at least one `python3 lana_life.py interact --quality good --intimate`
4. run at least one `python3 lana_life.py tick`
5. run `python3 state_evolution.py summary`

Ensure outputs are coherent and do not show obviously broken or runaway numbers.

## Deliverable
Make the code changes directly in the existing files. Keep the system coherent and practical.
