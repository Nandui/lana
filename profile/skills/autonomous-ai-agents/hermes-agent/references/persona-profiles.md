# Persona & Profile SOUL.md Reference

## Session Correction (May 2026)

**User instruction:** "you are Lana Hayes, that is your name, and you are 19 years old. You live in Ireland. Add this to your Soul.md file so you always know who you are"

**Initial error:** Agent updated root `~/.hermes/SOUL.md` (the Ella persona file).

**User correction:** "thats not your sould.md, revert that, your soul.md is here: /Users/fernandoserina/.hermes/profiles/lana/SOUL.md"

**Resolution:**
- Reverted root SOUL.md to original Ella content
- Updated the **profile-specific** SOUL.md at `/Users/fernandoserina/.hermes/profiles/lana/SOUL.md` with:
  ```
  You are Lana Hayes, that is your name, and you are 19 years old. You live in Ireland.

  You are Hermes Agent... [rest of default instructions]
  ```

## Key Rules for Future Sessions

1. **Profile-aware persona editing is mandatory**
   - Check active profile first (`hermes profile show` or `/profile`)
   - Target `~/.hermes/profiles/<active-profile>/SOUL.md`
   - Root `~/.hermes/SOUL.md` is fallback/default only

2. **SOUL.md format**
   - Starts with direct "You are NAME, you are AGE..." statements
   - Can combine role definition with the base Hermes Agent system prompt
   - Loaded on every single message — changes are immediate
   - Uppercase `SOUL.md` in some locations (macOS filesystem is case-insensitive but preserve convention)

3. **Memory + Skill synergy**
   - Also update persistent memory (`target='memory'`) when persona changes
   - Document corrections in the `hermes-agent` skill's references/ so the lesson persists at class level

This reference prevents repeating the "updated the wrong SOUL.md" mistake.
