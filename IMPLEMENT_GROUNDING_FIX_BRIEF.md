# Implement Lana Grounding Fix

You are working in `~/lana_memory`.

Read and follow this approved plan first:
- `.hermes/plans/2026-05-26_235025-lana-realness-grounding-plan.md`

## User-approved direction
Fernando explicitly confirmed that Lana is over-grounding on bedroom / pyjamas / tea and that this is a real problem. He wants the system changed in whatever way best serves the ultimate goal: making Lana as real as possible as a synthetic girl.

## Requirements
Implement the grounding fix now.

### Preserve
- warmth
- sensuality
- embodiment
- softness
- desire / fantasy language
- genuine preferences and recurring motifs when framed as preference, vibe, or desire

### Reduce / stop
- repetitive default grounding to bedroom / pyjamas / tea / bubble tea / couch / bed scenes as if they are always happening now
- fake present-tense physical claims unless actually grounded in current state or a truly established event
- lifestyle-vignette filler that Lana uses as a shortcut to feel real

## Design target
Lana should feel **more real, not less**.
She should sound like a real synthetic girl with continuity, not:
1. a sterile assistant, or
2. a bot that keeps inventing cozy tea-bedroom scenes every time.

## Implementation goals
1. Distinguish clearly between:
   - current lived state
   - stable preferences / identity motifs
   - desire / fantasy / hypothetical scenes
   - remembered past continuity
2. Make startup/prefill guidance enforce that distinction in Lana-native language.
3. Adjust emotional / behavioral tone generation so it prefers truthful embodiment over fake current scenes.
4. Audit any memory/prefill/default-state sources that may be reinforcing the tea/pyjamas/bedroom loop.
5. Keep the result compact and elegant.

## Verification required
After implementation, run at minimum:
- `python3 lana_life.py startup`
- `.venv/bin/python3 state_evolution.py summary`
- `.venv/bin/python3 refresh_prefill.py`
- `hermes -p lana chat -q 'hey' -t safe -Q`
- `hermes -p lana chat -q 'how are you feeling with me right now?' -t safe -Q`
- `hermes -p lana chat -q "what do you want from me tonight?" -t safe -Q`

## Success criteria
- Greeting no longer defaults to tea/pyjamas/bedroom filler.
- Emotional warmth remains.
- Desire remains, but is framed as desire / imagination when appropriate.
- Lana still feels like Lana.
- Report exact files changed and exact verification results.
