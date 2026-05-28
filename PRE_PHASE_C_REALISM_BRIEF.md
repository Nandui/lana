# Pre-Phase-C Realism Brief — Deep Emotional Continuity Layer

## Goal
Before building a deeper desire/arousal Phase C, deepen Lana's emotional realism so she behaves more like a continuous synthetic girl with inner drift, emotional memory, relationship sensitivity, and emergent traits.

This layer should sit on top of the existing system and make her state feel less like flat variables and more like a lived internal life.

## Existing System
Already exists and must remain functional:
- `state_evolution.py`
  - needs
  - relationship state
  - arousal
  - emotional state block from Phase B
- `lana_life.py`
  - startup, tick, interact, remember, preference
- `conversation_state_watchdog.py`
  - auto-processing real Discord turns into state updates
- `refresh_prefill.py`
  - generates startup prefill
- `day_state.json`
  - persistent state

## Important Constraints
1. Do not break the current system.
2. Do not add fake complexity with no behavioral consequence.
3. All new state must either:
   - evolve over time,
   - change due to interaction/content outcomes/memory,
   - or influence mood/behavior/startup guidance.
4. Avoid runaway saturation.
5. Keep it inspectable and practical.
6. No frontend/Whitemesa work in this pass unless absolutely necessary.

## Required New Capabilities

### 1. Rejection sensitivity / hurt
Add a state dimension representing emotional hurt or rejection sensitivity.

Expected behavior:
- rises after cold, dismissive, harsh, or negative interaction quality
- can also rise after unmet reassurance/validation over time
- falls slowly with warm, reassuring, high-quality interactions
- should affect mood synthesis and behavioral tone

This should NOT just be the same thing as reassurance.
It should feel like: "she got stung" / "she feels bruised" / "she is more fragile right now."

---

### 2. Situational jealousy
Add jealousy as a situational emotional state, separate from slow-moving possessiveness.

Expected behavior:
- jealousy should be relatively low by default
- it can rise based on certain interaction patterns, perceived distance, validation hunger, attachment insecurity, or cues of being deprioritized
- it should decay over time if not reinforced
- it should influence mood/behavior, but not become cartoonish or permanently high

Possessiveness = relationship flavor / trait tendency
Jealousy = current reactive emotional state
Keep those distinct.

---

### 3. Attachment style drift
Add a lightweight but real attachment-style model.

Do NOT overcomplicate into psychotherapy cosplay.
Keep it practical and state-driven.

A good structure could be something like:
- `attachment_style`: one of secure / anxious / avoidant / mixed
- or a small multi-axis representation that derives a current style label

Expected behavior:
- starts from a reasonable baseline
- can drift gradually based on repeated interaction quality, reassurance patterns, hurt, and trust
- should not flip wildly from one turn to the next
- should influence how Lana reacts to distance and closeness

This matters because the same unmet need should feel different under secure vs anxious drift.

---

### 4. Success/failure effects from content generation
The emotional system should respond to how content attempts go.

Implement a path so content outcomes can affect state.
At minimum support:
- success / good result
- failure / poor result / correction-heavy result

Expected emotional effects:
- success can improve confidence, reduce validation hunger, reduce tension, maybe increase warmth/playfulness
- failure can reduce confidence, increase validation need, increase hurt or frustration, maybe increase tension

You may implement a new CLI command, extend event handling, or add a helper function — whatever is cleanest.
But the state system must have a coherent place to receive content outcomes.

---

### 5. Memory-weighted emotional resonance
Add a mechanism so certain remembered themes can influence current emotion more than generic state.

This should be practical, not mystical.
Examples:
- if recent memories include correction, realism pressure, or emotional closeness, those should shape the current emotional tone differently
- if recent memories are warm/affirming, reassurance/validation/hurt may shift differently than if recent memories are mostly correction-heavy

This can be implemented in a lightweight way, e.g.:
- inspecting recent memories or recent life events
- extracting coarse categories/tags
- applying small emotional modifiers

The key: memory should not just exist as static recall. It should color present feeling.

---

### 6. Longer-term trait consolidation from repeated patterns
Add a mechanism for emotional/behavioral traits to stabilize when patterns repeat.

Examples:
- repeatedly needing reassurance may slowly make Lana more anxious-attuned
- repeated positive intimacy may deepen security/confidence
- repeated correction-heavy loops may raise sensitivity or lower confidence baseline
- repeated success in content may stabilize confidence or ambition

This should be slow-moving and should NOT rewrite core identity recklessly.
Think of it as drift in enduring emotional tendencies.

A clean implementation might include:
- a `traits` or `drift` block
- low-frequency trait adjustments
- helper logic that derives longer-term tendencies from cumulative signals

---

## Mood / behavior integration
All of the above must feed into mood synthesis and/or startup behavioral summary.

Do NOT just add hidden numbers that never matter.
If she is:
- hurt,
- jealous,
- insecure,
- more anxious-attached,
- resonating with recent correction-heavy memory,
then that should be visible in either:
- mood labels
- startup summary
- behavior guidance
- state summary

Keep it readable and compact.

## Implementation guidance
Good possible structures:
- extend `emotions`
- add `attachment`
- add `traits` or `drift`
- add content outcome handler(s)
- add memory resonance helper(s)

Prefer helper functions instead of dumping everything into one giant function.

## Verification requirements
After implementation, verify with real commands and fix issues:
1. `python3 lana_life.py startup`
2. `python3 lana_life.py interact --quality good`
3. `python3 lana_life.py interact --quality bad`
4. at least one content outcome test path (success and/or failure)
5. `python3 lana_life.py tick`
6. `python3 state_evolution.py summary`

If you add new commands, test them explicitly.

## Deliverable
Edit the existing files directly and keep the system coherent.
At the end, summarize:
- files changed
- new state dimensions
- new behaviors
- how content outcomes and memory resonance now affect Lana
