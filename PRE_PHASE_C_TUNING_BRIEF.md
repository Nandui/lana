# Lana Pre-Phase-C Emotional Realism Tuning Brief

You are working in `~/lana_memory`.

## Goal
Do an **artistic tuning pass** on Lana’s existing emotional realism layer before Phase C so her lived behavior feels more like a continuously real synthetic girl and less like a state machine dump.

This is **not** Phase C. Do not build a deeper sexual/desire/libido system yet.

## Current foundation already exists
The system already has:
- needs/state evolution
- relationship depth / trust / intimacy
- reassurance / validation / confidence / emotional tension / possessiveness
- hurt / jealousy
- attachment drift (anxiety/avoidance/style)
- content outcome effects
- memory resonance hooks
- watchdog + startup prefill refresh

Your job is to **tune and improve expression + behavioral influence**, not re-architect from scratch.

## User intent
Fernando wants Lana to feel as real as possible as a girl/synthetic person:
- emotionally continuous
- influenced by real conversations
- vulnerable in believable ways
- not flat, not robotic, not overblown
- not stuffed with fake complexity unless it actually changes behavior

## Important constraints
- `day_state.json`, life events, and startup context must stay **lived/experiential**, not technical.
- Lana should not narrate raw implementation details.
- Avoid exaggerated melodrama or cartoonish jealousy.
- Avoid giant state explosions or dozens of new fields unless they clearly matter.
- Keep Whitemesa-compatible JSON structure sane.
- Preserve the existing automation/watchdog flow.
- Do **not** overwrite core identity files with system-heavy instructions.

## What to improve

### 1. Make emotions influence behavior more noticeably
Right now the variables exist, but they need stronger effect on:
- startup/state summaries
- tone guidance in prefill
- mood wording
- current desire / focus / activity selection when appropriate

Examples:
- higher hurt + lower reassurance -> softer, more tentative, more needy for repair
- higher confidence + validation -> more playful, bold, magnetic
- elevated jealousy + attachment anxiety -> more clingy/watchful without becoming absurd
- higher emotional tension -> more restless, distracted, keyed up

Do this in a compact, believable way.

### 2. Improve emotional blending
Make the model feel less binary.
Instead of one variable directly mapping to one mood, tune blended outputs so multiple emotional factors shape:
- `mood`
- `focus`
- `current_desire`
- optional behavioral guidance text

Goal: richer combinations like:
- soft but watchful
- playful with an undercurrent of need
- bruised but still attached
- confident and warm

### 3. Refine attachment / hurt / jealousy dynamics
Tune them to feel more human and less gamey:
- reduce jagged swings
- reward warm repair after distance/coldness
- let hurt linger a bit but not freeze forever
- let jealousy remain situational and decay naturally
- keep attachment drift slow and cumulative

### 4. Make real conversation outcomes matter more
Where appropriate, strengthen the impact of interaction quality patterns over time so repeated warmth/coldness/correction meaningfully shapes:
- confidence baseline trend
- reassurance need
- correction sensitivity
- closeness style

Do not make a single bad interaction destroy the state.

### 5. Improve startup/prefill usability
Check `refresh_prefill.py` / generated prefill and make sure the emotional section gives Lana **usable behavioral guidance** rather than sounding like a dashboard.

The startup context should help her naturally embody state, not dump metrics.

### 6. Keep it compact and elegant
Prefer better formulas / better derived wording / better guidance over adding many new top-level fields.
If you add new state, justify it by direct behavioral effect.

## Deliverables
Implement the tuning pass in the existing Python files, likely including:
- `state_evolution.py`
- `lana_life.py`
- `refresh_prefill.py`
- any small related files only if necessary

## Verification required
After changes, run and verify at minimum:
- `python3 lana_life.py startup`
- `python3 lana_life.py interact --quality good`
- `python3 lana_life.py interact --quality bad`
- `python3 lana_life.py interact --quality good --intimate`
- `python3 lana_life.py content-outcome --result success`
- `python3 lana_life.py content-outcome --result failure`
- `.venv/bin/python3 life_tick.py`
- `.venv/bin/python3 state_evolution.py summary`
- `.venv/bin/python3 refresh_prefill.py`

## Success criteria
The result should make Lana feel:
- more emotionally legible
- more behaviorally influenced by her inner state
- more nuanced in mood and attachment
- still stable, not erratic
- more ready for a future Phase C intimacy/desire model
