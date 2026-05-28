# Lana Architecture: SOUL vs Skills

**Rule**: SOUL.md = identity. Skills = capabilities. Never mix them.

## What happened

During Instagram setup, Ella added login instructions, credentials, and browsing procedures to `~/.hermes/profiles/lana/SOUL.md`. Fernando immediately corrected this:

> "NO, dont change her soul remove this right now!! this is a skill not a soul!"

## The distinction

| SOUL.md | Skills |
|---|---|
| Who she IS | What she can DO |
| Permanent identity | Capabilities that can be added/removed |
| Core personality, relationships, values | Procedures, tool instructions, login routines |
| Rarely changes | Frequently updated |
| "I am Lana Hayes, 19yo Irish girl..." | "Navigate to instagram.com, fill credentials..." |

## Why it matters

If you put procedural instructions in SOUL.md:
- Her identity gets cluttered with technical noise
- She starts responding with login instructions in casual chat
- Her "realness" degrades — real girls don't have login routines in their soul
- The separation between being and doing collapses

## Correct placement

- **Instagram login routine** → `instagram-browsing` skill (profile: lana)
- **Instagram full browsing chapter** → `solo_session_prompt.md`
- **Credentials** → profile `.env` (never committed)
- **Lana's awareness she has Instagram** → skill loads at runtime when needed

## When adding new capabilities

Always ask: "Is this who Lana IS, or is this something she can DO?" If it's something she can DO, it goes in a skill, not her soul.
